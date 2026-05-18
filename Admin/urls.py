from django.urls import path
from . import views

# Ensure the name is exactly 'urlpatterns' (plural)
urlpatterns = [
   path('', views.admin_dashboard, name='admin_dashboard'),
   path('analytics/', views.platform_analytics, name='platform_analytics'),
   path('users/', views.user_management, name='user_list'),
   path('users/toggle/<int:user_id>/', views.toggle_user_status, name='toggle_user_status'),

#    these routes to your admin routing paths

   path('role-permissions/', views.role_permissions, name='role_permissions'),
   path('role-permissions/update/', views.update_permission_toggle, name='update_permission_toggle'),

   path('customers/', views.customer_management_list, name='customer_management_list'),
   path('customers/add/', views.add_customer, name='add_customer'),

   path('parlours/', views.parlour_directory_list, name='parlour_directory_list'),
   path('parlours/add/', views.add_parlour, name='add_parlour'),

   path('verify-requests/', views.pending_verification_list, name='pending_verification_list'),
   path('verify-requests/approve/<int:parlour_id>/', views.approve_parlour, name='approve_parlour'),
    # ... other paths

   path('categories/', views.category_catalog_list, name='category_catalog_list'),
   path('categories/add/', views.add_master_category, name='add_master_category'),
   path('categories/toggle/<int:category_id>/', views.toggle_category_status, name='toggle_category_status'),

   path('services/', views.service_type_list, name='service_type_list'),
   path('services/add/', views.add_service_type, name='add_service_type'),
   path('services/toggle/<int:service_id>/', views.toggle_service_status, name='toggle_service_status'),

   path('finance/commission/', views.commission_dashboard, name='commission_dashboard'),
   path('finance/commission/update-global/', views.update_global_commission, name='update_global_commission'),
   path('finance/commission/override/<int:parlour_id>/', views.update_parlour_override, name='update_parlour_override'),

   path('finance/payouts/', views.parlour_payout_manifest, name='parlour_payout_manifest'),
   path('finance/payouts/release/<int:parlour_id>/', views.release_vendor_payout, name='release_vendor_payout'),

   path('finance/transactions/', views.transaction_logs_list, name='transaction_logs_list'),

   path('system-logs/', views.system_audit_logs, name='system_audit_logs'),

   path('support/', views.global_support_center, name='global_support_center'),
   path('support/update/<int:ticket_id>/', views.update_ticket_status, name='update_ticket_status'),

   path('offers/', views.global_offers_catalog, name='global_offers_catalog'),
   path('offers/add/', views.add_global_offer, name='add_global_offer'),
   path('offers/toggle/<int:offer_id>/', views.toggle_offer_status, name='toggle_offer_status'),

   path('settings/', views.platform_settings_dashboard, name='platform_settings_dashboard'),
]