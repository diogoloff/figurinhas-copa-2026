import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from flask import current_app
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db


def utcnow():
    return datetime.now(timezone.utc)


def as_utc(value):
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    failed_login_count = db.Column(db.Integer, nullable=False, default=0)
    lockout_until = db.Column(db.DateTime(timezone=True), nullable=True)
    privacy_accepted_at = db.Column(db.DateTime(timezone=True), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_locked(self):
        lockout_until = as_utc(self.lockout_until)
        return lockout_until is not None and lockout_until > utcnow()

    def register_failed_login(self):
        self.failed_login_count += 1
        if self.failed_login_count >= current_app.config["LOGIN_MAX_ATTEMPTS"]:
            self.lockout_until = utcnow() + timedelta(hours=current_app.config["LOGIN_LOCKOUT_HOURS"])

    def clear_login_failures(self):
        self.failed_login_count = 0
        self.lockout_until = None


class PasswordResetToken(db.Model):
    __tablename__ = "password_reset_tokens"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = db.Column(db.String(64), unique=True, nullable=False, index=True)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    used_at = db.Column(db.DateTime(timezone=True), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)

    user = db.relationship("User", backref=db.backref("reset_tokens", lazy=True, cascade="all, delete-orphan"))

    @staticmethod
    def hash_token(token):
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    @classmethod
    def issue_for_user(cls, user):
        raw_token = secrets.token_urlsafe(48)
        token = cls(
            user=user,
            token_hash=cls.hash_token(raw_token),
            expires_at=utcnow() + timedelta(seconds=current_app.config["RESET_TOKEN_MAX_AGE_SECONDS"]),
        )
        db.session.add(token)
        return raw_token, token

    @property
    def is_valid(self):
        expires_at = as_utc(self.expires_at)
        return self.used_at is None and expires_at is not None and expires_at > utcnow()


class UserSticker(db.Model):
    __tablename__ = "user_stickers"
    __table_args__ = (
        db.UniqueConstraint("user_id", "code", name="uq_user_stickers_user_code"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    code = db.Column(db.String(16), nullable=False, index=True)
    is_collected = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)

    user = db.relationship("User", backref=db.backref("stickers", lazy=True, cascade="all, delete-orphan"))
