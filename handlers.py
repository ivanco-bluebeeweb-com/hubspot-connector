"""Chat functions for HubSpot Connector: connection management (connect/
disconnect/list), plus shared helpers used by every other handlers_*.py
module (handlers_crm.py, handlers_engagements.py, handlers_marketing.py,
handlers_admin.py, handlers_value_add.py).

WHY ONE SECRET HOLDING A JSON ARRAY OF CONNECTIONS, SAME PRECEDENT AS
MULESOFT/POWER AUTOMATE/N8N/MAKE.COM CONNECTOR.

ctx.secrets has no "one secret per id" primitive, so every multi-account
connector on this platform stores its connections as a JSON array under
one named secret and resolves by id in Python.
"""
from __future__ import annotations

import json

from imperal_sdk import ActionResult

import hubspot_client as hc
from app import ext, chat
from schemas import (
    NoParams,
    ConnectHubspotParams,
    DisconnectHubspotParams,
)

_SECRET_NAME = "hubspot_connections"


# ──────────────────────────────────────────────────────────────────────────
# Connection storage helpers
# ──────────────────────────────────────────────────────────────────────────


async def _load_connections(ctx) -> list[dict]:
    raw = await ctx.secrets.get(_SECRET_NAME)
    if not raw:
        return []
    try:
        data = json.loads(raw)
    except (TypeError, ValueError):
        return []
    return data if isinstance(data, list) else []


async def _save_connections(ctx, connections: list[dict]) -> None:
    await ctx.secrets.set(_SECRET_NAME, json.dumps(connections))


async def _resolve_connection(ctx, connection_id: str = "") -> dict | None:
    connections = await _load_connections(ctx)
    if not connections:
        return None
    if connection_id:
        for c in connections:
            if c.get("id") == connection_id:
                return c
        return None
    return connections[0]


async def _conn(ctx, connection_id: str = "") -> dict:
    """Resolve a stored connection or raise a user-facing ClientFail --
    every CRM/engagement/marketing/admin handler calls this first."""
    c = await _resolve_connection(ctx, connection_id)
    if c is None:
        raise hc.ClientFail(
            "No HubSpot portal connected yet. Use connect_hubspot with a "
            "Private App access token from Settings > Integrations > "
            "Private Apps in your HubSpot portal."
        )
    return c


def _fail_to_result(exc: hc.ClientFail) -> ActionResult:
    return ActionResult.fail(str(exc))


def _connection_to_dict(c: dict) -> dict:
    return {
        "id": c.get("id", ""),
        "title": c.get("label") or c.get("portal_id", "") or "HubSpot portal",
        "connected": True,
        "portal_id": c.get("portal_id", ""),
        "hub_domain": c.get("hub_domain", ""),
    }


# ──────────────────────────────────────────────────────────────────────────
# Connection management
# ──────────────────────────────────────────────────────────────────────────


@chat.function(
    name="connect_hubspot",
    description=(
        "Connect a HubSpot portal by saving a Private App access token, after "
        "checking it actually works. Create the Private App in your HubSpot "
        "portal: Settings > Integrations > Private Apps > Create a private app, "
        "grant it the CRM/Marketing/Files scopes you plan to use, then copy its "
        "Access token here. Non-expiring; you rotate it yourself in HubSpot if "
        "needed."
    ),
    action_type="write",
    chain_callable=True,
)
async def connect_hubspot(ctx, params: ConnectHubspotParams) -> ActionResult:
    token = params.access_token.strip()
    if not token:
        return ActionResult.fail("access_token is required.")
    try:
        info = await hc.get_account_info(token)
    except hc.ClientFail as exc:
        return _fail_to_result(exc)

    connections = await _load_connections(ctx)
    conn_id = f"hs_{info.get('portalId', len(connections) + 1)}"
    record = {
        "id": conn_id,
        "access_token": token,
        "portal_id": str(info.get("portalId", "")),
        "hub_domain": info.get("uiDomain", ""),
        "label": params.label.strip(),
    }
    connections = [c for c in connections if c.get("id") != conn_id]
    connections.append(record)
    await _save_connections(ctx, connections)
    return ActionResult.success(
        _connection_to_dict(record),
        summary=f"Connected HubSpot portal {record['portal_id']} ({record['hub_domain'] or 'no domain'}).",
    )


@chat.function(
    name="disconnect_hubspot",
    description="Disconnect a connected HubSpot portal. This does not revoke the Private App token in HubSpot itself -- revoke/delete it there too if you no longer want it valid.",
    action_type="write",
)
async def disconnect_hubspot(ctx, params: DisconnectHubspotParams) -> ActionResult:
    connections = await _load_connections(ctx)
    if not connections:
        return ActionResult.fail("No HubSpot portal is connected.")
    target = params.connection_id or connections[0].get("id", "")
    remaining = [c for c in connections if c.get("id") != target]
    if len(remaining) == len(connections):
        return ActionResult.fail(f"No connection found with id '{target}'.")
    await _save_connections(ctx, remaining)
    return ActionResult.success({"id": target}, summary=f"Disconnected HubSpot portal {target}.")


@chat.function(
    name="list_connections",
    description="List the connected HubSpot portals -- portal id, domain, and label.",
)
async def list_connections(ctx, params: NoParams) -> ActionResult:
    connections = await _load_connections(ctx)
    items = [_connection_to_dict(c) for c in connections]
    return ActionResult.success({"items": items}, summary=f"{len(items)} connected HubSpot portal(s).")
