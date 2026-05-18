
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import Sum, Count
from .models import Booking, Parlour, Service, User, PlatformSetting, PayoutLog, SystemAuditLog
import calendar
from django.db.models.functions import ExtractMonth
from django.contrib.auth.models import User
from django.contrib import messages
from decimal import Decimal
from .utils import log_system_action  # Import your new logger utility!
from .models import SupportTicket

def admin_login(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('admin_dashboard')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

def admin_dashboard(request):
    # 1. Top Cards
    revenue = Booking.objects.filter(status='Completed').aggregate(Sum('amount'))['amount__sum'] or 0
    bookings_count = Booking.objects.filter(status='Active').count()
    services_count = Service.objects.count()
    users_count = User.objects.count()

    # 2. Dynamic Chart Logic
    monthly_stats = (
        Booking.objects.annotate(month=ExtractMonth('date'))
        .values('month')
        .annotate(total=Sum('amount'))
        .order_by('month')
    )
    labels = [calendar.month_name[i['month']][:3] for i in monthly_stats]
    chart_data = [float(i['total']) for i in monthly_stats]

    # 3. New Components (FIXED: swapped is_verified -> is_active & created_at -> date_registered)
    recent_bookings = Booking.objects.select_related('parlour').order_by('-id')[:5]
    verification_queue = Parlour.objects.filter(is_active=False).order_by('-date_registered')[:4]
    top_parlours = Parlour.objects.annotate(num_bookings=Count('booking')).order_by('-num_bookings')[:4]

    context = {
        'revenue': revenue,
        'bookings': bookings_count,
        'services': services_count,
        'users': users_count,
        'labels': labels,
        'chart_data': chart_data,
        'recent_bookings': recent_bookings,
        'verification_queue': verification_queue,
        'top_parlours': top_parlours,
    }
    return render(request, 'Admin/Admin-dashboard/dashboard.html', context)
 
#  -----------------------------------------------analytics ---------------------------------------

def platform_analytics(request):
    # 1. Monthly Revenue Trend (For the Line Chart)
    monthly_revenue = (
        Booking.objects.annotate(month=ExtractMonth('date'))
        .values('month')
        .annotate(total=Sum('amount'))
        .order_by('month')
    )
    
    chart_labels = [calendar.month_name[item['month']][:3] for item in monthly_revenue]
    chart_data = [float(item['total']) for item in monthly_revenue]

    # 2. Category Distribution (For a Pie/Doughnut Chart)
    # This shows which parlours are most active
    parlour_share = Parlour.objects.annotate(
        booking_count=Count('booking')
    ).values('name', 'booking_count').order_by('-booking_count')[:5]

    pie_labels = [item['name'] for item in parlour_share]
    pie_data = [item['booking_count'] for item in parlour_share]

    # 3. Growth Metrics
    total_revenue = Booking.objects.aggregate(Sum('amount'))['amount__sum'] or 0
    avg_booking_value = total_revenue / Booking.objects.count() if Booking.objects.count() > 0 else 0

    context = {
        'chart_labels': chart_labels,
        'chart_data': chart_data,
        'pie_labels': pie_labels,
        'pie_data': pie_data,
        'total_revenue': total_revenue,
        'avg_val': avg_booking_value,
    }
    return render(request, 'Admin/analytics/analytics.html', context)

# -----------------------------all user----------------------------------------------------------
def user_management(request):
    # Fetch all regular customers (excluding admins/staff)
    users = User.objects.filter(is_staff=False).order_by('-date_joined')
    
    context = {
        'users': users,
        'total_users': users.count(),
    }
    return render(request, 'Admin/all-users/user_list.html', context)

def toggle_user_status(request, user_id):
    # Function to block/unblock a user
    user = get_object_or_404(User, id=user_id)
    user.is_active = not user.is_active
    user.save()
    messages.success(request, f"Status updated for {user.username}")
    return redirect('user_list')

# This view handles loading the permissions for the selected role and saving the toggles when clicked.
from .models import RolePermission
from django.http import JsonResponse
import json

def role_permissions(request):
    # Get the selected role from the URL query parameters, default to 'owner'
    selected_role = request.GET.get('role', 'owner')
    
    # Fetch all permission rules for that specific role
    permissions = RolePermission.objects.filter(role=selected_role)
    
    context = {
        'selected_role': selected_role,
        'permissions': permissions,
        'role_choices': RolePermission.ROLE_CHOICES
    }
    return render(request, 'Admin/all-users/role_permissions.html', context)

def update_permission_toggle(request):
    # This handles the AJAX request when a switch is clicked
    if request.method == "POST":
        data = json.loads(request.body)
        permission_id = data.get('id')
        is_allowed = data.get('is_allowed')
        
        try:
            perm = RolePermission.objects.get(id=permission_id)
            perm.is_allowed = is_allowed
            perm.save()
            return JsonResponse({'status': 'success', 'message': 'Permission updated successfully.'})
        except RolePermission.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Permission record not found.'}, status=404)
            
    return JsonResponse({'status': 'error', 'message': 'Invalid Request'}, status=400)

from django.db.models import Count, Sum

def customer_management_list(request):
    # Fetch all regular customers cleanly without crashing on foreign key lookups
    customers = User.objects.filter(is_staff=False).order_by('-date_joined')
    
    context = {
        'customers': customers,
        'total_customer_count': customers.count(),
    }
    return render(request, 'Admin/all-users/customers_list.html', context)

# NEW: The view that handles processing the modal form submit action
def add_customer(request):
    if request.method == "POST":
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        # Validation: Check if the user already exists in the system
        if User.objects.filter(username=username).exists():
            messages.error(request, f"The username '{username}' is already taken.")
            return redirect('customer_management_list')
            
        if User.objects.filter(email=email).exists():
            messages.error(request, f"The email '{email}' is already registered.")
            return redirect('customer_management_list')
            
        # Create the customer record safely
        new_customer = User.objects.create_user(username=username, email=email, password=password)
        new_customer.is_staff = False  # Explicitly make sure they are a regular customer
        new_customer.save()
        
        messages.success(request, f"Customer account for {username} was successfully created!")
        
    return redirect('customer_management_list')

from .models import Parlour

def parlour_directory_list(request):
    # Fetch all registered salons along with their owner profile relations
    parlours = Parlour.objects.all().order_by('-date_registered')
    # Fetch available parlour owners to populate our form dropdown selection
    available_owners = User.objects.filter(is_staff=False)
    
    context = {
        'parlours': parlours,
        'available_owners': available_owners,
    }
    return render(request, 'Admin/parlour-branches/parlour_directory.html', context)

def add_parlour(request):
    if request.method == "POST":
        name = request.POST.get('parlour_name')
        owner_id = request.POST.get('owner_id')
        contact = request.POST.get('contact_number')
        address = request.POST.get('address')
        
        try:
            owner_user = User.objects.get(id=owner_id)
            # Create and save the new parlour registration row
            new_salon = Parlour.objects.create(
                name=name,
                owner=owner_user,
                contact_number=contact,
                address=address
            )
            messages.success(request, f"'{name}' has been successfully added to the system directory!")
        except User.DoesNotExist:
            messages.error(request, "Selected Owner account profile error.")
            
    return redirect('parlour_directory_list')

def pending_verification_list(request):
    # Fetch only the parlours where is_active is False (waiting for approval)
    pending_parlours = Parlour.objects.filter(is_active=False).order_by('-date_registered')
    
    context = {
        'pending_parlours': pending_parlours,
        'pending_count': pending_parlours.count(),
    }
    return render(request, 'Admin/parlour-branches/verify_parlours.html', context)

def approve_parlour(request, parlour_id):
    if request.method == "POST":
        try:
            parlour = Parlour.objects.get(id=parlour_id)
            parlour.is_active = True  # Flip the switch to make them live!
            parlour.save()
            messages.success(request, f"'{parlour.name}' has been successfully verified and is now live!")
        except Parlour.DoesNotExist:
            messages.error(request, "Parlour profile records not found.")
            
    return redirect('pending_verification_list')


# --------------------categories views--------------------
from .models import MasterCategory, ServiceType

# 1. View to display the list matrix
def category_catalog_list(request):
    categories = MasterCategory.objects.all().order_by('-created_at')
    return render(request, 'Admin/master-catelogs/categories_list.html', {'categories': categories})

# 2. View to add a new category row
def add_master_category(request):
    if request.method == "POST":
        name = request.POST.get('category_name')
        icon = request.POST.get('icon_class')
        description = request.POST.get('description')
        
        if MasterCategory.objects.filter(name__iexact=name).exists():
            messages.error(request, f"A master category named '{name}' already exists.")
        else:
            MasterCategory.objects.create(name=name, icon_class=icon, description=description)
            messages.success(request, f"Category '{name}' added successfully to the master catalog!")
            
    return redirect('category_catalog_list')

# 3. View to handle status toggle switch switches
def toggle_category_status(request, category_id):
    if request.method == "POST":
        category = get_object_or_404(MasterCategory, id=category_id)
        category.is_active = not category.is_active  # Flips True to False, or False to True
        category.save()
        messages.success(request, f"Status for '{category.name}' updated successfully.")
    return redirect('category_catalog_list')

# --------------------------------service type views------------------
# 1. List View Matrix
def service_type_list(request):
    services = ServiceType.objects.all().select_related('category').order_by('-created_at')
    # We fetch active categories so the admin can pick one in the dropdown form
    active_categories = MasterCategory.objects.filter(is_active=True)
    
    context = {
        'services': services,
        'categories': active_categories,
    }
    return render(request, 'Admin/master-catelogs/service_type_list.html', context)

# 2. Action View: Add Service Type
def add_service_type(request):
    if request.method == "POST":
        name = request.POST.get('service_name')
        category_id = request.POST.get('category_id')
        description = request.POST.get('description')
        
        category = get_object_or_404(MasterCategory, id=category_id)
        
        # Check if service already exists under this specific category
        if ServiceType.objects.filter(name__iexact=name, category=category).exists():
            messages.error(request, f"'{name}' already exists under the {category.name} category.")
        else:
            ServiceType.objects.create(name=name, category=category, description=description)
            messages.success(request, f"Service '{name}' has been added successfully!")
            
    return redirect('service_type_list')

# 3. Action View: Toggle Active Status Switch
def toggle_service_status(request, service_id):
    if request.method == "POST":
        service = get_object_or_404(ServiceType, id=service_id)
        service.is_active = not service.is_active
        service.save()
        messages.success(request, f"Status for '{service.name}' updated successfully.")
    return redirect('service_type_list')


# -------------comission views--------------------------------
def commission_dashboard(request):
    # 1. Get or create the global system commission rule
    global_rate_setting, created = PlatformSetting.objects.get_or_create(
        key="global_commission_percentage",
        defaults={
            'label': 'Global Commission Percentage',
            'value': '12.00',
            'field_type': 'text',
        }
    )
    
    # 2. Fetch all parlours to manage individual override rules
    parlours = Parlour.objects.all().order_by('-date_registered')
    
    # 3. Project Mock Metrics (For your dashboard display badges)
    # In your booking app development, you will calculate these using actual Appointment sums
    total_volume = 125400.00  # Total business booked through BeautyQ
    try:
        rate_val = float(global_rate_setting.value)
    except (TypeError, ValueError):
        rate_val = 12.0
    admin_earnings = (total_volume * rate_val) / 100
    
    context = {
        'global_rate': rate_val,
        'parlours': parlours,
        'total_volume': total_volume,
        'admin_earnings': admin_earnings,
        'vendor_payouts': total_volume - admin_earnings
    }
    return render(request, 'Admin/finance-payouts/comission_logic.html', context)

def update_parlour_override(request, parlour_id):
    if request.method == "POST":
        parlour = get_object_or_404(Parlour, id=parlour_id)
        override_value = request.POST.get('custom_commission')
        parlour.custom_commission = override_value
        parlour.save()
        messages.success(request, f"Custom commission split tier saved for '{parlour.name}'.")
    return redirect('commission_dashboard')

# -------------payouts views-------------------

def parlour_payout_manifest(request):
    parlours = Parlour.objects.all()
    payout_table_data = []

    for parlour in parlours:
        # 1. Fetch total successful appointment revenue (Assuming an Appointment model exists)
        # For calculation clarity: Let's assume a total business volume or fetch from your system:
        # If you don't have appointments populated yet, we default to 0.00 cleanly
        gross_volume = Decimal('0.00') 
        if hasattr(parlour, 'appointments'):
            gross_volume = parlour.appointments.filter(status='Completed').aggregate(total=Sum('price'))['total'] or Decimal('0.00')

        # 2. Determine applicable commission split rate
        global_rate = Decimal('12.00') # Base platform default
        if parlour.custom_commission and parlour.custom_commission > 0:
            rate_percentage = parlour.custom_commission
        else:
            rate_percentage = global_rate

        # 3. Compute absolute shares mathematically
        admin_cut = (gross_volume * rate_percentage) / 100
        total_parlour_earnings = gross_volume - admin_cut

        # 4. Calculate what has actually been paid out from our PayoutLog table rows
        total_paid_out = PayoutLog.objects.filter(parlour=parlour).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        # 5. Live remaining pending balance code rule
        remaining_balance = total_parlour_earnings - total_paid_out

        payout_table_data.append({
            'parlour': parlour,
            'gross_volume': gross_volume,
            'total_earning': total_parlour_earnings,
            'total_paid': total_paid_out,
            'balance': remaining_balance
        })

    # Fetch recent global transfer clearings to display historical records below the matrix
    recent_transactions = PayoutLog.objects.all().order_by('-payment_date')[:10]

    context = {
        'payout_records': payout_table_data,
        'transactions': recent_transactions
    }
    return render(request, 'Admin/finance-payouts/payouts_list.html', context)

# Action View: Process and document a cash settlement release
def release_vendor_payout(request, parlour_id):
    if request.method == "POST":
        parlour = get_object_or_404(Parlour, id=parlour_id)
        amount_to_pay = Decimal(request.POST.get('amount_to_pay', '0.00'))
        ref_id = request.POST.get('transaction_reference')

        if amount_to_pay <= 0:
            messages.error(request, "Payout disbursement amount must be greater than zero.")
        else:
            # Create a live verified payout transaction history stamp
            PayoutLog.objects.create(
                parlour=parlour,
                amount=amount_to_pay,
                transaction_reference=ref_id,
                processed_by=request.user
            )
            messages.success(request, f"Successfully cleared payment of ₹{amount_to_pay} for {parlour.name}!")
            
    return redirect('parlour_payout_manifest')

# --------------------------transaction-logs --------------------

from .models import TransactionLog

def transaction_logs_list(request):
    # Fetch all transaction log records ordered by newest first
    logs = TransactionLog.objects.all().select_related('customer', 'parlour').order_by('-timestamp')
    
    # Calculate live real-time aggregate dashboard stats
    success_volume = TransactionLog.objects.filter(status='Success').aggregate(total=Sum('amount'))['total'] or 0.00
    failed_count = TransactionLog.objects.filter(status='Failed').count()
    total_logs_count = logs.count()

    context = {
        'logs': logs,
        'success_volume': success_volume,
        'failed_count': failed_count,
        'total_logs_count': total_logs_count,
    }
    return render(request, 'Admin/finance-payouts/transaction_logs.html', context)

# ---------------------------system auodit---------------

# 1. Main View to render the logs data list
def system_audit_logs(request):
    logs = SystemAuditLog.objects.all().select_related('user').order_by('-timestamp')
    return render(request, 'Admin/system-logs/audit_logs.html', {'logs': logs})

# 2. UPDATED VIEW EXAMPLE: Logging a Global Commission Change
def update_global_commission(request):
    if request.method == "POST":
        new_rate = request.POST.get('global_rate')
        setting = PlatformSetting.objects.get(key="global_commission_percentage")
        old_rate = setting.value
        setting.value = new_rate
        setting.save()
        
        # Write live record to audit trail!
        log_system_action(
            request=request,
            action_type="UPDATE",
            module_affected="Finance & Commissions",
            description=f"Changed default global platform commission rate from {old_rate}% to {new_rate}%."
        )
        
        messages.success(request, f"Global platform commission rate updated to {new_rate}% successfully!")
    return redirect('commission_dashboard')

# 3. UPDATED VIEW EXAMPLE: Logging a Parlour Approval
def approve_parlour(request, parlour_id):
    if request.method == "POST":
        try:
            parlour = Parlour.objects.get(id=parlour_id)
            parlour.is_active = True
            parlour.save()
            
            # Write live record to audit trail!
            log_system_action(
                request=request,
                action_type="APPROVAL",
                module_affected="Parlour Management",
                description=f"Verified and approved parlour network profile branch node: '{parlour.name}'."
            )
            
            messages.success(request, f"'{parlour.name}' has been successfully verified and is now live!")
        except Parlour.DoesNotExist:
            messages.error(request, "Parlour profile records not found.")
            
    return redirect('pending_verification_list')


# ------------------------globle support view----------------

# 1. Main Support Center Dashboard Matrix
def global_support_center(request):
    # Fetch all tickets ordered by critical urgency and newest date first
    tickets = SupportTicket.objects.all().select_related('user').order_by('-created_at')
    
    # Calculate quick analytical count parameters for summary displays
    total_tickets = tickets.count()
    open_tickets = SupportTicket.objects.filter(status='Open').count()
    resolved_tickets = SupportTicket.objects.filter(status='Resolved').count()

    context = {
        'tickets': tickets,
        'total_count': total_tickets,
        'open_count': open_tickets,
        'resolved_count': resolved_tickets,
    }
    return render(request, 'Admin/global-support/support_center.html', context)

# 2. Action View: Update Ticket Status
def update_ticket_status(request, ticket_id):
    if request.method == "POST":
        ticket = get_object_or_404(SupportTicket, id=ticket_id)
        
        # 1. Capture the reply text typed into the textarea box
        reply_text = request.POST.get('admin_reply_message')
        
        if reply_text:
            ticket.admin_reply = reply_text
            ticket.status = 'Resolved' # Automatically switch state to settled upon reply entry
            ticket.save()
            messages.success(request, f"Reply message attached and Ticket #{ticket.ticket_id} marked as Resolved!")
        else:
            messages.error(request, "Reply message content box cannot be blank.")
            
    return redirect('global_support_center')

# ---------------global offer--------------------

from .models import GlobalOffer
from datetime import date

# 1. Main Offers Catalog View Registry
def global_offers_catalog(request):
    offers = GlobalOffer.objects.all().order_by('-created_at')
    
    # Quick live summary counts for analytics badges
    total_offers = offers.count()
    active_offers = GlobalOffer.objects.filter(is_active=True, expiry_date__gte=date.today()).count()
    
    context = {
        'offers': offers,
        'total_offers': total_offers,
        'active_offers': active_offers,
    }
    return render(request, 'Admin/global-offers/offers_list.html', context)

# 2. Action View: Add New Coupon Row
def add_global_offer(request):
    if request.method == "POST":
        code = request.POST.get('coupon_code').upper().strip()
        name = request.POST.get('offer_name')
        d_type = request.POST.get('discount_type')
        value = request.POST.get('discount_value')
        min_val = request.POST.get('min_basket_value')
        exp_date = request.POST.get('expiry_date')

        if GlobalOffer.objects.filter(coupon_code=code).exists():
            messages.error(request, f"A coupon coupon rule with the code '{code}' already exists.")
        else:
            GlobalOffer.objects.create(
                coupon_code=code,
                offer_name=name,
                discount_type=d_type,
                discount_value=value,
                min_basket_value=min_val,
                expiry_date=exp_date
            )
            messages.success(request, f"Global promotional coupon '{code}' added successfully!")
            
    return redirect('global_offers_catalog')

# 3. Action View: Toggle Coupon Availability Switch
def toggle_offer_status(request, offer_id):
    if request.method == "POST":
        offer = get_object_or_404(GlobalOffer, id=offer_id)
        offer.is_active = not offer.is_active
        offer.save()
        messages.success(request, f"Status for promotional code '{offer.coupon_code}' updated successfully.")
    return redirect('global_offers_catalog')

# ------------settings--------

from .models import PlatformSetting

def platform_settings_dashboard(request):
    # 1. Initialize default core settings rows cleanly if the database table is completely fresh
    default_settings = [
        {"key": "platform_name", "label": "Application System Name", "value": "BeautyQ PRO", "field_type": "text"},
        {"key": "support_email", "label": "Global Helpdesk Contact Email", "value": "support@beautyq.com", "field_type": "text"},
        {"key": "contact_phone", "label": "Official Support Telephone Hotline", "value": "+91 9876543210", "field_type": "text"},
        {"key": "maintenance_mode", "label": "System Maintenance Block Mode", "value": "False", "field_type": "boolean"},
    ]
    
    for setting in default_settings:
        PlatformSetting.objects.get_or_create(
            key=setting["key"],
            defaults={
                "label": setting["label"],
                "value": setting["value"],
                "field_type": setting["field_type"]
            }
        )

    # 2. Handle configuration updates post submission
    if request.method == "POST":
        all_settings = PlatformSetting.objects.all()
        for setting in all_settings:
            # Handle standard text or boolean keys dynamically
            if setting.field_type == "boolean":
                form_value = request.POST.get(setting.key, "False")
            else:
                form_value = request.POST.get(setting.key, "").strip()
            
            setting.value = form_value
            setting.save()
            
        messages.success(request, "Global platform configuration controls updated successfully!")
        return redirect('platform_settings_dashboard')

    # Fetch rows to present live values onto the HTML template blocks
    settings_records = PlatformSetting.objects.all().order_by('id')
    return render(request, 'Admin/platform-settings/settings_panel.html', {'settings': settings_records})