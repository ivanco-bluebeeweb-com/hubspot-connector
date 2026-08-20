"""HubSpot REST API HTTP client -- Private App Bearer token auth, thin
generic wrapper over `/crm/v3/objects/{objectType}/...` (CRM Objects API),
plus associations, properties, pipelines, owners (Part 1 of this module;
engagements/lists/forms/files/webhooks/account live in
hubspot_client_extra.py to keep each file small after a prior truncation
incident on this platform -- see POST_AUDIT_LOG.md).

WHY ONE GENERIC OBJECT-CRUD LAYER, NOT SIX SEPARATE ENDPOINT SETS.

HubSpot's own API is built this way: `contacts`, `companies`, `deals`,
`tickets`, `products`, `line_items` AND any custom object all resolve to
identical `/crm/v3/objects/{objectType}/{id}` shaped calls (confirmed
developers.hubspot.com/docs/api-reference/latest/crm/understanding-the-crm,
2026-08-20). `handlers_crm_named.py`'s named tools (list_contacts,
create_deal, ...) are thin, pinned wrappers around this one client layer.

WHY 401 vs 403 vs 429 ARE HANDLED DIFFERENTLY, SAME PRINCIPLE AS
MULESOFT/n8n/Make.com/Power Automate CONNECTOR's clients.

A 401 means the access token itself is not accepted (revoked, wrong
portal, malformed). A 403 means the token is valid but the Private App
was not granted the scope this endpoint needs (confirmed
developers.hubspot.com/docs/apps/developer-platform/build-apps/
authentication/scopes) -- the fix is "add the scope in your Private App
settings", not "reconnect". A 429 means the portal's own rate limit was
hit (`X-HubSpot-RateLimit-*` response headers, confirmed
developers.hubspot.com/docs/developer-tooling/platform/usage-guidelines)
-- transient, worth a distinct message so the user does not think their
data is broken.
"""
from __future__ import annotations

from typing import Any

import httpx

BASE_URL = "https://api.hubapi.com"
TIMEOUT = 30.0


class ClientFail(Exception):
    """Raised for any HubSpot API call that fails, with an HTTP-status-
    aware message so handlers can map it to a clear user-facing error."""

    def __init__(self, status: int, message: str):
        self.status = status
        self.message = message
        super().__init__(message)


def _headers(conn: dict) -> dict:
    return {
        "Authorization": f"Bearer {conn.get('access_token', '')}",
        "Content-Type": "application/json",
    }


async def _request(conn: dict, method: str, path: str, *, params: dict | None = None, json_body: dict | None = None) -> dict:
    url = f"{BASE_URL}{path}"
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.request(method, url, headers=_headers(conn), params=params, json=json_body)
    if resp.status_code == 401:
        raise ClientFail(401, "HubSpot rejected this access token -- it may have been revoked or regenerated in the portal. Reconnect with a fresh Private App token.")
    if resp.status_code == 403:
        raise ClientFail(403, "The connected Private App does not have the scope this action needs. Add the missing scope in HubSpot (Settings > Integrations > Private Apps > your app) and reconnect.")
    if resp.status_code == 404:
        raise ClientFail(404, "Not found -- the record, object type, or id does not exist in this portal.")
    if resp.status_code == 429:
        raise ClientFail(429, "HubSpot's API rate limit was hit for this portal. Wait a moment and try again.")
    if resp.status_code >= 400:
        detail = ""
        try:
            detail = resp.json().get("message", "")
        except Exception:
            detail = resp.text[:300]
        raise ClientFail(resp.status_code, f"HubSpot API error {resp.status_code}: {detail}")
    if resp.status_code == 204 or not resp.content:
        return {}
    return resp.json()


async def verify_token(conn: dict) -> dict:
    """Confirm the token works and identify the portal (hub_id, scopes)."""
    return await _request(conn, "GET", "/account-info/v3/details")


# ──────────────────────────────────────────────────────────────────────────
# Generic CRM object CRUD
# ──────────────────────────────────────────────────────────────────────────

async def list_objects(conn: dict, object_type: str, limit: int, after: str, properties: list[str]) -> dict:
    params: dict[str, Any] = {"limit": limit}
    if after:
        params["after"] = after
    if properties:
        params["properties"] = ",".join(properties)
    return await _request(conn, "GET", f"/crm/v3/objects/{object_type}", params=params)


async def get_object(conn: dict, object_type: str, object_id: str, properties: list[str], id_property: str) -> dict:
    params: dict[str, Any] = {}
    if properties:
        params["properties"] = ",".join(properties)
    if id_property:
        params["idProperty"] = id_property
    return await _request(conn, "GET", f"/crm/v3/objects/{object_type}/{object_id}", params=params)


async def create_object(conn: dict, object_type: str, properties: dict[str, Any]) -> dict:
    payload = {"properties": properties}
    return await _request(conn, "POST", f"/crm/v3/objects/{object_type}", json_body=payload)


async def update_object(conn: dict, object_type: str, object_id: str, properties: dict[str, Any]) -> dict:
    payload = {"properties": properties}
    return await _request(conn, "PATCH", f"/crm/v3/objects/{object_type}/{object_id}", json_body=payload)


