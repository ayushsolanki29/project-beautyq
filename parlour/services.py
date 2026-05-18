"""External integrations: Gemini AI and Stripe payments."""

import hashlib
import json
import logging
import time
import urllib.error
import urllib.request
from decimal import Decimal

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

GEMINI_MODELS = (
    'gemini-2.5-flash',
    'gemini-2.5-flash-lite',
    'gemini-2.5-flash',
)
GEMINI_RETRY_ATTEMPTS = 3
GEMINI_RETRY_BASE_DELAY = 2.0
GEMINI_ADVICE_CACHE_SECONDS = 3600
AI_SESSION_RATE_LIMIT = 8
AI_SESSION_RATE_WINDOW = 60


def _gemini_url(model: str, api_key: str) -> str:
    return (
        'https://generativelanguage.googleapis.com/v1beta/models/'
        f'{model}:generateContent?key={api_key}'
    )


def _build_gemini_payload(prompt: str) -> dict:
    return {
        'contents': [{
            'parts': [{
                'text': (
                    'You are BeautyQ, a professional salon beauty advisor. '
                    'Give concise, friendly advice about hair, skin, nails, and salon services. '
                    f'Customer question: {prompt}'
                )
            }]
        }]
    }


def _parse_gemini_response(data: dict) -> str | None:
    candidates = data.get('candidates', [])
    if not candidates:
        return None
    parts = candidates[0].get('content', {}).get('parts', [])
    if parts:
        return parts[0].get('text')
    return None


def _call_gemini_once(model: str, api_key: str, prompt: str, timeout: int = 30) -> str:
    payload = _build_gemini_payload(prompt)
    req = urllib.request.Request(
        _gemini_url(model, api_key),
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST',
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode('utf-8'))
    text = _parse_gemini_response(data)
    if text:
        return text
    raise ValueError('Could not generate advice. Please try again.')


def _retry_delay(attempt: int, retry_after: str | None) -> float:
    if retry_after:
        try:
            return max(float(retry_after), 1.0)
        except ValueError:
            pass
    return GEMINI_RETRY_BASE_DELAY * (2 ** attempt)


def _generate_with_model(model: str, api_key: str, prompt: str) -> str:
    last_error = None
    for attempt in range(GEMINI_RETRY_ATTEMPTS):
        try:
            return _call_gemini_once(model, api_key, prompt)
        except urllib.error.HTTPError as exc:
            last_error = exc
            if exc.code == 429 and attempt < GEMINI_RETRY_ATTEMPTS - 1:
                delay = _retry_delay(attempt, exc.headers.get('Retry-After'))
                logger.warning('Gemini 429 on %s, retrying in %.1fs', model, delay)
                time.sleep(delay)
                continue
            raise
        except urllib.error.URLError as exc:
            last_error = exc
            if attempt < GEMINI_RETRY_ATTEMPTS - 1:
                time.sleep(_retry_delay(attempt, None))
                continue
            raise
    if last_error:
        raise last_error
    raise RuntimeError('Gemini request failed')


def _friendly_gemini_error(exc: Exception) -> str:
    if isinstance(exc, urllib.error.HTTPError):
        if exc.code == 429:
            return (
                'The AI service is busy right now (rate limit reached). '
                'Please wait a minute and try again. '
                'If this keeps happening, your API key may have hit its daily quota — '
                'check usage at https://aistudio.google.com/'
            )
        if exc.code in (401, 403):
            return 'AI advisor API key is invalid or not authorized. Check GEMINI_API_KEY in .env.'
        if exc.code == 404:
            return 'AI model is unavailable. Please contact the site administrator.'
    return (
        'AI service temporarily unavailable. Please try again in a moment. '
        f'({exc})'
    )


def check_ai_session_rate_limit(session) -> str | None:
    """Return an error message if the session exceeded the local rate limit."""
    now = time.time()
    key = 'ai_advisor_timestamps'
    timestamps = [t for t in session.get(key, []) if now - t < AI_SESSION_RATE_WINDOW]
    if len(timestamps) >= AI_SESSION_RATE_LIMIT:
        return (
            f'You have reached the limit of {AI_SESSION_RATE_LIMIT} questions per minute. '
            'Please wait a moment before trying again.'
        )
    return None


def record_ai_session_request(session) -> None:
    now = time.time()
    key = 'ai_advisor_timestamps'
    timestamps = [t for t in session.get(key, []) if now - t < AI_SESSION_RATE_WINDOW]
    timestamps.append(now)
    session[key] = timestamps
    session.modified = True


def get_cached_gemini_advice(prompt: str) -> str | None:
    normalized = prompt.strip()
    if not normalized:
        return None
    cache_key = 'gemini_advice:' + hashlib.sha256(normalized.lower().encode()).hexdigest()
    return cache.get(cache_key)


def get_gemini_advice(prompt: str) -> tuple[str, bool]:
    """
    Return (message, is_error).
    Uses cache, model fallbacks, and retries on transient 429 errors.
    """
    api_key = getattr(settings, 'GEMINI_API_KEY', '')
    if not api_key:
        return ('AI advisor is not configured. Add GEMINI_API_KEY to your .env file.', True)

    normalized = prompt.strip()
    if not normalized:
        return ('Please enter a question.', True)

    cache_key = 'gemini_advice:' + hashlib.sha256(normalized.lower().encode()).hexdigest()
    cached = cache.get(cache_key)
    if cached:
        return (cached, False)

    last_exc = None
    for model in GEMINI_MODELS:
        try:
            advice = _generate_with_model(model, api_key, normalized)
            cache.set(cache_key, advice, GEMINI_ADVICE_CACHE_SECONDS)
            return (advice, False)
        except urllib.error.HTTPError as exc:
            last_exc = exc
            if exc.code == 429:
                logger.warning('Gemini model %s rate limited, trying fallback', model)
                continue
            return (_friendly_gemini_error(exc), True)
        except Exception as exc:
            last_exc = exc
            logger.exception('Gemini request failed for model %s', model)
            continue

    return (_friendly_gemini_error(last_exc or RuntimeError('All models failed')), True)


def create_stripe_checkout_session(appointment, success_url: str, cancel_url: str):
    secret = getattr(settings, 'STRIPE_SECRET_KEY', '')
    if not secret:
        raise ValueError('Stripe is not configured. Add STRIPE_SECRET_KEY to .env')

    try:
        import stripe
    except ImportError:
        raise ValueError('Stripe library not installed. Run: pip install stripe')

    stripe.api_key = secret
    amount = int((appointment.service.price if appointment.service else Decimal('0')) * 100)

    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'inr',
                'product_data': {
                    'name': appointment.service.name if appointment.service else 'Salon Service',
                    'description': f'Appointment on {appointment.date} at {appointment.time}',
                },
                'unit_amount': max(amount, 100),
            },
            'quantity': 1,
        }],
        mode='payment',
        success_url=success_url + '?session_id={CHECKOUT_SESSION_ID}',
        cancel_url=cancel_url,
        customer_email=appointment.customer_email,
        metadata={'appointment_id': str(appointment.id)},
    )
    return session
