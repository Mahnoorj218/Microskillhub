import base64
import json
import os
from functools import lru_cache

from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing environment variable: {name}")
    return value


def jwt_key_role(api_key: str) -> str | None:
    """Read Supabase JWT role claim (service_role vs anon)."""
    try:
        parts = api_key.split(".")
        if len(parts) < 2:
            return None
        payload = parts[1]
        padded = payload + "=" * (-len(payload) % 4)
        data = json.loads(base64.urlsafe_b64decode(padded))
        return data.get("role")
    except Exception:
        return None


def validate_service_role_key() -> None:
    key = _require_env("SUPABASE_SERVICE_ROLE_KEY")
    role = jwt_key_role(key)
    if role and role != "service_role":
        raise RuntimeError(
            f"SUPABASE_SERVICE_ROLE_KEY is '{role}' — must be service_role. "
            "Supabase Dashboard → Project Settings → API → copy service_role (secret), "
            "not the anon public key."
        )


@lru_cache
def get_supabase() -> Client:
    """Service-role client for trusted backend operations."""
    validate_service_role_key()
    return create_client(
        _require_env("SUPABASE_URL"),
        _require_env("SUPABASE_SERVICE_ROLE_KEY"),
    )
