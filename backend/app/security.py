import hashlib
import hmac
import secrets
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from fastapi import HTTPException, Request
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError
from .config import settings


serializer = URLSafeTimedSerializer(settings.secret_key, salt="deathpit-session")


def password_matches(value: str, expected: str) -> bool:
    return hmac.compare_digest(value.encode(), expected.encode())


def credential_matches(value: str, plain: str, encoded: str) -> bool:
    if encoded:
        try:
            return PasswordHasher().verify(encoded, value)
        except VerificationError:
            return False
    return password_matches(value, plain)


def sign_session(owner_id: str, admin: bool = False) -> str:
    return serializer.dumps({"owner": owner_id, "admin": admin})


def read_session(request: Request, required: bool = True) -> dict:
    token = request.cookies.get("deathpit_session")
    if token:
        try:
            return serializer.loads(token, max_age=60 * 60 * 24 * 30)
        except (BadSignature, SignatureExpired):
            pass
    if required:
        raise HTTPException(401, "Arena login required")
    return {}


def require_admin(request: Request) -> dict:
    session = read_session(request)
    if not session.get("admin"):
        raise HTTPException(403, "Admin access required")
    return session


def new_token() -> str:
    return secrets.token_urlsafe(32)


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
