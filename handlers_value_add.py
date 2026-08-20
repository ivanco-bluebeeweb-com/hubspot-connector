"""Tier 3 value-add -- aggregate/derived tools that go beyond a thin API
wrapper, same tier MuleSoft Connector's audit_cloudhub_environment and
Power Automate's bulk tools occupy. Built entirely on the generic CRM
primitives already wrapped above -- no new HubSpot endpoints.
"""
from __future__ import annotations

import time
from collections import defaultdict

from imperal_sdk import ActionResult

import hubspot_client as hc
from app import chat
from schemas import (
    BulkUpdateDealStageParams, FindDuplicateContactsParams,
    GetPipelineHealthParams, SyncCheckParams,
)
from handlers import _conn, _fail_to_result


@chat.function(
    name="get_pipeline_health",
    description="Audit one or all pipelines for an object type (deals or tickets): open record counts per stage, and how many are stale (not modified in stale_after_days).",
)
async def get_pipeline_health(ctx, params: GetPipelineHealthParams) -> ActionResult:
    stage_property = "dealstage" if params.object_type == "deals" else "hs_pipeline_stage"
    try:
        conn = await _conn(ctx, params.connection_id)
        pipelines_data = await hc.list_pipelines(conn, params.object_type)
        pipelines = pipelines_data.get("results", [])
        if params.pipeline_id:
            pipelines = [p for p in pipelines if p.get("id") == params.pipeline_id]

        now_ms = int(time.time() * 1000)
        stale_ms = params.stale_after_days * 86400 * 1000
        rows = []
        for pipeline in pipelines:
            for stage in pipeline.get("stages", []):
                filter_groups = [{"filters": [
                    {"propertyName": stage_property, "operator": "EQ", "value": stage.get("id")},
                ]}]
                search = await hc.search_objects(
                    conn, params.object_type, filter_groups, [], "",
                    ["hs_lastmodifieddate"], 100, "",
                )
                results = search.get("results", [])
                stale = 0
                for r in results:
                    modified = r.get("properties", {}).get("hs_lastmodifieddate")
                    if not modified:
                        continue
                    try:
                        modified_ms = int(modified) if str(modified).isdigit() else 0
                    except (TypeError, ValueError):
                        modified_ms = 0
                    if modified_ms and (now_ms - modified_ms) > stale_ms:
                        stale += 1
                rows.append({
                    "pipeline_id": pipeline.get("id"),
                    "pipeline_label": pipeline.get("label"),
                    "stage_id": stage.get("id"),
                    "stage_label": stage.get("label"),
                    "open_count": search.get("total", len(results)),
                    "stale_count": stale,
                })
    except hc.ClientFail as exc:
        return _fail_to_result(exc)
    return ActionResult.success(
        {"rows": rows},
        summary=f"Pipeline health for {len(pipelines)} {params.object_type} pipeline(s): {len(rows)} stage(s) audited.",
    )


@chat.function(
    name="find_duplicate_contacts",
    description="Scan the most recent contacts for likely duplicates grouped by email (or another property you choose).",
)
async def find_duplicate_contacts(ctx, params: FindDuplicateContactsParams) -> ActionResult:
    try:
        conn = await _conn(ctx, params.connection_id)
        data = await hc.list_objects(conn, "contacts", params.limit, "", ["email"])
    except hc.ClientFail as exc:
        return _fail_to_result(exc)
    groups: dict[str, list[str]] = defaultdict(list)
    for record in data.get("results", []):
        email = (record.get("properties", {}) or {}).get("email")
        if not email or "@" not in email:
            continue
        key = email.strip().lower() if params.match_on == "email" else email.strip().lower().split("@", 1)[1]
        groups[key].append(record.get("id"))
    dupes = [{"key": k, "count": len(v), "ids": v} for k, v in groups.items() if len(v) > 1]
    return ActionResult.success(
        {"duplicate_groups": dupes},
        summary=f"Found {len(dupes)} duplicate group(s) among {params.limit} scanned contact(s), matched on {params.match_on}.",
    )


@chat.function(
    name="bulk_update_deal_stage",
    description="Move up to 100 deals to a new pipeline stage in one call.",
    action_type="write",
)
async def bulk_update_deal_stage(ctx, params: BulkUpdateDealStageParams) -> ActionResult:
    try:
        conn = await _conn(ctx, params.connection_id)
        updates = [{"id": deal_id, "properties": {"dealstage": params.new_stage_id}} for deal_id in params.deal_ids]
        data = await hc.batch_update_objects(conn, "deals", updates)
    except hc.ClientFail as exc:
        return _fail_to_result(exc)
    results = data.get("results", [])
    return ActionResult.success(
        {"items": results},
        summary=f"Moved {len(results)} deal(s) to stage {params.new_stage_id}.",
    )


@chat.function(
    name="sync_check",
    description="Quick health check for this connection: verifies the token, and reports the portal id and granted scopes.",
)
async def sync_check(ctx, params: SyncCheckParams) -> ActionResult:
    try:
        conn = await _conn(ctx, params.connection_id)
        info = await hc.verify_token(conn)
    except hc.ClientFail as exc:
        return _fail_to_result(exc)
    return ActionResult.success(
        info,
        summary=f"Connection OK -- portal {info.get('portalId', info.get('hub_id', '?'))}.",
    )
