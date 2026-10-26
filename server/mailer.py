import os
import logging

logger = logging.getLogger("reddit_teller.mailer")

# Variable expuesta para otros módulos (como payments.py)
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")

def send_verification_email(to_email: str, raw_token: str):
    resend_api_key = os.getenv("RESEND_API_KEY", "").strip()
    verify_url = f"{frontend_url}/?token={raw_token}"

    if not resend_api_key or "tu_clave" in resend_api_key:
        print("\n" + "=" * 60)
        print("✉  [MODO PRUEBA - CONSOLA]")
        print(f"Para: {to_email}")
        print(f"🔗 Enlace de verificación: {verify_url}")
        print("=" * 60 + "\n")
        return True

    try:
        import resend
        resend.api_key = resend_api_key
        email_from = os.getenv("EMAIL_FROM", "onboarding@resend.dev")

        resend.Emails.send({
            "from": email_from,
            "to": [to_email],
            "subject": "Confirma tu cuenta en Reddit Teller",
            "html": f"""
            <div style="font-family: sans-serif; background-color: #0E0D0F; color: #ECE7E1; padding: 30px; border-radius: 12px;">
                <h2 style="color: #E5484D;">¡Bienvenido a Reddit Teller! </h2>
                <p style="color: #8E8780;">Haz clic en el siguiente botón para activar tu cuenta:</p>
                <div style="margin: 24px 0;">
                    <a href="{verify_url}" style="background-color: #E5484D; color: white; padding: 12px 24px; font-weight: bold; text-decoration: none; border-radius: 8px; display: inline-block;">
                        Confirmar mi correo
                    </a>
                </div>
                <p style="font-size: 12px; color: #8E8780;">Este enlace vence en 1 hora.</p>
            </div>
            """
        })
        logger.info(f"Correo enviado exitosamente a {to_email}")
        return True
    except Exception as e:
        logger.error(f"Error enviando correo: {e}")
        return False