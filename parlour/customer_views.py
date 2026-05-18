from datetime import datetime, timedelta
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from Admin.models import GlobalOffer, Parlour
from .models import Appointment, Beautician, CustomerProfile, PromoCode, Service, ServicePackage
from .services import (
    check_ai_session_rate_limit,
    create_stripe_checkout_session,
    get_cached_gemini_advice,
    get_gemini_advice,
    record_ai_session_request,
)


def customer_home(request):
    services = Service.objects.all()[:8]
    packages = ServicePackage.objects.filter(is_active=True)[:4]
    promos = PromoCode.objects.filter(is_active=True)[:3]
    parlours = Parlour.objects.filter(is_active=True)[:6]
    context = {
        'services': services,
        'packages': packages,
        'promos': promos,
        'parlours': parlours,
        'total_bookings': Appointment.objects.exclude(status='cancelled').count(),
    }
    return render(request, 'customer/home.html', context)


def services_catalog(request):
    category = request.GET.get('category', '')
    qs = Service.objects.all()
    if category:
        qs = qs.filter(category__iexact=category)
    return render(request, 'customer/services.html', {
        'services': qs,
        'categories': Service.objects.values_list('category', flat=True).distinct(),
        'selected_category': category,
    })


def packages_catalog(request):
    return render(request, 'customer/packages.html', {
        'packages': ServicePackage.objects.filter(is_active=True),
    })


def book_appointment(request):
    if not request.user.is_authenticated:
        messages.info(request, 'Please login or sign up to book an appointment.')
        return redirect(f"{reverse('login')}?next=/book/")
    services = Service.objects.all()
    beauticians = Beautician.objects.filter(is_active=True)
    global_offers = GlobalOffer.objects.filter(is_active=True, expiry_date__gte=timezone.now().date())

    if request.method == 'POST':
        service = get_object_or_404(Service, pk=request.POST.get('service_id'))
        beautician_id = request.POST.get('beautician_id')
        beautician = Beautician.objects.filter(pk=beautician_id).first() if beautician_id else None

        date_str = request.POST.get('date')
        time_str = request.POST.get('time')
        if not date_str or not time_str:
            messages.error(request, 'Please select date and time.')
            return redirect('book_appointment')

        appt_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        appt_time = datetime.strptime(time_str, '%H:%M').time()

        conflict = Appointment.objects.filter(
            date=appt_date,
            time=appt_time,
            beautician=beautician,
            status__in=['pending', 'confirmed'],
        ).exists() if beautician else False

        if conflict:
            messages.error(request, 'This time slot is already booked. Please choose another.')
            return redirect('book_appointment')

        profile = getattr(request.user, 'customer_profile', None)
        appointment = Appointment.objects.create(
            customer_user=request.user,
            customer_name=request.user.get_full_name() or request.user.username,
            customer_email=request.user.email,
            customer_phone=profile.phone if profile else request.POST.get('phone', ''),
            service=service,
            beautician=beautician,
            date=appt_date,
            time=appt_time,
            status='pending',
            notes=request.POST.get('notes', ''),
            promo_code=request.POST.get('promo_code', '').strip().upper(),
        )

        today_pending = Appointment.objects.filter(
            date=appt_date,
            status__in=['pending', 'confirmed'],
        ).count()
        appointment.queue_position = today_pending
        appointment.save()

        if request.POST.get('pay_now') == 'on':
            try:
                session = create_stripe_checkout_session(
                    appointment,
                    request.build_absolute_uri('/booking/success/'),
                    request.build_absolute_uri('/booking/cancel/'),
                )
                appointment.stripe_session_id = session.id
                appointment.save(update_fields=['stripe_session_id'])
                return redirect(session.url)
            except Exception as exc:
                messages.warning(request, f'Payment gateway error: {exc}. Booking saved as pending.')
        else:
            messages.success(request, 'Appointment booked! You will receive a turn notification when ready.')

        return redirect('my_appointments')

    return render(request, 'customer/book.html', {
        'services': services,
        'beauticians': beauticians,
        'global_offers': global_offers,
        'min_date': timezone.now().date().isoformat(),
        'max_date': (timezone.now() + timedelta(days=60)).date().isoformat(),
    })


def booking_success(request):
    session_id = request.GET.get('session_id')
    if session_id:
        updated = Appointment.objects.filter(stripe_session_id=session_id)
        for appt in updated:
            appt.payment_status = 'paid'
            appt.status = 'confirmed'
            if appt.service:
                appt.amount_paid = appt.service.price
            appt.save()
        if updated.exists():
            messages.success(request, 'Payment successful! Your appointment is confirmed.')
    return redirect('my_appointments')


def booking_cancel(request):
    messages.info(request, 'Payment was cancelled. Your booking may still be pending.')
    return redirect('my_appointments')


@login_required
def my_appointments(request):
    appointments = Appointment.objects.filter(
        Q(customer_user=request.user) | Q(customer_email=request.user.email)
    ).select_related('service', 'beautician__user').order_by('-date', '-time')

    today = timezone.now().date()
    for appt in appointments.filter(date=today, status__in=['pending', 'confirmed']):
        if appt.queue_position <= 2 and not appt.turn_notified:
            messages.info(
                request,
                f'Your turn for {appt.service.name} is approaching! '
                f'Queue position: #{appt.queue_position}',
            )
            appt.turn_notified = True
            appt.save(update_fields=['turn_notified'])

    return render(request, 'customer/my_appointments.html', {'appointments': appointments})


@require_http_methods(['GET', 'POST'])
def ai_beauty_advisor(request):
    advice = None
    advice_is_error = False
    if request.method == 'POST':
        prompt = request.POST.get('prompt', '').strip()
        if prompt:
            cached = get_cached_gemini_advice(prompt)
            if cached:
                advice, advice_is_error = cached, False
            else:
                rate_limit_msg = check_ai_session_rate_limit(request.session)
                if rate_limit_msg:
                    advice, advice_is_error = rate_limit_msg, True
                else:
                    record_ai_session_request(request.session)
                    advice, advice_is_error = get_gemini_advice(prompt)
    return render(request, 'customer/ai_advisor.html', {
        'advice': advice,
        'advice_is_error': advice_is_error,
    })


def register_customer(request):
    if request.user.is_authenticated:
        return redirect('customer_home')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        phone = request.POST.get('phone', '').strip()

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken.')
        elif User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered.')
        else:
            user = User.objects.create_user(username=username, email=email, password=password)
            CustomerProfile.objects.create(user=user, phone=phone)
            login(request, user)
            messages.success(request, 'Welcome to BeautyQ!')
            return redirect('customer_home')

    return render(request, 'customer/register.html', {'role': 'customer'})


def register_owner(request):
    if request.user.is_authenticated:
        return redirect('parlour-dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        parlour_name = request.POST.get('parlour_name', '').strip()
        contact = request.POST.get('contact', '').strip()
        address = request.POST.get('address', '').strip()

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken.')
        else:
            user = User.objects.create_user(username=username, email=email, password=password)
            Parlour.objects.create(
                owner=user,
                name=parlour_name,
                contact_number=contact,
                address=address,
                is_active=False,
            )
            login(request, user)
            messages.success(request, 'Parlour registered! Awaiting admin verification.')
            return redirect('parlour-dashboard')

    return render(request, 'customer/register_owner.html')


def role_login_redirect(user):
    if user.is_superuser or user.is_staff:
        return '/myadmin/'
    if hasattr(user, 'customer_profile'):
        return '/'
    if user.parlours.exists():
        return '/dashboard'
    return '/dashboard'
