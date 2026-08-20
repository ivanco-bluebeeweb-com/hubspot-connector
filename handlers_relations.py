"""Associations, properties, pipelines/stages, owners, generic search and
batch operations -- the cross-cutting CRM primitives that sit alongside
object CRUD (handlers_crm.py / handlers_crm_named.py).

WHY ASSOCIATIONS ARE THEIR OWN DOMAIN, NOT PART OF OBJECT CRUD.

HubSpot v4 associations (confirmed developers.hubspot.com/docs/api-
reference/latest/crm/associations/overview, 2026-08-20) are a distinct
`/crm/v4/objects/{fromType}/{fromId}/associations/...` surface with their
own typed labels (e.g. "Primary Contact" on a deal) -- not a field on the
object itself. Modeling it as its own tools mirrors HubSpot's own API
shape.
"""
from __future__ import annotations

from imperal_sdk import ActionResult

import hubspot_client as hc
from app import chat
from schemas import (
    BatchCreateParams, BatchObjectIdsParams, BatchUpdateParams,
    CreateAssociationParams, CreatePropertyParams, DeleteAssociationParams,
    GetOwnerParams, GetPipelineParams, GetPropertyParams,
    ListAssociationsParams, ListOwnersParams, ListPipelinesParams,
    ListPropertiesParams, SearchObjectsParams,
)
from handlers import _conn, _fail_to_result


# ──────────────────────────────────────────────────────────────────────────
# Search
# ──────────────────────────────────────────────────────────────────────────

@chat.function(
    name="search_objects",
    description="Search CRM records of any object type with filters, sorting and free-text query -- the CRM Search API. Use this instead of list_objects when you need to filter (e.g. deals above a certain amount, contacts created after a date).",
)
async def search_objects(ctx, params: SearchObjectsParams) -> ActionResult:
    try:
        conn = await _conn(ctx, params.connection_id)
        data = await hc.search_objects(
            conn, params.object_type, params.filter_groups, params.sorts,
            params.query, params.properties, params.limit, params.after,
        )
    except hc.ClientFail as exc:
        return _fail_to_result(exc)
    results = data.get("results", [])
    return ActionResult.success(
        {"items": results, "total": data.get("total", len(results)), "paging": data.get("paging", {})},
        summary=f"{len(results)} of {data.get('total', len(results))} {params.object_type} matched.",
    )


# ──────────────────────────────────────────────────────────────────────────
# Batch operations
# ──────────────────────────────────────────────────────────────────────────

@chat.function(
    name="batch_read_objects",
    description="Read up to 100 CRM records of one object type by id (or by a unique property like email) in a single call.",
)
async def batch_read_objects(ctx, params: BatchObjectIdsParams) -> ActionResult:
    try:
        conn = await _conn(ctx, params.connection_id)
        data = await hc.batch_read_objects(conn, params.object_type, params.object_ids, params.id_property, params.properties)
    except hc.ClientFail as exc:
        return _fail_to_result(exc)
    results = data.get("results", [])
    return ActionResult.success({"items": results}, summary=f"Read {len(results)} {params.object_type} record(s).")


@chat.function(
    name="batch_create_objects",
    description="Create up to 100 CRM records of one object type in a single call.",
    action_type="write",
)
async def batch_create_objects(ctx, params: BatchCreateParams) -> ActionResult:
    try:
        conn = await _conn(ctx, params.connection_id)
        data = await hc.batch_create_objects(conn, params.object_type, params.records)
    except hc.ClientFail as exc:
        return _fail_to_result(exc)
    results = data.get("results", [])
    return ActionResult.success({"items": results}, summary=f"Created {len(results)} {params.object_type} record(s).")


@chat.function(
    name="batch_update_objects",
    description="Update up to 100 CRM records of one object type in a single call.",
    action_type="write",
)
async def batch_update_objects(ctx, params: BatchUpdateParams) -> ActionResult:
    try:
        conn = await _conn(ctx, params.connection_id)
        data = await hc.batch_update_objects(conn, params.object_type, params.records)
    except hc.ClientFail as exc:
        return _fail_to_result(exc)
    results = data.get("results", [])
    return ActionResult.success({"items": results}, summary=f"Updated {len(results)} {params.object_type} record(s).")


@chat.function(
    name="batch_archive_objects",
    description="Archive (soft-delete) up to 100 CRM records of one object type in a single call.",
    action_type="write",
)
async def batch_archive_objects(ctx, params: BatchObjectIdsParams) -> ActionResult:
    try:
        conn = await _conn(ctx, params.connection_id)
        await hc.batch_archive_objects(conn, params.object_type, params.object_ids)
    except hc.ClientFail as exc:
        return _fail_to_result(exc)
    return ActionResult.success({"ids": params.object_ids}, summary=f"Archived {len(params.object_ids)} {params.object_type} record(s).")


# ──────────────────────────────────────────────────────────────────────────
# Associations
# ──────────────────────────────────────────────────────────────────────────

@chat.function(
    name="list_associations",
    description="List the records associated with one CRM record (e.g. which contacts are linked to a deal).",
)
async def list_associations(ctx, params: ListAssociationsParams) -> ActionResult:
    try:
        conn = await _conn(ctx, params.connection_id)
        data = await hc.list_associations(conn, params.from_object_type, params.from_object_id, params.to_object_type)
    except hc.ClientFail as exc:
        return _fail_to_result(exc)
    results = data.get("results", [])
    return ActionResult.success({"items": results}, summary=f"{len(results)} associated {params.to_object_type} record(s).")


