"""JWT authentication helpers for protected nonprofit routes."""
import os
from datetime import datetime, timedelta, timezone
from functools import wraps

import jwt
from dotenv import load_dotenv
from flask import g, jsonify, request

load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET", "dev-jwt-secret-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 24

VALID_ROLES = ("platform_admin", "nonprofit_user")


def resolve_role(user):
    """Map stored user fields to the application role string."""
    if user.get("is_admin"):
        return "platform_admin"
    role = user.get("role", "nonprofit_user")
    return role if role in VALID_ROLES else "nonprofit_user"


def create_token(user_id, role, nonprofit_id=None):
    payload = {
        "sub": str(user_id),
        "role": role,
        "nonprofit_id": nonprofit_id,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRY_HOURS),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token):
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])


def get_auth_context():
    """Return the current request's auth context from Flask g."""
    return getattr(g, "auth", None)


def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        header = request.headers.get("Authorization", "")
        if not header.startswith("Bearer "):
            return jsonify({"error": "Authentication required"}), 401
        token = header[7:]
        try:
            payload = decode_token(token)
        except jwt.PyJWTError:
            return jsonify({"error": "Invalid or expired token"}), 401

        from repositories.user_repo import UserRepo
        user = UserRepo().get_user_by_id(int(payload["sub"]))
        if not user or user.get("is_deleted"):
            return jsonify({"error": "Authentication required"}), 401

        g.auth = {
            "user_id": user["user_id"],
            "role": resolve_role(user),
            "nonprofit_id": user.get("nonprofit_id"),
            "email": user["email"],
            "name": user["name"],
        }
        return f(*args, **kwargs)

    return decorated


def require_roles(*roles):
    def decorator(f):
        @wraps(f)
        @require_auth
        def decorated(*args, **kwargs):
            ctx = get_auth_context()
            if ctx["role"] not in roles and ctx["role"] != "platform_admin":
                return jsonify({"error": "Forbidden"}), 403
            return f(*args, **kwargs)

        return decorated

    return decorator
