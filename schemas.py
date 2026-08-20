"""Pydantic params models for HubSpot Connector.

All params models are module-scope (V17 federal invariant, same rule as
MuleSoft Connector / Power Automate Connector / n8n Connector's schemas.py).

WHY `object_type: str` (FREE TEXT), NOT AN ENUM, ON EVERY GENERIC CRM TOOL.

HubSpot's CRM Objects API is genuinely generic: `contacts`, `companies`,
`deals`, `tickets`, `products`, `line_items`, plus any CUSTOM OBJECT the
portal defines (e.g. `2-12345`) all share the exact same
`/crm/objects/{objectType}/...` shape (confirmed
developers.hubspot.com/docs/api-reference/latest/crm/understanding-the-crm,
2026-08-20). Hard-coding an enum of the 6 standard types would silently
break every custom-object portal -- a real, common HubSpot Enterprise
scenario. Free text with a clear description (and named convenience
wrappers like `list_contacts` for the common path) mirrors the same
"generic + convenience wrapper" shape MuleSoft Connector uses for its
CloudHub domain vs its bulk/audit convenience tools.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class NoParams(BaseModel):
    """Explicit empty params model -- V17 disallows untyped handlers."""
    pass


class ConnectionScoped(BaseModel):
    connection_id: str = Field(
        "",
        description="Which connected HubSpot portal to use (see list_connections). Omit if only one portal is connected.",
    )


# ──────────────────────────────────────────────────────────────────────────
# Connection
# ──────────────────────────────────────────────────────────────────────────


class ConnectHubspotParams(BaseModel):
    access_token: str = Field(
        "",
        description="Private App access token from your HubSpot portal (Settings > Integrations > Private Apps > your app > Access token).",
    )
    label: str = Field("", description="Optional friendly name for this portal connection.")


class DisconnectHubspotParams(ConnectionScoped):
    pass


# ──────────────────────────────────────────────────────────────────────────
# Generic CRM objects (contacts/companies/deals/tickets/products/line_items/
# custom objects all share this shape)
# ──────────────────────────────────────────────────────────────────────────


class ListObjectsParams(ConnectionScoped):
    object_type: str = Field(
        "contacts",
        description="CRM object type: contacts, companies, deals, tickets, products, line_items, or a custom object's fully-qualified name/id (e.g. '2-12345').",
    )
    limit: int = Field(20, ge=1, le=100, description="Max records to return (1-100).")
    after: str = Field("", description="Pagination cursor from a previous call's paging.next.after, if any.")
    properties: list[str] = Field(default_factory=list, description="Specific property names to include; empty returns the default set.")


class GetObjectParams(ConnectionScoped):
    object_type: str = Field("contacts", description="CRM object type, see list_objects.")
    object_id: str = Field(..., description="Record id, or a unique property value if id_property is set.")
    id_property: str = Field("", description="Optional: treat object_id as this unique property's value instead of the internal record id (e.g. 'email' for contacts).")
    properties: list[str] = Field(default_factory=list, description="Specific property names to include; empty returns the default set.")


class CreateObjectParams(ConnectionScoped):
    object_type: str = Field("contacts", description="CRM object type, see list_objects.")
    properties: dict[str, Any] = Field(..., description="Property name/value pairs for the new record, e.g. {'email': 'a@b.com', 'firstname': 'Ana'}.")


class UpdateObjectParams(ConnectionScoped):
    object_type: str = Field("contacts", description="CRM object type, see list_objects.")
    object_id: str = Field(..., description="Record id to update.")
    properties: dict[str, Any] = Field(..., description="Property name/value pairs to change; omitted properties are left untouched.")


class ArchiveObjectParams(ConnectionScoped):
    object_type: str = Field("contacts", description="CRM object type, see list_objects.")
    object_id: str = Field(..., description="Record id to archive (HubSpot's soft-delete; recoverable from the portal's recycling bin for 90 days).")


class BatchObjectIdsParams(ConnectionScoped):
    object_type: str = Field("contacts", description="CRM object type, see list_objects.")
    object_ids: list[str] = Field(..., min_length=1, max_length=100, description="Record ids, 1-100.")
    properties: list[str] = Field(default_factory=list, description="For batch read: specific property names to include.")


class BatchCreateParams(ConnectionScoped):
    object_type: str = Field("contacts", description="CRM object type, see list_objects.")
    records: list[dict[str, Any]] = Field(..., min_length=1, max_length=100, description="List of {'properties': {...}} objects, 1-100.")


class BatchUpdateParams(ConnectionScoped):
    object_type: str = Field("contacts", description="CRM object type, see list_objects.")
    records: list[dict[str, Any]] = Field(..., min_length=1, max_length=100, description="List of {'id': '...', 'properties': {...}} objects, 1-100.")


class SearchObjectsParams(ConnectionScoped):
    object_type: str = Field("contacts", description="CRM object type, see list_objects.")
    query: str = Field("", description="Free-text search query across default searchable properties.")
    filter_groups: list[dict[str, Any]] = Field(
        default_factory=list,
        description="HubSpot filterGroups structure for precise filtering, e.g. [{'filters': [{'propertyName': 'email', 'operator': 'CONTAINS_TOKEN', 'value': 'acme.com'}]}]. ORed across groups, ANDed within a group.",
    )
    sorts: list[dict[str, Any]] = Field(default_factory=list, description="Sort spec, e.g. [{'propertyName': 'createdate', 'direction': 'DESCENDING'}].")
    properties: list[str] = Field(default_factory=list, description="Specific property names to include in results.")
    limit: int = Field(20, ge=1, le=200, description="Max results (1-200).")
    after: str = Field("", description="Pagination cursor.")


# ──────────────────────────────────────────────────────────────────────────
# Associations (v4)
# ──────────────────────────────────────────────────────────────────────────


class ListAssociationsParams(ConnectionScoped):
    from_object_type: str = Field(..., description="Source object type, e.g. 'contacts'.")
    from_object_id: str = Field(..., description="Source record id.")
    to_object_type: str = Field(..., description="Target object type, e.g. 'companies'.")


class CreateAssociationParams(ConnectionScoped):
    from_object_type: str = Field(..., description="Source object type.")
    from_object_id: str = Field(..., description="Source record id.")
    to_object_type: str = Field(..., description="Target object type.")
    to_object_id: str = Field(..., description="Target record id.")
    association_type: str = Field(
        "",
        description="Optional specific association type label/id (e.g. 'contact_to_company'). Empty uses HubSpot's default association type for this object pair.",
    )


class DeleteAssociationParams(ConnectionScoped):
    from_object_type: str = Field(..., description="Source object type.")
    from_object_id: str = Field(..., description="Source record id.")
    to_object_type: str = Field(..., description="Target object type.")
    to_object_id: str = Field(..., description="Target record id.")


# ──────────────────────────────────────────────────────────────────────────
# Properties
# ──────────────────────────────────────────────────────────────────────────


class ListPropertiesParams(ConnectionScoped):
    object_type: str = Field("contacts", description="CRM object type, see list_objects.")


class GetPropertyParams(ConnectionScoped):
    object_type: str = Field("contacts", description="CRM object type, see list_objects.")
    property_name: str = Field(..., description="Internal property name.")


class CreatePropertyParams(ConnectionScoped):
    object_type: str = Field("contacts", description="CRM object type, see list_objects.")
    name: str = Field(..., description="Internal property name (lowercase, underscores).")
    label: str = Field(..., description="Human-readable label shown in the HubSpot UI.")
    group_name: str = Field(..., description="Property group this belongs to (see the object's property groups in HubSpot settings).")
    type: str = Field("string", description="Data type: string, number, date, datetime, enumeration, bool.")
    field_type: str = Field("text", description="UI field type: text, textarea, select, checkbox, radio, number, date, phonenumber, etc.")
    description: str = Field("", description="Optional help text shown in the UI.")
    options: list[dict[str, Any]] = Field(default_factory=list, description="For enumeration/select/checkbox/radio: list of {'label':..., 'value':...} choices.")


# ──────────────────────────────────────────────────────────────────────────
# Pipelines / Owners
# ──────────────────────────────────────────────────────────────────────────


class ListPipelinesParams(ConnectionScoped):
    object_type: str = Field("deals", description="'deals' or 'tickets' -- the two pipeline-enabled object types.")


class GetPipelineParams(ConnectionScoped):
    object_type: str = Field("deals", description="'deals' or 'tickets'.")
    pipeline_id: str = Field(..., description="Pipeline id from list_pipelines.")


class ListOwnersParams(ConnectionScoped):
    email: str = Field("", description="Optional: filter to the owner with this email.")
    limit: int = Field(100, ge=1, le=500, description="Max owners to return.")
    after: str = Field("", description="Pagination cursor from a previous list_owners response.")


class GetOwnerParams(ConnectionScoped):
    owner_id: str = Field(..., description="Owner id from list_owners.")


# ──────────────────────────────────────────────────────────────────────────
# Engagements (notes/calls/emails/meetings/tasks share the CRM objects shape
# under object types 'notes'/'calls'/'emails'/'meetings'/'tasks')
# ──────────────────────────────────────────────────────────────────────────


class CreateEngagementParams(ConnectionScoped):
    engagement_type: str = Field(..., description="One of: note, call, email, meeting, task.")
    properties: dict[str, Any] = Field(..., description="Engagement property values, e.g. {'hs_note_body': 'Called, left voicemail'} for a note, or {'hs_task_body': '...', 'hs_task_subject': '...', 'hs_timestamp': <ms epoch>} for a task.")
    associate_object_type: str = Field("", description="Optional: object type to associate this engagement with immediately, e.g. 'contacts'.")
    associate_object_id: str = Field("", description="Optional: record id to associate this engagement with immediately.")


class ListEngagementsParams(ConnectionScoped):
    engagement_type: str = Field(..., description="One of: note, call, email, meeting, task.")
    limit: int = Field(20, ge=1, le=100, description="Max records to return.")
    after: str = Field("", description="Pagination cursor.")


class GetEngagementParams(ConnectionScoped):
    engagement_type: str = Field(..., description="One of: note, call, email, meeting, task.")
    engagement_id: str = Field(..., description="Engagement record id.")


class UpdateEngagementParams(ConnectionScoped):
    engagement_type: str = Field(..., description="One of: note, call, email, meeting, task.")
    engagement_id: str = Field(..., description="Engagement record id.")
    properties: dict[str, Any] = Field(..., description="Property values to change.")


# ──────────────────────────────────────────────────────────────────────────
# Marketing: Lists / Forms / Files
# ──────────────────────────────────────────────────────────────────────────


class ListMarketingListsParams(ConnectionScoped):
    limit: int = Field(20, ge=1, le=100, description="Max lists to return.")
    after: str = Field("", description="Pagination cursor.")


class GetMarketingListParams(ConnectionScoped):
    list_id: str = Field(..., description="List id from list_marketing_lists.")


class ListMembershipParams(ConnectionScoped):
    list_id: str = Field(..., description="List id.")
    limit: int = Field(100, ge=1, le=250, description="Max member ids to return.")
    after: str = Field("", description="Pagination cursor.")


class ModifyListMembershipParams(ConnectionScoped):
    list_id: str = Field(..., description="List id (must be a static/ILS list, not an active/dynamic list).")
    contact_ids: list[str] = Field(..., min_length=1, max_length=100, description="Contact record ids to add or remove.")


class ListFormsParams(ConnectionScoped):
    limit: int = Field(20, ge=1, le=100, description="Max forms to return.")


class GetFormSubmissionsParams(ConnectionScoped):
    form_id: str = Field(..., description="Form id/guid from list_forms.")
    limit: int = Field(20, ge=1, le=50, description="Max submissions to return.")
    after: str = Field("", description="Pagination cursor.")


class ListFilesParams(ConnectionScoped):
    limit: int = Field(20, ge=1, le=100, description="Max files to return.")
    after: str = Field("", description="Pagination cursor.")


class UploadFileParams(ConnectionScoped):
    file_url: str = Field(..., description="Publicly reachable https:// URL of the file to fetch and upload into HubSpot's File Manager.")
    file_name: str = Field(..., description="Desired file name in HubSpot, including extension.")
    folder_path: str = Field("", description="Optional destination folder path in the File Manager; empty uses HubSpot's default folder.")
    access: str = Field("PUBLIC_INDEXABLE", description="File access setting: PUBLIC_INDEXABLE, PUBLIC_NOT_INDEXABLE, or PRIVATE.")


class GetFileParams(ConnectionScoped):
    file_id: str = Field(..., description="File id from list_files.")


# ──────────────────────────────────────────────────────────────────────────
# Custom Objects (schema-level, not instances -- instances use the generic
# object_type='<fully-qualified-name>' path above)
# ──────────────────────────────────────────────────────────────────────────


class ListCustomObjectSchemasParams(ConnectionScoped):
    pass


class GetCustomObjectSchemaParams(ConnectionScoped):
    object_type: str = Field(..., description="Custom object type id or fully-qualified name.")


class CreateCustomObjectSchemaParams(ConnectionScoped):
    name: str = Field(..., description="Internal name for the custom object type (lowercase, underscores).")
    labels: dict[str, str] = Field(..., description="Display labels, e.g. {'singular': 'Project', 'plural': 'Projects'}.")
    primary_display_property: str = Field(..., description="Internal name of the property shown as the record's title.")
    properties: list[dict[str, Any]] = Field(..., min_length=1, description="Initial property definitions, each like {'name':..., 'label':..., 'type':..., 'fieldType':...}.")
    associated_objects: list[str] = Field(default_factory=list, description="Standard object types this custom object may associate with, e.g. ['CONTACT', 'COMPANY'].")


# ──────────────────────────────────────────────────────────────────────────
# Webhooks (app-level subscriptions -- advanced flow, needs a Developer
# Account + App ID separate from the Private App token)
# ──────────────────────────────────────────────────────────────────────────


class ListWebhookSubscriptionsParams(ConnectionScoped):
    app_id: str = Field(..., description="HubSpot Developer App ID that owns the webhook target URL config.")
    developer_api_key: str = Field("", description="Optional: HubSpot developer API key if different from the portal's Private App token (webhooks endpoints are app-scoped, not portal-scoped).")


class CreateWebhookSubscriptionParams(ConnectionScoped):
    app_id: str = Field(..., description="HubSpot Developer App ID.")
    developer_api_key: str = Field("", description="Developer API key for this app, if different from the portal's Private App token.")
    subscription_type: str = Field(..., description="Event to subscribe to, e.g. 'contact.creation', 'deal.propertyChange'.")
    property_name: str = Field("", description="Required only for *.propertyChange subscription types -- which property to watch.")
    active: bool = Field(True, description="Whether the subscription is active immediately.")


class DeleteWebhookSubscriptionParams(ConnectionScoped):
    app_id: str = Field(..., description="HubSpot Developer App ID.")
    subscription_id: str = Field(..., description="Subscription id from list_webhook_subscriptions.")
    developer_api_key: str = Field("", description="Developer API key for this app, if different from the portal's Private App token.")


class SetWebhookTargetUrlParams(ConnectionScoped):
    app_id: str = Field(..., description="HubSpot Developer App ID.")
    target_url: str = Field(..., description="HTTPS URL HubSpot should POST events to.")
    max_concurrent_requests: int = Field(10, ge=1, le=100, description="Throttling limit HubSpot applies when delivering events to your endpoint.")
    developer_api_key: str = Field("", description="Developer API key for this app, if different from the portal's Private App token.")


# ──────────────────────────────────────────────────────────────────────────
# Account info
# ──────────────────────────────────────────────────────────────────────────


class AccountInfoParams(ConnectionScoped):
    pass


# ──────────────────────────────────────────────────────────────────────────
# Tier 3 value-add
# ──────────────────────────────────────────────────────────────────────────


class GetPipelineHealthParams(ConnectionScoped):
    object_type: str = Field("deals", description="'deals' or 'tickets'.")
    pipeline_id: str = Field("", description="Optional: restrict to one pipeline id; empty covers every pipeline.")
    stale_after_days: int = Field(14, ge=1, le=365, description="Flag records not modified in this many days as stale.")


class FindDuplicateContactsParams(ConnectionScoped):
    match_on: str = Field("email", description="Property to detect duplicates on: 'email' or 'domain' (company domain from the contact's associated company).")
    limit: int = Field(500, ge=1, le=1000, description="Max contacts to scan for duplicates.")


class BulkUpdateDealStageParams(ConnectionScoped):
    deal_ids: list[str] = Field(..., min_length=1, max_length=100, description="Deal record ids to move, 1-100.")
    new_stage_id: str = Field(..., description="Target dealstage id (from list_pipeline_stages).")


class SyncCheckParams(ConnectionScoped):
    pass