async def archive_object(conn: dict, object_type: str, object_id: str) -> None:
    await _request(conn, "DELETE", f"/crm/v3/objects/{object_type}/{object_id}")


# ──────────────────────────────────────────────────────────────────────────
# Search (CRM Search API)
# ──────────────────────────────────────────────────────────────────────────

async def search_objects(
    conn: dict, object_type: str, filter_groups: list, sorts: list,
    query: str, properties: list[str], limit: int, after: str,
) -> dict:
    payload: dict[str, Any] = {"limit": limit}
    if filter_groups:
        payload["filterGroups"] = filter_groups
    if sorts:
        payload["sorts"] = sorts
    if query:
        payload["query"] = query
    if properties:
        payload["properties"] = properties
    if after:
        payload["after"] = after
    return await _request(conn, "POST", f"/crm/v3/objects/{object_type}/search", json_body=payload)


# ──────────────────────────────────────────────────────────────────────────
# Batch operations
# ──────────────────────────────────────────────────────────────────────────

async def batch_read_objects(conn: dict, object_type: str, ids: list[str], id_property: str, properties: list[str]) -> dict:
    payload: dict[str, Any] = {"inputs": [{"id": i} for i in ids]}
    if id_property:
        payload["idProperty"] = id_property
    if properties:
        payload["properties"] = properties
    return await _request(conn, "POST", f"/crm/v3/objects/{object_type}/batch/read", json_body=payload)


async def batch_create_objects(conn: dict, object_type: str, inputs: list[dict]) -> dict:
    payload = {"inputs": [{"properties": p} for p in inputs]}
    return await _request(conn, "POST", f"/crm/v3/objects/{object_type}/batch/create", json_body=payload)


async def batch_update_objects(conn: dict, object_type: str, updates: list[dict]) -> dict:
    payload = {"inputs": updates}
    return await _request(conn, "POST", f"/crm/v3/objects/{object_type}/batch/update", json_body=payload)


async def batch_archive_objects(conn: dict, object_type: str, ids: list[str]) -> None:
    payload = {"inputs": [{"id": i} for i in ids]}
    await _request(conn, "POST", f"/crm/v3/objects/{object_type}/batch/archive", json_body=payload)


# ──────────────────────────────────────────────────────────────────────────
# Associations (v4)
# ──────────────────────────────────────────────────────────────────────────

async def list_associations(conn: dict, from_type: str, from_id: str, to_type: str) -> dict:
    return await _request(conn, "GET", f"/crm/v4/objects/{from_type}/{from_id}/associations/{to_type}")


async def create_association(conn: dict, from_type: str, from_id: str, to_type: str, to_id: str, association_types: list[dict]) -> dict:
    payload = {"types": association_types} if association_types else {}
    return await _request(
        conn, "PUT",
        f"/crm/v4/objects/{from_type}/{from_id}/associations/{to_type}/{to_id}",
        json_body=payload,
    )


async def delete_association(conn: dict, from_type: str, from_id: str, to_type: str, to_id: str) -> None:
    await _request(conn, "DELETE", f"/crm/v4/objects/{from_type}/{from_id}/associations/{to_type}/{to_id}")


# ──────────────────────────────────────────────────────────────────────────
# Properties
# ──────────────────────────────────────────────────────────────────────────

async def list_properties(conn: dict, object_type: str) -> dict:
    return await _request(conn, "GET", f"/crm/v3/properties/{object_type}")


async def get_property(conn: dict, object_type: str, property_name: str) -> dict:
    return await _request(conn, "GET", f"/crm/v3/properties/{object_type}/{property_name}")


async def create_property(conn: dict, object_type: str, name: str, label: str, group_name: str, field_type: str, prop_type: str, options: list[dict]) -> dict:
    payload: dict[str, Any] = {
        "name": name, "label": label, "groupName": group_name,
        "fieldType": field_type, "type": prop_type,
    }
    if options:
        payload["options"] = options
    return await _request(conn, "POST", f"/crm/v3/properties/{object_type}", json_body=payload)


# ──────────────────────────────────────────────────────────────────────────
# Pipelines / stages
# ──────────────────────────────────────────────────────────────────────────

async def list_pipelines(conn: dict, object_type: str) -> dict:
    return await _request(conn, "GET", f"/crm/v3/pipelines/{object_type}")


async def get_pipeline(conn: dict, object_type: str, pipeline_id: str) -> dict:
    return await _request(conn, "GET", f"/crm/v3/pipelines/{object_type}/{pipeline_id}")


# ──────────────────────────────────────────────────────────────────────────
# Owners
# ──────────────────────────────────────────────────────────────────────────

async def list_owners(conn: dict, email: str, limit: int, after: str) -> dict:
    params: dict[str, Any] = {"limit": limit}
    if email:
        params["email"] = email
    if after:
        params["after"] = after
    return await _request(conn, "GET", "/crm/v3/owners", params=params)


async def get_owner(conn: dict, owner_id: str) -> dict:
    return await _request(conn, "GET", f"/crm/v3/owners/{owner_id}")