@chat.function(
    name="associate_objects",
    description="Link two CRM records together (e.g. attach a contact to a deal, or a line item to a deal). Use association_type='' for HubSpot's default label, or a specific typed association id if you have one.",
    action_type="write",
)
async def associate_objects(ctx, params: CreateAssociationParams) -> ActionResult:
    try:
        conn = await _conn(ctx, params.connection_id)
        assoc_types = [{"associationCategory": "USER_DEFINED", "associationTypeId": params.association_type}] if params.association_type else []
        data = await hc.create_association(
            conn, params.from_object_type, params.from_object_id,
            params.to_object_type, params.to_object_id, assoc_types,
        )
    except hc.ClientFail as exc:
        return _fail_to_result(exc)
    return ActionResult.success(data, summary=f"Associated {params.from_object_type} {params.from_object_id} with {params.to_object_type} {params.to_object_id}.")


@chat.function(
    name="remove_association",
    description="Remove the link between two CRM records without deleting either record.",
    action_type="write",
)
async def remove_association(ctx, params: DeleteAssociationParams) -> ActionResult:
    try:
        conn = await _conn(ctx, params.connection_id)
        await hc.delete_association(conn, params.from_object_type, params.from_object_id, params.to_object_type, params.to_object_id)
    except hc.ClientFail as exc:
        return _fail_to_result(exc)
    return ActionResult.success({}, summary=f"Removed association between {params.from_object_type} {params.from_object_id} and {params.to_object_type} {params.to_object_id}.")


# ──────────────────────────────────────────────────────────────────────────
# Properties (custom fields)
# ──────────────────────────────────────────────────────────────────────────

@chat.function(
    name="list_properties",
    description="List the properties (fields) defined on one CRM object type, including custom properties.",
)
async def list_properties(ctx, params: ListPropertiesParams) -> ActionResult:
    try:
        conn = await _conn(ctx, params.connection_id)
        data = await hc.list_properties(conn, params.object_type)
    except hc.ClientFail as exc:
        return _fail_to_result(exc)
    results = data.get("results", [])
    return ActionResult.success({"items": results}, summary=f"{len(results)} propert(y/ies) on {params.object_type}.")


@chat.function(
    name="get_property",
    description="Read one property's full definition (type, options if it's an enumeration, group).",
)
async def get_property(ctx, params: GetPropertyParams) -> ActionResult:
    try:
        conn = await _conn(ctx, params.connection_id)
        data = await hc.get_property(conn, params.object_type, params.property_name)
    except hc.ClientFail as exc:
        return _fail_to_result(exc)
    return ActionResult.success(data, summary=f"Property {params.property_name} on {params.object_type}.")


@chat.function(
    name="create_property",
    description="Create a new custom property (field) on a CRM object type.",
    action_type="write",
)
async def create_property(ctx, params: CreatePropertyParams) -> ActionResult:
    try:
        conn = await _conn(ctx, params.connection_id)
        data = await hc.create_property(
            conn, params.object_type, params.name, params.label, params.group_name,
            params.field_type, params.type, params.options,
        )
    except hc.ClientFail as exc:
        return _fail_to_result(exc)
    return ActionResult.success(data, summary=f"Created property {params.name} on {params.object_type}.")


# ──────────────────────────────────────────────────────────────────────────
# Pipelines & stages
# ──────────────────────────────────────────────────────────────────────────

@chat.function(
    name="list_pipelines",
    description="List the pipelines defined for an object type (e.g. deal pipelines, ticket pipelines), each with its stages.",
)
async def list_pipelines(ctx, params: ListPipelinesParams) -> ActionResult:
    try:
        conn = await _conn(ctx, params.connection_id)
        data = await hc.list_pipelines(conn, params.object_type)
    except hc.ClientFail as exc:
        return _fail_to_result(exc)
    results = data.get("results", [])
    return ActionResult.success({"items": results}, summary=f"{len(results)} pipeline(s) for {params.object_type}.")


@chat.function(
    name="get_pipeline",
    description="Read one pipeline in full, including its ordered stages.",
)
async def get_pipeline(ctx, params: GetPipelineParams) -> ActionResult:
    try:
        conn = await _conn(ctx, params.connection_id)
        data = await hc.get_pipeline(conn, params.object_type, params.pipeline_id)
    except hc.ClientFail as exc:
        return _fail_to_result(exc)
    return ActionResult.success(data, summary=f"Pipeline {params.pipeline_id} for {params.object_type}.")


# ──────────────────────────────────────────────────────────────────────────
# Owners
# ──────────────────────────────────────────────────────────────────────────

@chat.function(
    name="list_owners",
    description="List HubSpot owners (the users records can be assigned to) -- id, name, email.",
)
async def list_owners(ctx, params: ListOwnersParams) -> ActionResult:
    try:
        conn = await _conn(ctx, params.connection_id)
        data = await hc.list_owners(conn, params.email, params.limit, params.after)
    except hc.ClientFail as exc:
        return _fail_to_result(exc)
    results = data.get("results", [])
    return ActionResult.success({"items": results}, summary=f"{len(results)} owner(s).")


@chat.function(
    name="get_owner",
    description="Read one HubSpot owner in full by their owner id.",
)
async def get_owner(ctx, params: GetOwnerParams) -> ActionResult:
    try:
        conn = await _conn(ctx, params.connection_id)
        data = await hc.get_owner(conn, params.owner_id)
    except hc.ClientFail as exc:
        return _fail_to_result(exc)
    return ActionResult.success(data, summary=f"Owner {params.owner_id}.")
