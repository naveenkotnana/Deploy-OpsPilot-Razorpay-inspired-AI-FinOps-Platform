"""Local JWT auth + RBAC. No external identity provider, no hardcoded secrets
in code (JWT_SECRET comes from env; the dev default is clearly labelled)."""
import datetime as dt
import hashlib, hmac, os
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.base import get_db
from app.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)

ROLE_PERMISSIONS = {
    "ANALYST": {"view", "investigate"},
    "MANAGER": {"view", "investigate", "approve", "reject"},
    "ADMIN":   {"view", "investigate", "approve", "reject",
                "configure", "manage_users", "administer"},
}


# --- password hashing: PBKDF2-HMAC-SHA256, stdlib only (no bcrypt wheel needed)
def hash_password(password: str, salt: Optional[bytes] = None) -> str:
    salt = salt or os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 200_000)
    return f"pbkdf2_sha256$200000${salt.hex()}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, iters, salt_hex, hash_hex = stored.split("$")
        dk = hashlib.pbkdf2_hmac("sha256", password.encode(),
                                 bytes.fromhex(salt_hex), int(iters))
        return hmac.compare_digest(dk.hex(), hash_hex)
    except Exception:
        return False


def create_access_token(user: User) -> str:
    now = dt.datetime.now(dt.timezone.utc)
    payload = {"sub": user.user_id, "username": user.username, "role": user.role,
               "iat": now, "exp": now + dt.timedelta(minutes=settings.JWT_EXPIRE_MINUTES)}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALG)


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])


def get_current_user(token: str = Depends(oauth2_scheme),
                     db: Session = Depends(get_db)) -> User:
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing credentials")
    try:
        payload = decode_token(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")
    user = db.query(User).filter(User.user_id == payload.get("sub")).first()
    if not user or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Unknown or inactive user")
    return user


def require(*permissions: str):
    """Server-side permission enforcement. The dashboard's UI restrictions are
    cosmetic; this is the control."""
    def dep(user: User = Depends(get_current_user)) -> User:
        granted = ROLE_PERMISSIONS.get(user.role, set())
        missing = set(permissions) - granted
        if missing:
            raise HTTPException(status.HTTP_403_FORBIDDEN,
                                f"Role {user.role} lacks permission(s): {sorted(missing)}")
        return user
    return dep


DEMO_USERS = [
    ("USR-001", "analyst", "analyst123", "ANALYST"),
    ("USR-002", "manager", "manager123", "MANAGER"),
    ("USR-003", "admin",   "admin123",   "ADMIN"),
]


def seed_demo_users(db: Session) -> int:
    """Demo-only credentials for a local synthetic environment."""
    n = 0
    for uid, username, pw, role in DEMO_USERS:
        if not db.query(User).filter(User.username == username).first():
            db.add(User(user_id=uid, username=username,
                        password_hash=hash_password(pw), role=role, is_active=True))
            n += 1
    db.commit()
    return n
