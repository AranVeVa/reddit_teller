import os
import logging
from pathlib import Path
from dotenv import load_dotenv
import stripe

from server import db

ROOT = Path(__file__).parent.parent.resolve()
load_dotenv(ROOT / ".env")

logger = logging.getLogger("reddit_teller.payments")

# ── Config ─────────────────────────────────────────────────────────────────

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "").strip()
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "").strip()

FRONTEND_URL = (
    os.getenv("FRONTEND_URL")
    or os.getenv("APP_BASE_URL")     # fallback por compatibilidad
    or "http://localhost:5173"
).rstrip("/")

PRO_PRICE_CENTS = int(os.getenv("PRO_PRICE_CENTS", "999"))     # $9.99
PRO_CURRENCY = os.getenv("PRO_CURRENCY", "usd").lower()
PRO_INTERVAL = os.getenv("PRO_INTERVAL", "month")              # month|year

if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY


# ── Excepción pública ──────────────────────────────────────────────────────

class PaymentError(Exception):
    """Error controlado de pago. app.py lo mapea a 400/402/500 según contexto."""


# ── Modo / config ──────────────────────────────────────────────────────────

def get_mode() -> str:
    return "stripe" if STRIPE_SECRET_KEY else "simulated"


def get_config() -> dict:
    return {
        "mode": get_mode(),
        "price_usd": PRO_PRICE_CENTS / 100,
        "currency": PRO_CURRENCY.upper(),
        "interval": PRO_INTERVAL,
        "publishable_key": os.getenv("STRIPE_PUBLIC_KEY", "").strip(),
    }


# ── Stripe: crear sesión ───────────────────────────────────────────────────

def create_checkout_session(user: dict) -> str:
    """Crea un Checkout Session y devuelve la URL a la que redirigir."""
    if not STRIPE_SECRET_KEY:
        raise PaymentError("Stripe no está configurado")
    if db.has_premium_access(user):
        raise PaymentError("Tu cuenta ya tiene acceso Premium")

    try:
        session = stripe.checkout.Session.create(
            mode="subscription",
            line_items=[{
                "price_data": {
                    "currency": PRO_CURRENCY,
                    "product_data": {"name": "Plan Pro Reddit Teller"},
                    "unit_amount": PRO_PRICE_CENTS,
                    "recurring": {"interval": PRO_INTERVAL},
                },
                "quantity": 1,
            }],
            customer_email=user.get("email"),
            client_reference_id=user["id"],
            metadata={"user_id": user["id"]},
            success_url=(
                f"{FRONTEND_URL}/?payment=success"
                "&session_id={CHECKOUT_SESSION_ID}"
            ),
            cancel_url=f"{FRONTEND_URL}/?payment=cancelled",
        )
        return session.url
    except stripe.error.StripeError as e:
        logger.exception("Stripe create_checkout_session falló")
        raise PaymentError(f"Error de Stripe: {getattr(e, 'user_message', None) or e}")


# ── Stripe: confirmar sesión (flujo local) ─────────────────────────────────

def confirm_checkout_session(user: dict, session_id: str) -> dict:
    """Verifica que la sesión pertenece al usuario y que fue pagada. Sube a Pro."""
    if not STRIPE_SECRET_KEY:
        raise PaymentError("Stripe no está configurado")
    if not session_id:
        raise PaymentError("session_id vacío")

    try:
        session = stripe.checkout.Session.retrieve(session_id)
    except stripe.error.StripeError as e:
        raise PaymentError(f"No se pudo recuperar la sesión: {getattr(e, 'user_message', None) or e}")

    meta_uid = (session.get("metadata") or {}).get("user_id")
    if meta_uid != user["id"]:
        raise PaymentError("Esta sesión de pago no te pertenece")

    if session.get("payment_status") not in ("paid", "no_payment_required"):
        raise PaymentError("El pago aún no se ha completado")

    if session.get("status") != "complete":
        raise PaymentError(f"Sesión en estado inesperado: {session.get('status')}")

    updated = db.update_user_access(user["id"], is_premium=True)
    return db.public_user(updated)


# ── Simulador (fallback y modo demo) ───────────────────────────────────────

def simulate_payment(user: dict, outcome: str = "approved") -> dict:
    if outcome != "approved":
        raise PaymentError("Pago rechazado (simulado)")
    updated = db.update_user_access(user["id"], is_premium=True)
    return db.public_user(updated)


# ── Webhook (opcional, producción) ─────────────────────────────────────────

def handle_webhook(raw_body: bytes, signature_header: str | None) -> None:
    if not STRIPE_WEBHOOK_SECRET:
        return  # sin secreto, se ignora silenciosamente
    if not signature_header:
        raise PaymentError("Falta cabecera stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            raw_body, signature_header, STRIPE_WEBHOOK_SECRET
        )
    except (ValueError, stripe.error.SignatureVerificationError) as e:
        raise PaymentError(f"Webhook inválido: {e}")

    if event["type"] in (
        "checkout.session.completed",
        "customer.subscription.updated",
    ):
        sess = event["data"]["object"]
        uid = (sess.get("metadata") or {}).get("user_id")
        if uid and sess.get("payment_status") in ("paid", "no_payment_required"):
            try:
                db.update_user_access(uid, is_premium=True)
            except Exception:
                logger.exception("Error actualizando usuario desde webhook")