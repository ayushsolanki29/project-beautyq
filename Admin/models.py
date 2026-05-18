
from django.db import models
from django.contrib.auth.models import User # Use Django's built-in User

class Parlour(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='parlours')
    name = models.CharField(max_length=100)
    contact_number = models.CharField(max_length=15)
    address = models.TextField()
    is_active = models.BooleanField(default=True)
    date_registered = models.DateTimeField(auto_now_add=True)
    custom_commission = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text="Set above 0 to override global rate")
    def __str__(self):
        return self.name

class Service(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name

class Booking(models.Model):
    parlour = models.ForeignKey(Parlour, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, default='Pending')
    date = models.DateField(auto_now_add=True)

# this model define the permissions for each role

class RolePermission(models.Model):
    ROLE_CHOICES = [
        ('admin', 'System Admin'),
        ('owner', 'Parlour Owner'),
        ('staff', 'Service Staff'),
        ('customer', 'Customer'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    module_name = models.CharField(max_length=50)  # e.g., 'Bookings', 'Services'
    feature_name = models.CharField(max_length=50) # e.g., 'Manage Status', 'Add Services'
    codename = models.CharField(max_length=50)     # e.g., 'can_manage_status'
    is_allowed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.get_role_display()} - {self.feature_name}: {self.is_allowed}"

# ---------------------categories model------------------
class MasterCategory(models.Model):
    name = models.CharField(max_length=50, unique=True)
    icon_class = models.CharField(max_length=50, default="fa-solid fa-sparkles", help_text="FontAwesome class name e.g. fa-solid fa-scissors")
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

#  -------------------------------servicetype----------------------------
class ServiceType(models.Model):
    category = models.ForeignKey(MasterCategory, on_delete=models.CASCADE, related_name='service_types')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.category.name})"
    
# --------------payouts & logs ----------------------------

class PayoutLog(models.Model):
    parlour = models.ForeignKey(Parlour, on_delete=models.CASCADE, related_name='payouts')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_reference = models.CharField(max_length=100, unique=True, help_text="Bank transfer UTR or Txn ID")
    payment_date = models.DateTimeField(auto_now_add=True)
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"₹{self.amount} to {self.parlour.name} on {self.payment_date.strftime('%d-%m-%Y')}"
    
# ----------------transaction-logs-----------------

class TransactionLog(models.Model):
    # Status option choices
    STATUS_CHOICES = [
        ('Success', 'Success'),
        ('Failed', 'Failed'),
        ('Refunded', 'Refunded'),
    ]

    transaction_id = models.CharField(max_length=100, unique=True, help_text="Unique Gateway Order/Payment ID")
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    parlour = models.ForeignKey(Parlour, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=50, default="UPI / Card")
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='Success')
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_id} - ₹{self.amount} ({self.status})"
    

# ----------------------audit log dashboard model-----------------

class SystemAuditLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action_type = models.CharField(max_length=50, help_text="e.g., CREATE, UPDATE, DELETE, APPROVAL")
    module_affected = models.CharField(max_length=100, help_text="e.g., Parlour, Finance, User Management")
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username if self.user else 'System'} - {self.action_type} on {self.timestamp.strftime('%d-%m-%Y')}"
    

# --------------------globle support ticket------------------

class SupportTicket(models.Model):
    PRIORITY_CHOICES = [
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
        ('Critical', 'Critical'),
    ]
    
    STATUS_CHOICES = [
        ('Open', 'Open'),
        ('In Progress', 'In Progress'),
        ('Resolved', 'Resolved'),
    ]

    ticket_id = models.CharField(max_length=20, unique=True, help_text="Generated Ticket Reference Number")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='support_tickets')
    subject = models.CharField(max_length=150)
    message = models.TextField()
    priority = models.CharField(max_length=15, choices=PRIORITY_CHOICES, default='Medium')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='Open')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    admin_reply = models.TextField(null=True, blank=True, help_text="Official response text sent by platform admin")

    def __str__(self):
        return f"#{self.ticket_id} - {self.subject} ({self.status})"
    
# ----------------------global offer model----------

class GlobalOffer(models.Model):
    OFFER_TYPE_CHOICES = [
        ('Percentage', 'Percentage (%)'),
        ('Flat', 'Flat Amount (₹)'),
    ]

    coupon_code = models.CharField(max_length=20, unique=True, help_text="e.g., FESTIVAL20, BEAUTYQ50")
    offer_name = models.CharField(max_length=100, help_text="e.g., Monsoon Flash Discount")
    discount_type = models.CharField(max_length=15, choices=OFFER_TYPE_CHOICES, default='Percentage')
    discount_value = models.DecimalField(max_digits=6, decimal_places=2, help_text="Percentage rate or direct flat deduction cut")
    min_basket_value = models.DecimalField(max_digits=8, decimal_places=2, default=0.00, help_text="Minimum appointment billing required to apply code")
    expiry_date = models.DateField()
    is_active = models.BooleanField(default=True, help_text="Toggle visibility across platform checkout loops")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.coupon_code} - {self.offer_name}"
    
# =--------------------settings------------------------

class PlatformSetting(models.Model):
    key = models.CharField(max_length=100, unique=True, help_text="Unique internal code handle, e.g., platform_email")
    label = models.CharField(max_length=100, help_text="Human-readable title, e.g., Support Contact Email")
    value = models.TextField(help_text="The actual running parameter value stored")
    field_type = models.CharField(max_length=20, default="text", help_text="text, textarea, or boolean")

    def __str__(self):
        return f"{self.label}: {self.value}"