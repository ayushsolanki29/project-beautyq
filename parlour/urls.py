from django.urls import path
from . import views, customer_views
from .views import (
    ServiceListView, ServiceCreateView,
    ServiceUpdateView, ServiceDeleteView, PackageListView, PackageCreateView,
    PackageUpdateView, PackageDeleteView, PromoListView, PromoCreateView,
    PromoUpdateView, PromoDeleteView,
)


urlpatterns = [
    path('', customer_views.customer_home, name='customer_home'),
    path('services/', customer_views.services_catalog, name='services_catalog'),
    path('packages/', customer_views.packages_catalog, name='packages_catalog'),
    path('book/', customer_views.book_appointment, name='book_appointment'),
    path('booking/success/', customer_views.booking_success, name='booking_success'),
    path('booking/cancel/', customer_views.booking_cancel, name='booking_cancel'),
    path('my-appointments/', customer_views.my_appointments, name='my_appointments'),
    path('ai-advisor/', customer_views.ai_beauty_advisor, name='ai_advisor'),
    path('register/', customer_views.register_customer, name='register_customer'),
    path('register/owner/', customer_views.register_owner, name='register_owner'),
    path('dashboard', views.dashboard, name='parlour-dashboard'),
    path('appointments/new-requests/', views.NewRequestsView.as_view(), name='new_requests'),
    path('appointments/<int:appointment_id>/confirm/', views.confirm_appointment, name='confirm_appointment'),
    path('appointments/<int:appointment_id>/decline/', views.decline_appointment, name='decline_appointment'),
    path('appointments/today-schedule/', views.TodayScheduleView.as_view(), name='today_schedule'),
    path('appointments/history/', views.BookingHistoryView.as_view(), name='booking_history'),
    path('catalog/services/', ServiceListView.as_view(), name='all_services'),
    path('catalog/services/add/', ServiceCreateView.as_view(), name='service_add'),
    path('catalog/services/<int:pk>/edit/', ServiceUpdateView.as_view(), name='service_edit'),
    path('catalog/services/<int:pk>/delete/', ServiceDeleteView.as_view(), name='service_delete'),
    path('catalog/packages/', PackageListView.as_view(), name='all_packages'),
    path('catalog/packages/add/', PackageCreateView.as_view(), name='package_add'),
    path('catalog/packages/<int:pk>/edit/', PackageUpdateView.as_view(), name='package_edit'),
    path('catalog/packages/<int:pk>/delete/', PackageDeleteView.as_view(), name='package_delete'),
    path('catalog/promos/', PromoListView.as_view(), name='all_promos'),
    path('catalog/promos/add/', PromoCreateView.as_view(), name='promo_add'),
    path('catalog/promos/<int:pk>/edit/', PromoUpdateView.as_view(), name='promo_edit'),
    path('catalog/promos/<int:pk>/delete/', PromoDeleteView.as_view(), name='promo_delete'),
     path('staff/', views.staff_list, name='staff_list'),
    path('staff/add/', views.staff_add, name='staff_add'),
     path('duty-roster/', views.duty_roster, name='duty_roster'),
    path('duty/add/', views.duty_add, name='duty_add'),
    path('duty/delete/<int:duty_id>/', views.duty_delete, name='duty_delete'),
    path('payouts/', views.payout_periods, name='payout_periods'),
    path('payouts/add/', views.payout_period_add, name='payout_period_add'),
    path('payouts/<int:period_id>/', views.payout_period_detail, name='payout_period_detail'),
    path('payouts/<int:period_id>/generate/', views.generate_payouts, name='generate_payouts'),
    path('payouts/update/<int:payout_id>/', views.update_payout, name='update_payout'),
    path('payouts/delete/<int:period_id>/', views.delete_payout_period, name='delete_payout_period'),
    path('earnings/', views.earnings_overview, name='earnings_overview'),
    path('transactions/', views.tax_transaction_view, name='tax_transactions'),
    path('export/analytics/', views.export_earnings_csv, name='export_analytics'),
    # URL for the Reviews Page
    path('reviews/', views.parlour_reviews_view, name='parlour_reviews'),

    # URL for the Message Center
    path('messages/', views.message_center, name='message_center'),
    path('supportdesk/', views.support_desk, name='support_desk'),

]
