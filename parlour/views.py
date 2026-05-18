from django.shortcuts import render, redirect,  get_object_or_404
from django.contrib import messages
from django.forms import ModelForm, DateInput, TimeInput
from .models import Staff, DutyRoster
from django.views.generic import ListView
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from .models import Appointment
from .models import Service
from .models import ServicePackage
from .models import PromoCode
from datetime import datetime, timedelta
from django.urls import reverse_lazy
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum, Q
from decimal import Decimal
from .models import Beautician, Appointment, Service, DutyRoster, PayoutPeriod, Payout
from django.urls import reverse

def dashboard(request):
    today = timezone.now().date()
    completed = Appointment.objects.filter(status='completed')
    total_revenue = completed.aggregate(Sum('service__price'))['service__price__sum'] or 0
    active_bookings = Appointment.objects.filter(
        status__in=['pending', 'confirmed']
    ).count()
    context = {
        "total_revenue": total_revenue,
        "active_bookings": active_bookings,
        "total_services": Service.objects.count(),
        "staff_count": Staff.objects.count(),
        "today_count": Appointment.objects.filter(date=today).exclude(status='cancelled').count(),
        "pending_count": Appointment.objects.filter(status='pending').count(),
    }
    return render(request, "parlour/parlour-dashboard/dashboard.html", context)

class NewRequestsView( ListView):
    model = Appointment
    template_name = 'parlour/appointments/new_requests.html'
    context_object_name = 'appointments'

    def get_queryset(self):
        return Appointment.objects.filter(status='pending').order_by('date', 'time')

class TodayScheduleView( ListView):
    model = Appointment
    template_name = 'parlour/appointments/today_schedule.html'
    context_object_name = 'appointments'

    def get_queryset(self):
        today = timezone.now().date()
        return Appointment.objects.filter(date=today).exclude(status='cancelled').order_by('time')

class BookingHistoryView( ListView):
    model = Appointment
    template_name = 'parlour/appointments/booking_history.html'
    context_object_name = 'appointments'
    paginate_by = 20

    def get_queryset(self):
        return Appointment.objects.filter(status__in=['completed', 'cancelled']).order_by('-date', '-time')

# my service========================
class ServiceListView( ListView):
    model = Service
    template_name = 'parlour/catalog/service_list.html'
    context_object_name = 'services'
    ordering = ['name']

# Create a new service
class ServiceCreateView( CreateView):
    model = Service
    fields = ['name', 'category', 'duration', 'price', 'description', 'image']
    template_name = 'parlour/catalog/service_form.html'
    success_url = reverse_lazy('all_services')

# Update an existing service
class ServiceUpdateView( UpdateView):
    model = Service
    fields = ['name', 'category', 'duration', 'price', 'description', 'image']
    template_name = 'parlour/catalog/service_form.html'
    success_url = reverse_lazy('all_services')

# Delete a service
class ServiceDeleteView( DeleteView):
    model = Service
    template_name = 'parlour/catalog/service_confirm_delete.html'
    success_url = reverse_lazy('all_services')

class PackageListView( ListView):
    model = ServicePackage
    template_name = 'parlour/catalog/package_list.html'
    context_object_name = 'packages'

class PackageCreateView( CreateView):
    model = ServicePackage
    fields = ['name', 'description', 'services', 'original_price', 'package_price', 'image', 'is_active']
    template_name = 'parlour/catalog/package_form.html'
    success_url = reverse_lazy('all_packages')

class PackageUpdateView( UpdateView):
    model = ServicePackage
    fields = ['name', 'description', 'services', 'original_price', 'package_price', 'image', 'is_active']
    template_name = 'parlour/catalog/package_form.html'
    success_url = reverse_lazy('all_packages')

class PackageDeleteView( DeleteView):
    model = ServicePackage
    template_name = 'parlour/catalog/package_confirm_delete.html'
    success_url = reverse_lazy('all_packages')

class PromoListView( ListView):
    model = PromoCode
    template_name = 'parlour/catalog/promo_list.html'
    context_object_name = 'promos'

class PromoCreateView( CreateView):
    model = PromoCode
    fields = ['code', 'discount_type', 'discount_value', 'valid_from', 'valid_to', 
              'max_uses', 'min_order_amount', 'is_active']
    template_name = 'parlour/catalog/promo_form.html'
    success_url = reverse_lazy('all_promos')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['valid_from'].widget.input_type = 'datetime-local'
        form.fields['valid_to'].widget.input_type = 'datetime-local'
        return form

