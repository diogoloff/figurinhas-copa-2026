from flask import current_app, render_template, url_for
from flask_mail import Message

from app.extensions import mail


def send_password_reset_email(user, token):
    reset_url = url_for("auth.reset_password", token=token, _external=True)
    msg = Message(
        subject="Redefinição de senha - Controle de Figurinhas Copa 2026",
        recipients=[user.email],
    )
    msg.body = render_template("emails/reset_password.txt", reset_url=reset_url)
    msg.html = render_template("emails/reset_password.html", reset_url=reset_url)

    if current_app.config.get("MAIL_USERNAME") and current_app.config.get("MAIL_PASSWORD"):
        mail.send(msg)
    else:
        current_app.logger.warning("Link de redefinição para %s: %s", user.email, reset_url)
