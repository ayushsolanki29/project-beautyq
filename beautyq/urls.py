"""
URL configuration for beautyq project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from parlour.auth_views import BeautyQLoginView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/login/', BeautyQLoginView.as_view(), name='login'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('', include('parlour.urls')),
    path('myadmin/', include('Admin.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
