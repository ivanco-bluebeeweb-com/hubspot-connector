"""HubSpot REST client, Part 2 -- Marketing Lists, Forms, Files, Custom
Object Schemas, Webhooks (app-level), Account Info. Kept in a second file
from hubspot_client.py to keep each file small (see POST_AUDIT_LOG.md for
the truncation incident that motivated the split).

WHY WEBHOOKS NEED A SEPARATE developer_api_key, NOT THE PORTAL'S PRIVATE
APP TOKEN.

HubSpot's webhook subscription endpoints
(`/webhooks/v3/{appId}/subscriptions`) are scoped to a Developer App, not
a portal -- they require either the app's own developer API key or an
OAuth token issued for that app (confirmed developers.hubspot.com/docs/
api-reference/latest/webhooks/guide, 2026-08-20). A portal's Private App
access token cannot authenticate these calls. Each webhook tool therefore
accepts an optional developer_api_key and falls back to the portal token
only as a best-effort (will 401 if that app is not the source of the
Private App token) -- the tool descriptions say this plainly.
"""
from __future__ import annotations

from typing import Any

from hubspot_client import ClientFail, _request  # noqa: F401 (re-exported for handlers)


# ──────────────────────────────────────────────────────────────────────────
# Marketing Lists (Contact Lists)
# ──────────────────────────────────────────────────────────────────────────

async def list_marketing_lists(conn: dict, limit: int, after: str) -> dict:
    params: dict[str, Any] = {"limit": limit}
    if after:
        params["after"] = after
    return await _request(conn, "GET", "/crm/v3/lists", params=params)


async def get_marketing_list(conn: dict, list_id: str) -> dict:
    return await _request(conn, "GET", f"/crm/v3/lists/{list_id}")


async def list_membership(conn: dict, list_id: str, limit: int, after: str) -> dict:
    params: dict[str, Any] = {"limit": limit}
    if after:
        params["after"] = after
    return await _request(conn, "GET", f"/crm/v3/lists/{list_id}/memberships", params=params)


async def add_to_list(conn: dict, list_id: str, contact_ids: list[str]) -> dict:
    return await _request(conn, "PUT", f"/crm/v3/lists/{list_id}/memberships/add", json_body=contact_ids)


async def remove_from_list(conn: dict, list_id: str, contact_ids: list[str]) -> dict:
    return await _request(conn, "PUT", f"/crm/v3/lists/{list_id}/memberships/remove", json_body=contact_ids)


# ──────────────────────────────────────────────────────────────────────────
# Forms
# ──────────────────────────────────────────────────────────────────────────

async def list_forms(conn: dict, limit: int) -> dict:
    return await _request(conn, "GET", "/marketing/v3/forms", params={"limit": limit})


async def get_form_submissions(conn: dict, form_id: str, limit: int, after: str) -> dict:
    params: dict[str, Any] = {"limit": limit}
    if after:
        params["after"] = after
    return await _request(conn, "GET", f"/form-integrations/v1/submissions/forms/{form_id}", params=params)


# ──────────────────────────────────────────────────────────────────────────
# Files
# ──────────────────────────────────────────────────────────────────────────

async def list_files(conn: dict, limit: int, after: str) -> dict:
    params: dict[str, Any] = {"limit": limit}
    if after:
        params["after"] = after
    return await _request(conn, "GET", "/files/v3/files", params=params)


async def upload_file_from_url(conn: dict, file_url: str, file_name: str, folder_path: str, access: str) -> dict:
    payload: dict[str, Any] = {"fileUrl": file_url, "fileName": file_name, "options": {"access": access}}
    if folder_path:
        payload["folderPath"] = folder_path
    return await _request(conn, "POST", "/files/v3/files/import-from-url/async", json_body=payload)


async def get_file(conn: dict, file_id: str) -> dict:
    return await _request(conn, "GET", f"/files/v3/files/{file_id}")


# ──────────────────────────────────────────────────────────────────────────
# Custom Object Schemas
# ──────────────────────────────────────────────────────────────────────────

async def list_custom_object_schemas(conn: dict) -> dict:
    return await _request(conn, "GET", "/crm/v3/schemas")


async def get_custom_object_schema(conn: dict, object_type: str) -> dict:
    return await _request(conn, "GET", f"/crm/v3/schemas/{object_type}")


async def create_custom_object_schema(
    conn: dict, name: str, labels: dict[str, str], primary_display_property: str,
    properties: list[dict], associated_objects: list[str],
) -> dict:
    payload = {
        "name": name, "labels": labels, "primaryDisplayProperty": primary_display_property,
        "properties": properties, "associatedObjects": associated_objects,
    }
    return await _request(conn, "POST", "/crm/v3/schemas", json_body=payload)


# ──────────────────────────────────────────────────────────────────────────
# Webhooks (app-level -- see module docstring for the auth caveat)
# ──────────────────────────────────────────────────────────────────────────

def _webhook_conn(conn: dict, developer_api_key: str) -> dict:
    if not developer_api_key:
        return conn
    return {**conn, "access_token": developer_api_key}


async def list_webhook_subscriptions(conn: dict, app_id: str, developer_api_key: str) -> dict:
    return await _request(_webhook_conn(conn, developer_api_key), "GET", f"/webhooks/v3/{app_id}/subscriptions")


async def create_webhook_subscription(
    conn: dict, app_id: str, developer_api_key: str, subscription_type: str,
    property_name: str, active: bool,
) -> dict:
    payload: dict[str, Any] = {"eventType": subscription_type, "active": active}
    if property_name:
        payload["propertyName"] = property_name
    return await _request(_webhook_conn(conn, developer_api_key), "POST", f"/webhooks/v3/{app_id}/subscriptions", json_body=payload)


async def delete_webhook_subscription(conn: dict, app_id: str, subscription_id: str, developer_api_key: str) -> None:
    await _request(_webhook_conn(conn, developer_api_key), "DELETE", f"/webhooks/v3/{app_id}/subscriptions/{subscription_id}")


async def set_webhook_target_url(conn: dict, app_id: str, target_url: str, max_concurrent_requests: int, developer_api_key: str) -> dict:
    payload = {"targetUrl": target_url, "maxConcurrentRequests": max_concurrent_requests}
    return await _request(_webhook_conn(conn, developer_api_key), "PUT", f"/webhooks/v3/{app_id}/settings", json_body=payload)


# ──────────────────────────────────────────────────────────────────────────
# Account info
# ──────────────────────────────────────────────────────────────────────────

async def get_account_info(conn: dict) -> dict:
    return await _request(conn, "GET", "/account-info/v3/details")
