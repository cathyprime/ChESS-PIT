import hashlib
import hmac
import secrets
import threading
import time
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from fastapi import HTTPException, Request
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError
from .config import settings


serializer = URLSafeTimedSerializer(settings.secret_key, salt="chesspit-session")
_attempt_lock = threading.Lock()
_attempts: dict[tuple[str, str], list[float]] = {}


def session_cookie_name() -> str:
    return "__Host-chesspit_session" if settings.secure_cookies else "chesspit_session"


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
    return serializer.dumps({"owner": owner_id,
                             "admin_until": time.time() + 1800 if admin else 0})


def read_session(request: Request, required: bool = True) -> dict:
    token = request.cookies.get(session_cookie_name())
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
    if float(session.get("admin_until", 0)) < time.time():
        raise HTTPException(403, "Admin access required")
    return session


def is_admin(session: dict) -> bool:
    return float(session.get("admin_until", 0)) >= time.time()


def client_address(request: Request) -> str:
    peer = request.client.host if request.client else "unknown"
    if peer in settings.trusted_proxies:
        forwarded = request.headers.get("x-forwarded-for", "").split(",", 1)[0].strip()
        if forwarded:
            return forwarded
    return peer


def check_attempt_limit(request: Request, bucket: str, limit: int = 5, window: int = 900) -> None:
    key, current = (bucket, client_address(request)), time.monotonic()
    with _attempt_lock:
        recent = [stamp for stamp in _attempts.get(key, []) if current - stamp < window]
        _attempts[key] = recent
        if len(recent) >= limit:
            retry = max(1, int(window - (current - recent[0])))
            raise HTTPException(429, "Too many attempts", headers={"Retry-After": str(retry)})


def record_failed_attempt(request: Request, bucket: str) -> None:
    with _attempt_lock:
        _attempts.setdefault((bucket, client_address(request)), []).append(time.monotonic())


def new_token() -> str:
    return secrets.token_urlsafe(32)


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
