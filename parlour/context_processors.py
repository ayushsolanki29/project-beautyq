from django.conf import settings


def beautyq_settings(request):
    return {
        'STRIPE_PUBLISHABLE_KEY': getattr(settings, 'STRIPE_PUBLISHABLE_KEY', ''),
        'GEMINI_ENABLED': bool(getattr(settings, 'GEMINI_API_KEY', '')),
    }
