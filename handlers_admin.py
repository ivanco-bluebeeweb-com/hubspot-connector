"""Custom Object Schemas, Webhooks (app-level), Account Info -- portal
administration surfaces.
"""
from __future__ import annotations

from imperal_sdk import ActionResult

import hubspot_client_extra as hce
from hubspot_client import ClientFail
from app import chat
from schemas import (
    AccountInfoParams, CreateCustomObjectSchemaParams, CreateWebhookSubscriptionParams,
    DeleteWebhookSubscriptionParams, GetCustomObjectSchemaParams,
    ListCustomObjectSchemasParams, ListWebhookSubscriptionsParams,
    SetWebhookTargetUrlParams,
)
from handlers import _conn, _fail_to_result


# ── Custom Object Schemas ───────────────────────────────────────────────

@chat.function(name="list_custom_object_schemas", description="List custom object type definitions configured in this portal (Enterprise feature).")
async def list_custom_object_schemas(ctx, params: ListCustomObjectSchemasParams) -> ActionResult:
    try:
        conn = await _conn(ctx, params.connection_id)
        data = await hce.list_custom_object_schemas(conn)
    except ClientFail as exc:
        return _fail_to_result(exc)
    results = data.get("results", [])
    return ActionResult.success({"items": results}, summary=f"{len(results)} custom object schema(s).")


@chat.function(name="get_custom_object_schema", description="Read one custom object type's full schema -- its properties and association rules.")
async def get_custom_object_schema(ctx, params: GetCustomObjectSchemaParams) -> ActionResult:
    try:
        conn = await _conn(ctx, params.connection_id)
        data = await hce.get_custom_object_schema(conn, params.object_type)
    except ClientFail as exc:
        return _fail_to_result(exc)
    return ActionResult.success(data, summary=f"Custom object schema {params.object_type}.")


@chat.function(
    name="create_custom_object_schema",
    description="Define a brand-new custom object type in this portal (Enterprise feature). Once created, use the generic object tools with this type's fully-qualified name.",
    action_type="write",
)
async def create_custom_object_schema(ctx, params: CreateCustomObjectSchemaParams) -> ActionResult:
    try:
        conn = await _conn(ctx, params.connection_id)
        data = await hce.create_custom_object_schema(
            conn, params.name, params.labels, params.primary_display_property,
            params.properties, params.associated_objects,
        )
    except ClientFail as exc:
        return _fail_to_result(exc)
    return ActionResult.success(data, summary=f"Created custom object schema {params.name}.")


# ── Webhooks (app-level) ────────────────────────────────────────────────

@chat.function(
    name="list_webhook_subscriptions",
    description="List event subscriptions configured for a HubSpot Developer App. Needs app_id; pass developer_api_key if it differs from the connected Private App token.",
)
async def list_webhook_subscriptions(ctx, params: ListWebhookSubscriptionsParams) -> ActionResult:
    try:
        conn = await _conn(ctx, params.connection_id)
        data = await hce.list_webhook_subscriptions(conn, params.app_id, params.developer_api_key)
    except ClientFail as exc:
        return _fail_to_result(exc)
    results = data if isinstance(data, list) else data.get("results", [])
    return ActionResult.success({"items": results}, summary=f"{len(results)} webhook subscription(s) for app {params.app_id}.")


@chat.function(
    name="create_webhook_subscription",
    description="Subscribe a HubSpot Developer App to a CRM event (e.g. contact.creation, deal.propertyChange). Advanced flow -- requires a Developer App id, not just the portal's Private App token.",
    action_type="write",
)
async def create_webhook_subscription(ctx, params: CreateWebhookSubscriptionParams) -> ActionResult:
    try:
        conn = await _conn(ctx, params.connection_id)
        data = await hce.create_webhook_subscription(
            conn, params.app_id, params.developer_api_key, params.subscription_type,
            params.property_name, params.active,
        )
    except ClientFail as exc:
        return _fail_to_result(exc)
    return ActionResult.success(data, summary=f"Subscribed app {params.app_id} to {params.subscription_type}.")


@chat.function(name="delete_webhook_subscription", description="Remove a webhook event subscription from a Developer App.", action_type="write")
async def delete_webhook_subscription(ctx, params: DeleteWebhookSubscriptionParams) -> ActionResult:
    try:
        conn = await _conn(ctx, params.connection_id)
        await hce.delete_webhook_subscription(conn, params.app_id, params.subscription_id, params.developer_api_key)
    except ClientFail as exc:
        return _fail_to_result(exc)
    return ActionResult.success({"id": params.subscription_id}, summary=f"Deleted webhook subscription {params.subscription_id}.")


@chat.function(name="set_webhook_target_url", description="Set (or change) the HTTPS endpoint a Developer App's webhook events are delivered to.", action_type="write")
async def set_webhook_target_url(ctx, params: SetWebhookTargetUrlParams) -> ActionResult:
    try:
        conn = await _conn(ctx, params.connection_id)
        data = await hce.set_webhook_target_url(conn, params.app_id, params.target_url, params.max_concurrent_requests, params.developer_api_key)
    except ClientFail as exc:
        return _fail_to_result(exc)
    return ActionResult.success(data, summary=f"Set webhook target URL for app {params.app_id}.")


# ── Account info ─────────────────────────────────────────────────────────

@chat.function(name="get_account_info", description="Read this portal's account details -- hub id, time zone, currency, account type.")
async def get_account_info(ctx, params: AccountInfoParams) -> ActionResult:
    try:
        conn = await _conn(ctx, params.connection_id)
        data = await hce.get_account_info(conn)
    except ClientFail as exc:
        return _fail_to_result(exc)
    return ActionResult.success(data, summary="Account info.")
