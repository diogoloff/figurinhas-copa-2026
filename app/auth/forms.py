import re

from flask_wtf import FlaskForm
from wtforms import BooleanField, EmailField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError


PASSWORD_PATTERN = re.compile(r"^(?=.*[A-Za-z])(?=.*\d)(?=.*[^A-Za-z\d]).{8,}$")


def strong_password(form, field):
    if not PASSWORD_PATTERN.match(field.data or ""):
        raise ValidationError("Use no mínimo 8 caracteres, com letras, números e um caractere especial.")


class LoginForm(FlaskForm):
    email = EmailField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    password = PasswordField("Senha", validators=[DataRequired()])
    remember = BooleanField("Manter conectado")
    submit = SubmitField("Entrar")


class RegisterForm(FlaskForm):
    email = EmailField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    password = PasswordField("Senha", validators=[DataRequired(), strong_password])
    confirm_password = PasswordField(
        "Confirmar senha",
        validators=[DataRequired(), EqualTo("password", message="As senhas precisam ser iguais.")],
    )
    privacy_accept = BooleanField("Aceito o aviso de privacidade", validators=[DataRequired()])
    submit = SubmitField("Criar cadastro")


class ForgotPasswordForm(FlaskForm):
    email = EmailField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    submit = SubmitField("Enviar link")


class ResetPasswordForm(FlaskForm):
    password = PasswordField("Nova senha", validators=[DataRequired(), strong_password])
    confirm_password = PasswordField(
        "Confirmar nova senha",
        validators=[DataRequired(), EqualTo("password", message="As senhas precisam ser iguais.")],
    )
    submit = SubmitField("Redefinir senha")
