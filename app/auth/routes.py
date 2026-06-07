from datetime import timezone
from urllib.parse import urlsplit

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.extensions import db, limiter
from app.models import PasswordResetToken, User, as_utc, utcnow

from .email import send_password_reset_email
from .forms import ForgotPasswordForm, LoginForm, RegisterForm, ResetPasswordForm

auth_bp = Blueprint("auth", __name__)


def normalize_email(email):
    return (email or "").strip().lower()


def safe_redirect_target(target):
    if not target:
        return None
    parsed = urlsplit(target)
    if parsed.scheme or parsed.netloc:
        return None
    if not target.startswith("/"):
        return None
    return target


@auth_bp.get("/")
def home():
    if current_user.is_authenticated:
        return redirect(url_for("auth.dashboard"))
    return render_template("home.html")


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute; 40 per hour")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("auth.dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        email = normalize_email(form.email.data)
        user = User.query.filter_by(email=email).first()

        if user and user.is_locked:
            lockout = as_utc(user.lockout_until).astimezone(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")
            flash(f"Conta bloqueada por muitas tentativas. Tente novamente depois de {lockout}.", "danger")
            return render_template("auth/login.html", form=form)

        if user and user.check_password(form.password.data):
            user.clear_login_failures()
            db.session.commit()
            session.permanent = True
            login_user(user, remember=form.remember.data)
            next_url = safe_redirect_target(request.args.get("next"))
            return redirect(next_url or url_for("auth.dashboard"))

        if user:
            user.register_failed_login()
            db.session.commit()
        flash("Email ou senha inválidos.", "danger")

    return render_template("auth/login.html", form=form)


@auth_bp.route("/cadastro", methods=["GET", "POST"])
@limiter.limit("5 per minute; 20 per hour")
def register():
    if current_user.is_authenticated:
        return redirect(url_for("auth.dashboard"))

    form = RegisterForm()
    if form.validate_on_submit():
        email = normalize_email(form.email.data)
        if User.query.filter_by(email=email).first():
            flash("Já existe um cadastro com este email.", "danger")
            return render_template("auth/register.html", form=form)

        user = User(email=email, privacy_accepted_at=utcnow())
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash("Cadastro criado com sucesso.", "success")
        return redirect(url_for("auth.dashboard"))

    return render_template("auth/register.html", form=form)


@auth_bp.route("/recuperar-senha", methods=["GET", "POST"])
@limiter.limit("3 per minute; 10 per hour")
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for("auth.dashboard"))

    form = ForgotPasswordForm()
    if form.validate_on_submit():
        email = normalize_email(form.email.data)
        user = User.query.filter_by(email=email).first()
        if user:
            raw_token, _ = PasswordResetToken.issue_for_user(user)
            db.session.commit()
            send_password_reset_email(user, raw_token)
        flash("Se este email estiver cadastrado, enviaremos um link de redefinição válido por 1 hora.", "info")
        return redirect(url_for("auth.login"))

    return render_template("auth/forgot_password.html", form=form)


@auth_bp.route("/redefinir-senha/<token>", methods=["GET", "POST"])
@limiter.limit("6 per minute; 20 per hour")
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for("auth.dashboard"))

    token_hash = PasswordResetToken.hash_token(token)
    reset_token = PasswordResetToken.query.filter_by(token_hash=token_hash).first()
    if not reset_token or not reset_token.is_valid:
        flash("Link inválido ou expirado. Solicite uma nova redefinição de senha.", "danger")
        return redirect(url_for("auth.forgot_password"))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        reset_token.user.set_password(form.password.data)
        reset_token.user.clear_login_failures()
        reset_token.used_at = utcnow()
        db.session.commit()
        flash("Senha redefinida com sucesso. Entre com sua nova senha.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/reset_password.html", form=form)


@auth_bp.get("/painel")
@login_required
def dashboard():
    return render_template("dashboard.html")


@auth_bp.post("/logout")
@login_required
def logout():
    logout_user()
    flash("Você saiu do sistema.", "info")
    return redirect(url_for("auth.home"))