class PromoUpdateView( UpdateView):
    model = PromoCode
    fields = ['code', 'discount_type', 'discount_value', 'valid_from', 'valid_to', 
              'max_uses', 'min_order_amount', 'is_active']
    template_name = 'parlour/catalog/promo_form.html'
    success_url = reverse_lazy('all_promos')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['valid_from'].widget.input_type = 'datetime-local'
        form.fields['valid_to'].widget.input_type = 'datetime-local'
        return form

class PromoDeleteView( DeleteView):
    model = PromoCode
    template_name = 'parlour/catalog/promo_confirm_delete.html'
    success_url = reverse_lazy('all_promos')
# loginrequierd last use here ...............
# Inline form – no separate forms.py
class StaffForm(ModelForm):
    class Meta:
        model = Staff
        fields = ['first_name', 'last_name', 'email', 'phone', 'position', 'hire_date']
        widgets = {
            'hire_date': DateInput(attrs={'type': 'date'}),
        }

def staff_list(request):
    staff_members = Staff.objects.all()
    return render(request, 'parlour/beautician/staff_list.html', {'staff_members': staff_members})

def staff_add(request):
    if request.method == 'POST':
        form = StaffForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Staff member added successfully!')
            return redirect('staff_list')
    else:
        form = StaffForm()
    return render(request, 'parlour/beautician/staff_form.html', {'form': form, 'title': 'Add Staff'})

# ----- Inline form for Duty Roster (no forms.py) -----
class DutyRosterForm(ModelForm):
    class Meta:
        model = DutyRoster
        fields = ['staff', 'date', 'start_time', 'end_time', 'role', 'notes']
        widgets = {
            'date': DateInput(attrs={'type': 'date'}),
            'start_time': TimeInput(attrs={'type': 'time'}),
            'end_time': TimeInput(attrs={'type': 'time'}),
        }

def duty_roster(request):
    # Get week start from query param (e.g. ?week=2026-04-13)
    week_param = request.GET.get('week')
    today = timezone.now().date()
    
    if week_param:
        try:
            start_of_week = datetime.strptime(week_param, '%Y-%m-%d').date()
        except ValueError:
            start_of_week = today - timedelta(days=today.weekday())
    else:
        start_of_week = today - timedelta(days=today.weekday())
    
    # Generate dates for the week (Monday to Sunday)
    week_dates = [start_of_week + timedelta(days=i) for i in range(7)]
    
    # Fetch all duties for this week
    duties = DutyRoster.objects.filter(date__gte=start_of_week, date__lte=start_of_week + timedelta(days=6))
    
    # Build matrix: staff.id -> date -> list of duties
    staff_members = Staff.objects.all()
    roster_matrix = {}
    for staff in staff_members:
        roster_matrix[staff.id] = {}
        for d in week_dates:
            roster_matrix[staff.id][d] = []
    
    for duty in duties:
        roster_matrix[duty.staff_id][duty.date].append(duty)
    
    # Week navigation
    prev_week = start_of_week - timedelta(days=7)
    next_week = start_of_week + timedelta(days=7)
    
    context = {
        'week_dates': week_dates,
        'staff_members': staff_members,
        'roster_matrix': roster_matrix,
        'prev_week': prev_week,
        'next_week': next_week,
        'current_week_start': start_of_week,
    }
    return render(request, 'parlour/beautician/duty_roster.html', context)

def duty_add(request):
    if request.method == 'POST':
        form = DutyRosterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Duty shift added successfully!')
            return redirect('duty_roster')
    else:
        form = DutyRosterForm()
    return render(request, 'parlour/beautician/duty_form.html', {'form': form, 'title': 'Add Duty Shift'})

def duty_delete(request, duty_id):
    duty = get_object_or_404(DutyRoster, id=duty_id)
    duty.delete()
    messages.success(request, 'Duty shift removed.')
    return redirect('duty_roster')

# ---------- Inline Form for PayoutPeriod ----------
class PayoutPeriodForm(ModelForm):
    class Meta:
        model = PayoutPeriod
        fields = ['name', 'start_date', 'end_date']
        widgets = {
            'start_date': DateInput(attrs={'type': 'date'}),
            'end_date': DateInput(attrs={'type': 'date'}),
        }

 #---------- Views ----------
def payout_periods(request):
    periods = PayoutPeriod.objects.all()
    return render(request, 'parlour/beautician/payout_periods.html', {'periods': periods})

def payout_period_add(request):
    if request.method == 'POST':
        form = PayoutPeriodForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Payout period created.')
            return redirect('payout_periods')
    else:
        form = PayoutPeriodForm()
    return render(request, 'parlour/beautician/payout_period_form.html', {'form': form, 'title': 'Add Payout Period'})

