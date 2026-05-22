"""Supabase database helpers."""

from typing import Any, Dict, List, Optional

from supabase_client import get_supabase


def _client():
    return get_supabase()


def fetch_all(table: str, select: str = "*", **filters) -> List[Dict[str, Any]]:
    query = _client().table(table).select(select)
    for key, value in filters.items():
        query = query.eq(key, value)
    response = query.execute()
    return response.data or []


def fetch_one(table: str, select: str = "*", **filters) -> Optional[Dict[str, Any]]:
    rows = fetch_all(table, select, **filters)
    return rows[0] if rows else None


def insert_row(table: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    response = _client().table(table).insert(payload).execute()
    if not response.data:
        raise RuntimeError(f"Insert into {table} returned no data")
    return response.data[0]


def update_rows(table: str, payload: Dict[str, Any], **filters) -> None:
    query = _client().table(table).update(payload)
    for key, value in filters.items():
        query = query.eq(key, value)
    query.execute()


def delete_rows(table: str, **filters) -> None:
    query = _client().table(table).delete()
    for key, value in filters.items():
        query = query.eq(key, value)
    query.execute()


def rpc(function_name: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    response = _client().rpc(function_name, params or {}).execute()
    return response.data or []
