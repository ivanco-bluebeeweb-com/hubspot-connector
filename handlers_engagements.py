"""Engagements (Activities) -- notes, calls, emails, meetings, tasks logged
against CRM records.

WHY THIS REUSES THE GENERIC OBJECT CRUD, NOT A SEPARATE ENDPOINT FAMILY.

HubSpot models each engagement type as an ordinary CRM object type under
`/crm/v3/objects/{type}` -- `notes`, `calls`, `emails`, `meetings`, `tasks`
(confirmed developers.hubspot.com/docs/api-reference/latest/crm/
activities/{calls,tasks,meetings}/guide, 2026-08-20). There is no
dedicated "engagements API" left in the current version -- it is the same
object CRUD surface handlers_crm.py already wraps. This module only adds
the engagement_type -> object_type mapping and the optional
"associate immediately on create" convenience.
"""
from __future__ import annotations

from imperal_sdk import ActionResult

import hubspot_client as hc
from app import chat
from schemas import CreateEngagementParams, GetEngagementParams, ListEngagementsParams, UpdateEngagementParams, CrmRecord, CrmRecordList
from handlers import _conn, _fail_to_result

_TYPE_MAP = {"note": "notes", "call": "calls", "email": "emails", "meeting": "meetings", "task": "tasks"}


def _obj_type(engagement_type: str) -> str:
    return _TYPE_MAP.get(engagement_type, engagement_type)


@chat.function(
    name="list_engagements",
    description="List logged activities of one type (note, call, email, meeting, task) across the whole portal.",
    data_model=CrmRecordList,
)
async def list_engagements(ctx, params: ListEngagementsParams) -> ActionResult:
    try:
        conn = await _conn(ctx, params.connection_id)
        data = await hc.list_objects(conn, _obj_type(params.engagement_type), params.limit, params.after, [])
    except hc.ClientFail as exc:
        return _fail_to_result(exc)
    results = data.get("results", [])
    return ActionResult.success({"items": results, "paging": data.get("paging", {})}, summary=f"{len(results)} {params.engagement_type}(s).")


@chat.function(
    name="get_engagement",
    description="Read one logged activity (note/call/email/meeting/task) in full.",
    data_model=CrmRecord,
)
async def get_engagement(ctx, params: GetEngagementParams) -> ActionResult:
    try:
        conn = await _conn(ctx, params.connection_id)
        data = await hc.get_object(conn, _obj_type(params.engagement_type), params.engagement_id, [], "")
    except hc.ClientFail as exc:
        return _fail_to_result(exc)
    return ActionResult.success(data, summary=f"{params.engagement_type} {params.engagement_id}.")


@chat.function(
    name="create_engagement",
    description="Log a new activity (note, call, email, meeting, or task) and optionally associate it with a CRM record right away, e.g. log a call on a contact.",
    action_type="write",
    data_model=CrmRecord,
    event="hubspot-connector.create_engagement",
    effects=["hubspot.engagement.created"],
)
async def create_engagement(ctx, params: CreateEngagementParams) -> ActionResult:
    """Create a note/call/email/meeting/task record and optionally associate it with a CRM record."""
    try:
        conn = await _conn(ctx, params.connection_id)
        object_type = _obj_type(params.engagement_type)
        data = await hc.create_object(conn, object_type, params.properties)
        engagement_id = data.get("id", "")
        if params.associate_object_type and params.associate_object_id and engagement_id:
            await hc.create_association(conn, object_type, engagement_id, params.associate_object_type, params.associate_object_id, [])
    except hc.ClientFail as exc:
        return _fail_to_result(exc)
    return ActionResult.success(data, summary=f"Logged a new {params.engagement_type}.")


@chat.function(
    name="update_engagement",
    description="Update the properties of an existing logged activity.",
    action_type="write",
    data_model=CrmRecord,
    event="hubspot-connector.update_engagement",
    effects=["hubspot.engagement.updated"],
)
async def update_engagement(ctx, params: UpdateEngagementParams) -> ActionResult:
    """Patch an existing note/call/email/meeting/task record's properties."""
    try:
        conn = await _conn(ctx, params.connection_id)
        data = await hc.update_object(conn, _obj_type(params.engagement_type), params.engagement_id, params.properties)
    except hc.ClientFail as exc:
        return _fail_to_result(exc)
    return ActionResult.success(data, summary=f"Updated {params.engagement_type} {params.engagement_id}.")
