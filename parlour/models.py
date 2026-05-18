from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
from django.db.models import Sum
from django.shortcuts import render
from django.db.models import Avg

# ========== EXISTING MODELS (kept as you had) ==========

class Service(models.Model):
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=100, default="hair")
    duration = models.PositiveIntegerField(help_text="Duration in minutes")
    price = models.DecimalField(max_digits=8, decimal_places=2)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='services/', blank=True, null=True)

    def __str__(self):
        return self.name

class Beautician(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='beautician_profile')
    specialty = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=15)
    is_active = models.BooleanField(default=True)
    # NEW fields for payouts:
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)  # e.g., 20.00 = 20%

    def __str__(self):
        return self.user.get_full_name() or self.user.username

class Appointment(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    PAYMENT_STATUS_CHOICES = (
        ('unpaid', 'Unpaid'),
        ('paid', 'Paid'),
        ('refunded', 'Refunded'),
    )

    customer_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='appointments')
    customer_name = models.CharField(max_length=100)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=15)
    service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True)
    beautician = models.ForeignKey(Beautician, on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateField()
    time = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='unpaid')
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    stripe_session_id = models.CharField(max_length=255, blank=True)
    promo_code = models.CharField(max_length=20, blank=True)
    queue_position = models.PositiveIntegerField(default=0)
    turn_notified = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-time']

    def __str__(self):
        return f"{self.customer_name} - {self.service} on {self.date} at {self.time}"

    @property
    def service_price(self):
        return self.service.price if self.service else Decimal('0.00')


class CustomerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='customer_profile')
    phone = models.CharField(max_length=15, blank=True)
    preferred_category = models.CharField(max_length=50, blank=True, default='hair')

    def __str__(self):
        return self.user.get_full_name() or self.user.username

class ServicePackage(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    services = models.ManyToManyField(Service, related_name='packages')
    original_price = models.DecimalField(max_digits=8, decimal_places=2)
    package_price = models.DecimalField(max_digits=8, decimal_places=2)
    image = models.ImageField(upload_to='packages/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def discount_percentage(self):
        if self.original_price > 0:
            return round((1 - self.package_price / self.original_price) * 100)
        return 0

class PromoCode(models.Model):
    DISCOUNT_TYPE_CHOICES = (
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    )

    code = models.CharField(max_length=20, unique=True)
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPE_CHOICES)
    discount_value = models.DecimalField(max_digits=8, decimal_places=2)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    max_uses = models.PositiveIntegerField(default=1)
    used_count = models.PositiveIntegerField(default=0, editable=False)
    min_order_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.code

    def is_valid(self):
        now = timezone.now()
        return (self.is_active and self.valid_from <= now <= self.valid_to and self.used_count < self.max_uses)

# ========== STAFF & DUTY ROSTER (if you need admin staff) ==========
# Keep these if you want a separate staff (reception, manager) – they are NOT beauticians
class Staff(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, blank=True)
    position = models.CharField(max_length=100)
    hire_date = models.DateField()

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    class Meta:
        ordering = ['last_name', 'first_name']

class DutyRoster(models.Model):
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='duties')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    role = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['date', 'start_time']
        unique_together = ['staff', 'date', 'start_time']

    def __str__(self):
        return f"{self.staff.first_name} {self.staff.last_name} - {self.date}"

# ========== NEW PAYOUT MODELS (for beauticians only) ==========

class PayoutPeriod(models.Model):
    name = models.CharField(max_length=100, help_text="e.g., March 2026 (Week 1)")
    start_date = models.DateField()
    end_date = models.DateField()
    is_processed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-start_date']

    def get_total(self):
        return self.payouts.aggregate(Sum('amount'))['amount__sum'] or 0

class Payout(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    )

    beautician = models.ForeignKey(Beautician, on_delete=models.CASCADE, related_name='payouts')
    period = models.ForeignKey(PayoutPeriod, on_delete=models.CASCADE, related_name='payouts')
    total_hours = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    base_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_commission = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    bonus = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    net_pay = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ['beautician', 'period']

    def __str__(self):
        return f"{self.beautician.user.get_full_name()} – {self.period.name}"
    

from django.core.validators import MaxValueValidator, MinValueValidator

class Review(models.Model):
    # Link it to the appointment so you know which service was reviewed
    appointment = models.OneToOneField('Appointment', on_delete=models.CASCADE, related_name='review')
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review for {self.appointment.service.name} - {self.rating} Stars"
    
from django.contrib.auth.models import User

class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    subject = models.CharField(max_length=255)
    body = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender.username} to {self.receiver.username}: {self.subject}"
    