def payout_period_detail(request, period_id):
    period = get_object_or_404(PayoutPeriod, id=period_id)
    payouts = period.payouts.select_related('beautician__user').all()
    total_net = sum(p.net_pay for p in payouts)
    context = {
        'period': period,
        'payouts': payouts,
        'total_net': total_net,
    }
    return render(request, 'parlour/beautician/payout_period_detail.html', context)

def generate_payouts(request, period_id):
    period = get_object_or_404(PayoutPeriod, id=period_id)
    if period.is_processed:
        messages.warning(request, 'Payouts already generated for this period.')
        return redirect('payout_period_detail', period_id=period.id)

    # Get all completed appointments in this period
    appointments = Appointment.objects.filter(
        date__gte=period.start_date,
        date__lte=period.end_date,
        status='completed',
        beautician__isnull=False
    ).select_related('beautician', 'service')

    # Calculate commission per beautician
    commission_map = {}
    for apt in appointments:
        beautician = apt.beautician
        if beautician.commission_rate > 0:
            commission = apt.service.price * (beautician.commission_rate / 100)
        else:
            commission = 0
        commission_map[beautician.id] = commission_map.get(beautician.id, 0) + commission

    # Calculate hours from DutyRoster – but DutyRoster is linked to Staff, not Beautician.
    # If you have a way to track beautician hours, add it here. Otherwise set hours=0.
    # For now we'll set hours to 0 and base_salary=0.
    
    for beautician in Beautician.objects.all():
        total_commission = commission_map.get(beautician.id, 0)
        total_hours = 0
        base_salary = total_hours * beautician.hourly_rate
        net_pay = base_salary + total_commission

        Payout.objects.update_or_create(
            beautician=beautician,
            period=period,
            defaults={
                'total_hours': total_hours,
                'base_salary': base_salary,
                'total_commission': total_commission,
                'net_pay': net_pay,
                'status': 'pending',
            }
        )

    period.is_processed = True
    period.save()
    messages.success(request, f'Payouts generated for {period.name}')
    return redirect('payout_period_detail', period_id=period.id)

def update_payout(request, payout_id):
    payout = get_object_or_404(Payout, id=payout_id)
    if request.method == 'POST':
        # Update bonus, deductions, status, payment date
        bonus = Decimal(request.POST.get('bonus', 0))
        deductions = Decimal(request.POST.get('deductions', 0))
        payout.bonus = bonus
        payout.deductions = deductions
        payout.net_pay = payout.base_salary + payout.total_commission + bonus - deductions
        payout.status = request.POST.get('status')
        if request.POST.get('payment_date'):
            payout.payment_date = request.POST.get('payment_date')
        payout.save()
        messages.success(request, f'Payout for {payout.beautician.user.get_full_name()} updated.')
    return redirect('payout_period_detail', period_id=payout.period.id)

def delete_payout_period(request, period_id):
    """Delete a payout period and all associated payouts"""
    period = get_object_or_404(PayoutPeriod, id=period_id)
    if request.method == 'POST':
        period_name = period.name
        period.delete()  # This also deletes related payouts due to CASCADE
        messages.success(request, f'Payout period "{period_name}" has been deleted.')
        return redirect('payout_periods')
    # If GET request, redirect to list (prevents accidental deletion)
    return redirect('payout_periods')




def earnings_overview(request):
    # 1. Total money collected from customers
    total_revenue = Appointment.objects.filter(
        status='completed'
    ).aggregate(Sum('service__price'))['service__price__sum'] or 0

    # 2. Total money paid to staff (The net_pay we found earlier)
    total_staff_paid = Payout.objects.filter(
        period__is_processed=True
    ).aggregate(Sum('net_pay'))['net_pay__sum'] or 0

    # 3. Profit for the Parlour Owner
    parlour_profit = total_revenue - total_staff_paid

    context = {
        'total_revenue': total_revenue,
        'total_staff_paid': total_staff_paid,
        'parlour_profit': parlour_profit,
        # ... keep your other context items ...
    }
    return render(request, 'parlour/finance/earnings_overview.html', context)

# tax--- transaction============================



