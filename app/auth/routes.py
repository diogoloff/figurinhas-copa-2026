from datetime import timezone
from urllib.parse import urlsplit

from flask import Blueprint, abort, flash, jsonify, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.album_data import build_compact_list_data, build_dashboard_data, build_selection_data, find_selection_by_code
from app.extensions import db, limiter
from app.models import PasswordResetToken, User, UserSticker, as_utc, utcnow

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
    collected_codes = {
        sticker.code
        for sticker in UserSticker.query.filter_by(user_id=current_user.id, is_collected=True).all()
    }
    album = build_dashboard_data(collected_codes)
    return render_template("dashboard.html", album=album)


@auth_bp.get("/figurinhas/resumo")
@login_required
def compact_sticker_list():
    collected_codes = {
        sticker.code
        for sticker in UserSticker.query.filter_by(user_id=current_user.id, is_collected=True).all()
    }
    mode = "collected" if request.args.get("modo") == "adquiridas" else "pending"
    compact_list = build_compact_list_data(collected_codes, mode=mode, query=request.args.get("q", "").strip())
    return render_template("compact_sticker_list.html", compact_list=compact_list)


@auth_bp.post("/figurinhas/resumo/<sticker_code>/alternar")
@login_required
def toggle_sticker_from_list(sticker_code):
    group, selection = find_selection_by_code(sticker_code)
    if not selection:
        abort(404)

    sticker = UserSticker.query.filter_by(user_id=current_user.id, code=sticker_code).first()
    if sticker:
        sticker.is_collected = not sticker.is_collected
    else:
        sticker = UserSticker(user_id=current_user.id, code=sticker_code, is_collected=True)
        db.session.add(sticker)
    db.session.commit()

    redirect_args = {}
    if request.form.get("modo") == "adquiridas":
        redirect_args["modo"] = "adquiridas"
    if request.form.get("q"):
        redirect_args["q"] = request.form["q"]

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        collected_codes = {
            user_sticker.code
            for user_sticker in UserSticker.query.filter_by(user_id=current_user.id, is_collected=True).all()
        }
        mode = "collected" if request.form.get("modo") == "adquiridas" else "pending"
        compact_list = build_compact_list_data(collected_codes, mode=mode, query=request.form.get("q", "").strip())
        return jsonify(
            {
                "sticker": {
                    "code": sticker_code,
                    "collected": sticker.is_collected,
                },
                "compactList": {
                    "totalVisible": compact_list["total_visible"],
                    "showingCollected": compact_list["showing_collected"],
                    "emptyTitle": compact_list["empty_title"],
                },
            }
        )
    return redirect(url_for("auth.compact_sticker_list", **redirect_args))


@auth_bp.get("/figurinhas/<selection_sigla>")
@login_required
def sticker_selection(selection_sigla):
    collected_codes = {
        sticker.code
        for sticker in UserSticker.query.filter_by(user_id=current_user.id, is_collected=True).all()
    }
    pending_only = request.args.get("pendentes") == "1"
    selection = build_selection_data(selection_sigla, collected_codes, pending_only=pending_only)
    if not selection:
        abort(404)
    return render_template("sticker_selection.html", selection=selection)


@auth_bp.post("/figurinhas/<selection_sigla>/<sticker_code>/alternar")
@login_required
def toggle_sticker(selection_sigla, sticker_code):
    selection = build_selection_data(selection_sigla, set())
    selection_codes = {sticker["code"] for sticker in selection["stickers"]} if selection else set()
    if not selection or sticker_code not in selection_codes:
        abort(404)

    sticker = UserSticker.query.filter_by(user_id=current_user.id, code=sticker_code).first()
    if sticker:
        sticker.is_collected = not sticker.is_collected
    else:
        sticker = UserSticker(user_id=current_user.id, code=sticker_code, is_collected=True)
        db.session.add(sticker)
    db.session.commit()

    redirect_args = {"selection_sigla": selection["sigla"].lower()}
    if request.form.get("pendentes") == "1":
        redirect_args["pendentes"] = "1"

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        collected_codes = {
            user_sticker.code
            for user_sticker in UserSticker.query.filter_by(user_id=current_user.id, is_collected=True).all()
        }
        updated_selection = build_selection_data(
            selection["sigla"].lower(),
            collected_codes,
            pending_only=request.form.get("pendentes") == "1",
        )
        return jsonify(
            {
                "sticker": {
                    "code": sticker_code,
                    "collected": sticker.is_collected,
                    "state": "Marcada" if sticker.is_collected else "Pendente",
                },
                "selection": {
                    "completed": updated_selection["completed"],
                    "total": updated_selection["total"],
                    "percent": updated_selection["percent"],
                    "pending": updated_selection["pending"],
                    "pendingOnly": updated_selection["pending_only"],
                    "visibleStickers": len(updated_selection["stickers"]),
                },
            }
        )
    return redirect(url_for("auth.sticker_selection", **redirect_args))


@auth_bp.post("/logout")
@login_required
def logout():
    logout_user()
    flash("Você saiu do sistema.", "info")
    return redirect(url_for("auth.home"))
