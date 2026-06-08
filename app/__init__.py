import re

import click
from flask import Flask
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.middleware.proxy_fix import ProxyFix

from config import Config

from .extensions import csrf, db, limiter, login_manager, mail
from .models import User


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    if app.config["SECRET_KEY"] == "dev-change-me" and app.config.get("ENV") != "development":
        raise RuntimeError("Defina SECRET_KEY com um valor aleatorio antes de iniciar a aplicacao.")

    proxy_fix_args = {
        "x_for": app.config.get("PROXY_FIX_X_FOR", 0),
        "x_proto": app.config.get("PROXY_FIX_X_PROTO", 0),
        "x_host": app.config.get("PROXY_FIX_X_HOST", 0),
    }
    if any(proxy_fix_args.values()):
        app.wsgi_app = ProxyFix(app.wsgi_app, **proxy_fix_args)

    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    limiter.init_app(app)
    csrf.init_app(app)

    login_manager.login_view = "auth.login"
    login_manager.login_message = "Entre com seu email e senha para acessar o sistema."
    login_manager.login_message_category = "info"

    @app.after_request
    def add_security_headers(response):
        if not app.config.get("SECURITY_HEADERS", True):
            return response
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "same-origin")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        if app.config.get("SESSION_COOKIE_SECURE"):
            response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        if app.config.get("CONTENT_SECURITY_POLICY"):
            response.headers.setdefault("Content-Security-Policy", app.config["CONTENT_SECURITY_POLICY"])
        return response

    @login_manager.user_loader
    def load_user(user_id):
        try:
            return db.session.get(User, int(user_id))
        except (TypeError, ValueError):
            return None

    from .auth.routes import auth_bp

    app.register_blueprint(auth_bp)

    @app.cli.command("init-db")
    def init_db():
        schema = app.config.get("POSTGRES_SCHEMA")
        database_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
        if database_uri.startswith("postgresql") and schema:
            if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", schema):
                raise ValueError("POSTGRES_SCHEMA deve conter apenas letras, números e underscore.")
            schema_exists = db.session.execute(
                text("SELECT to_regnamespace(:schema_name) IS NOT NULL"),
                {"schema_name": schema},
            ).scalar()
            if not schema_exists:
                try:
                    db.session.execute(text(f'CREATE SCHEMA "{schema}"'))
                    db.session.commit()
                except Exception as exc:
                    db.session.rollback()
                    raise click.ClickException(
                        f"Schema '{schema}' não existe e o usuário do banco não tem permissão para criá-lo. "
                        "Crie o schema manualmente com um usuário administrador ou conceda CREATE no banco."
                    ) from exc
        try:
            db.create_all()
        except SQLAlchemyError as exc:
            raise click.ClickException(
                f"Nao foi possivel criar as tabelas no schema '{schema or 'padrao'}'. "
                "Verifique se o usuário do banco tem USAGE e CREATE nesse schema."
            ) from exc
        print(f"Banco de dados inicializado no schema '{schema or 'padrão'}'.")

    @app.cli.command("show-db-config")
    def show_db_config():
        database_uri = app.config.get("SQLALCHEMY_DATABASE_URI")
        url = make_url(database_uri)
        print(f"DATABASE_URL carregada: {url.render_as_string(hide_password=True)}")
        print(f"POSTGRES_SCHEMA carregado: {app.config.get('POSTGRES_SCHEMA')}")

    return app