def tax_transaction_view(request):
    # Constants
    TAX_RATE = Decimal('0.18')  # 18%
    FEE_RATE = Decimal('0.02')  # 2%

    # Fetch appointments
    appointments = Appointment.objects.filter(status='completed').select_related('service')

    # Add calculated fields to each appointment object dynamically
    for txn in appointments:
        txn.tax_amount = txn.service.price * TAX_RATE
        txn.fee_amount = txn.service.price * FEE_RATE
        txn.final_amount = txn.service.price - txn.tax_amount - txn.fee_amount

    # Aggregate Totals
    total_gross = appointments.aggregate(Sum('service__price'))['service__price__sum'] or 0
    total_tax = total_gross * TAX_RATE
    total_fees = total_gross * FEE_RATE
    net_to_parlour = total_gross - total_tax - total_fees

    context = {
        'transactions': appointments,
        'total_gross': total_gross,
        'total_tax': total_tax,
        'total_fees': total_fees,
        'net_to_parlour': net_to_parlour,
        'tax_rate_percent': TAX_RATE * 100,
        'fee_rate_percent': FEE_RATE * 100,
    }
    return render(request, 'parlour/finance/tax_transactions.html', context)

# export earning ================

import csv
from django.http import HttpResponse

def export_earnings_csv(request):
    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="parlour_analytics.csv"'

    writer = csv.writer(response)
    # Write the header row
    writer.writerow(['Date', 'Customer', 'Service', 'Price', 'Tax (18%)', 'Platform Fee (2%)', 'Net Amount'])

    # Fetch completed appointments
    # Ensure you filter by request.user.parlour if you have multi-tenancy!
    appointments = Appointment.objects.filter(status='completed').select_related('service')

    for appt in appointments:
        price = appt.service.price
        tax = price * Decimal('0.18')
        fee = price * Decimal('0.02')
        net = price - tax - fee
        
        writer.writerow([
            appt.date.strftime('%Y-%m-%d'),
            appt.customer_name,
            appt.service.name,
            price,
            tax,
            fee,
            net
        ])

    return response

from django.db.models import Avg
from .models import Review, Beautician  # Ensure these are imported

def parlour_reviews_view(request):
    # 1. Find the Beauticians associated with the logged-in user.
    # I am assuming your Beautician model has a field like 'owner' or 'parlour_admin' 
    # that points to the User who is the boss.
    
    # If the logged-in User IS the beautician, use: beautician_user=request.user
    # If the logged-in User is the BOSS of beauticians, we need to find their staff:
    
    staff = Beautician.objects.filter(user=request.user)
    # If you have a different field like 'boss', change 'user' to 'boss'
    
    # 2. Filter reviews for appointments assigned to these staff members
    reviews = Review.objects.filter(
        appointment__beautician__in=staff
    ).select_related('appointment__service', 'appointment__beautician__user').order_by('-created_at')

    # 3. Calculate metrics
    average_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0

    context = {
        'reviews': reviews,
        'average_rating': round(average_rating, 1),
        'total_reviews': reviews.count(),
    }
    
    return render(request, 'parlour/customer-feedback/reviews.html', context)

from django.contrib.auth.models import User
from .models import Message
from django.contrib import messages

def message_center(request):
    inbox = Message.objects.filter(receiver=request.user).order_by('-created_at')
    sent_items = Message.objects.filter(sender=request.user).order_by('-created_at')

    # 1. Admins (Standard Django Users)
    admins = User.objects.filter(is_superuser=True)

    # 2. Staff (Using the 'beautician_profile' link we found earlier)
    staff = User.objects.filter(beautician_profile__isnull=False).exclude(id=request.user.id)

    # 3. Customers (The Fix)
    # Since your Appointment model uses 'customer_email'/name instead of a User account, 
    # we cannot send internal database messages to them. 
    # For now, we set this to an empty list to prevent the crash.
    customers = []

    if request.method == 'POST':
        receiver_id = request.POST.get('receiver')
        subject = request.POST.get('subject')
        body = request.POST.get('body')
        
        try:
            receiver = User.objects.get(id=receiver_id)
            Message.objects.create(
                sender=request.user,
                receiver=receiver,
                subject=subject,
                body=body
            )
            messages.success(request, "Message sent successfully!")
        except User.DoesNotExist:
            messages.error(request, "Recipient not found.")
            
        return redirect('message_center')

    context = {
        'inbox': inbox,
        'sent_items': sent_items,
        'admins': admins,
        'staff': staff,
        'customers': customers,
    }
    return render(request, 'parlour/customer-feedback/messages.html', context)

def support_desk(request):
    # Fetch only messages sent to the Admin from this user
    support_tickets = Message.objects.filter(
        sender=request.user, 
        receiver__is_superuser=True
    ).order_by('-created_at')

    context = {
        'tickets': support_tickets,
        'faq_items': [
            {'q': 'How do I export my earnings?', 'a': 'Go to the Analytics page and click Export CSV.'},
            {'q': 'Can I add multiple staff?', 'a': 'Yes, use the "Add Staff" button in your dashboard.'},
        ]
    }
    return render(request, 'parlour/support-desk/support-desk.html', context)