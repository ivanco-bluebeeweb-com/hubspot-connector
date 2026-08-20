"""CRM object handlers -- generic CRUD over any HubSpot object type
(contacts, companies, deals, tickets, products, line_items, custom
objects), plus named convenience wrappers for the six standard types.

WHY NAMED WRAPPERS (list_contacts, create_deal, ...) INSTEAD OF ONLY THE
GENERIC list_objects/create_object.

Both exist on purpose. The generic tools cover custom objects and any
object type HubSpot adds later without a code change. The named wrappers
exist because that is how a user actually talks about their CRM ("create
a deal", not "create an object of type deals") -- same duality MuleSoft
Connector keeps between its generic bulk tools and named
start_cloudhub_application-style tools.
"""
from __future__ import annotations

from imperal_sdk import ActionResult

import hubspot_client as hc
from app import chat
from schemas import (
    ArchiveObjectParams, CreateObjectParams, GetObjectParams,
    ListObjectsParams, UpdateObjectParams, CrmRecord, CrmRecordList,
    DeleteResult,
)
from handlers import _conn, _fail_to_result


# ──────────────────────────────────────────────────────────────────────────
# Generic CRM objects
# ──────────────────────────────────────────────────────────────────────────


@chat.function(
    name="list_objects",
    description="List CRM records of any object type (contacts, companies, deals, tickets, products, line_items, or a custom object). Use list_contacts/list_companies/... for the standard types; use this for custom objects.",
    data_model=CrmRecordList,
)
async def list_objects(ctx, params: ListObjectsParams) -> ActionResult:
    try:
        conn = await _conn(ctx, params.connection_id)
        data = await hc.list_objects(conn, params.object_type, params.limit, params.after, params.properties)
    except hc.ClientFail as exc:
        return _fail_to_result(exc)
    results = data.get("results", [])
    return ActionResult.success(
        {"items": results, "paging": data.get("paging", {})},
        summary=f"{len(results)} {params.object_type} record(s).",
    )


@chat.function(
    name="get_object",
    description="Read one CRM record of any object type in full.",
    data_model=CrmRecord,
)
async def get_object(ctx, params: GetObjectParams) -> ActionResult:
    try:
        conn = await _conn(ctx, params.connection_id)
        data = await hc.get_object(conn, params.object_type, params.object_id, params.properties, params.id_property)
    except hc.ClientFail as exc:
        return _fail_to_result(exc)
    return ActionResult.success(data, summary=f"{params.object_type} record {params.object_id}.")


@chat.function(
    name="create_object",
    description="Create a new CRM record of any object type.",
    action_type="write",
    data_model=CrmRecord,
    event="hubspot-connector.create_object",
    effects=["hubspot.crm_record.created"],
)
async def create_object(ctx, params: CreateObjectParams) -> ActionResult:
    """Create a new CRM record via the generic /crm/v3/objects/{objectType} endpoint."""
    try:
        conn = await _conn(ctx, params.connection_id)
        data = await hc.create_object(conn, params.object_type, params.properties)
    except hc.ClientFail as exc:
        return _fail_to_result(exc)
    return ActionResult.success(data, summary=f"Created {params.object_type} record {data.get('id', '')}.")


@chat.function(
    name="update_object",
    description="Update an existing CRM record's properties (any object type). Omitted properties are left untouched.",
    action_type="write",
    data_model=CrmRecord,
    event="hubspot-connector.update_object",
    effects=["hubspot.crm_record.updated"],
)
async def update_object(ctx, params: UpdateObjectParams) -> ActionResult:
    """Patch a CRM record's properties via the generic /crm/v3/objects/{objectType}/{id} endpoint."""
    try:
        conn = await _conn(ctx, params.connection_id)
        data = await hc.update_object(conn, params.object_type, params.object_id, params.properties)
    except hc.ClientFail as exc:
        return _fail_to_result(exc)
    return ActionResult.success(data, summary=f"Updated {params.object_type} record {params.object_id}.")


@chat.function(
    name="archive_object",
    description="Archive (soft-delete) a CRM record of any object type. Recoverable from the portal's recycling bin for 90 days.",
    action_type="write",
    data_model=DeleteResult,
    event="hubspot-connector.archive_object",
    effects=["hubspot.crm_record.archived"],
)
async def archive_object(ctx, params: ArchiveObjectParams) -> ActionResult:
    """Archive a CRM record via the generic /crm/v3/objects/{objectType}/{id} DELETE endpoint (soft-delete)."""
    try:
        conn = await _conn(ctx, params.connection_id)
        await hc.archive_object(conn, params.object_type, params.object_id)
    except hc.ClientFail as exc:
        return _fail_to_result(exc)
    return ActionResult.success({"id": params.object_id}, summary=f"Archived {params.object_type} record {params.object_id}.")
