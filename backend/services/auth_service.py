"""Authentication for the nonprofit dashboard platform."""
from werkzeug.security import check_password_hash

from auth import create_token, resolve_role
from repositories.user_repo import UserRepo


def login(email, password):
    repo = UserRepo()
    user = repo.get_user_by_email(email)
    if not user:
        raise ValueError("Invalid email or password")
    if user.get("is_deleted"):
        raise ValueError("Account deactivated")
    if not user.get("password_hash"):
        raise ValueError("Invalid email or password")
    if not check_password_hash(user["password_hash"], password):
        raise ValueError("Invalid email or password")

    role = resolve_role(user)
    token = create_token(user["user_id"], role, user.get("nonprofit_id"))
    return {
        "userId": user["user_id"],
        "name": user["name"],
        "email": user["email"],
        "role": role,
        "nonprofitId": user.get("nonprofit_id"),
        "token": token,
    }
