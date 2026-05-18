from .models import SystemAuditLog

def log_system_action(request, action_type, module_affected, description):
    # Extracts the visitor IP address safely
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
        
    SystemAuditLog.objects.create(
        user=request.user if request.user.is_authenticated else None,
        action_type=action_type,
        module_affected=module_affected,
        description=description,
        ip_address=ip
    )