"""Named convenience wrappers over handlers_crm.py's generic object CRUD,
one set per standard HubSpot object type -- contacts, companies, deals,
tickets, products, line_items. Each is a thin pin of object_type onto the
generic tool, same duality reasoning as handlers_crm.py's module docstring.
"""
from __future__ import annotations

from imperal_sdk import ActionResult

from app import chat
from schemas import ArchiveObjectParams, CreateObjectParams, GetObjectParams, ListObjectsParams, UpdateObjectParams, CrmRecord, CrmRecordList, DeleteResult
from handlers_crm import archive_object, create_object, get_object, list_objects, update_object


def _pin(params, object_type: str):
    params.object_type = object_type
    return params


# ── Contacts ─────────────────────────────────────────────────────────────

@chat.function(name="list_contacts", description="List contact records.", data_model=CrmRecordList)
async def list_contacts(ctx, params: ListObjectsParams) -> ActionResult:
    return await list_objects(ctx, _pin(params, "contacts"))


@chat.function(name="get_contact", description="Read one contact in full. Set id_property='email' to look up by email instead of internal id.", data_model=CrmRecord)
async def get_contact(ctx, params: GetObjectParams) -> ActionResult:
    return await get_object(ctx, _pin(params, "contacts"))


@chat.function(
    name="create_contact",
    description="Create a new contact record.",
    action_type="write",
    data_model=CrmRecord,
    event="hubspot-connector.create_contact",
    effects=["hubspot.crm_record.created"],
)
async def create_contact(ctx, params: CreateObjectParams) -> ActionResult:
    """Pin object_type="contacts" and delegate to the generic create_object tool."""
    return await create_object(ctx, _pin(params, "contacts"))


@chat.function(
    name="update_contact",
    description="Update an existing contact's properties.",
    action_type="write",
    data_model=CrmRecord,
    event="hubspot-connector.update_contact",
    effects=["hubspot.crm_record.updated"],
)
async def update_contact(ctx, params: UpdateObjectParams) -> ActionResult:
    """Pin object_type="contacts" and delegate to the generic update_object tool."""
    return await update_object(ctx, _pin(params, "contacts"))


@chat.function(
    name="archive_contact",
    description="Archive (soft-delete) a contact.",
    action_type="write",
    data_model=DeleteResult,
    event="hubspot-connector.archive_contact",
    effects=["hubspot.crm_record.archived"],
)
async def archive_contact(ctx, params: ArchiveObjectParams) -> ActionResult:
    """Pin object_type="contacts" and delegate to the generic archive_object tool."""
    return await archive_object(ctx, _pin(params, "contacts"))


# ── Companies ────────────────────────────────────────────────────────────

@chat.function(name="list_companies", description="List company records.", data_model=CrmRecordList)
async def list_companies(ctx, params: ListObjectsParams) -> ActionResult:
    return await list_objects(ctx, _pin(params, "companies"))


@chat.function(name="get_company", description="Read one company in full.", data_model=CrmRecord)
async def get_company(ctx, params: GetObjectParams) -> ActionResult:
    return await get_object(ctx, _pin(params, "companies"))


@chat.function(
    name="create_company",
    description="Create a new company record.",
    action_type="write",
    data_model=CrmRecord,
    event="hubspot-connector.create_company",
    effects=["hubspot.crm_record.created"],
)
async def create_company(ctx, params: CreateObjectParams) -> ActionResult:
    """Pin object_type="companies" and delegate to the generic create_object tool."""
    return await create_object(ctx, _pin(params, "companies"))


@chat.function(
    name="update_company",
    description="Update an existing company's properties.",
    action_type="write",
    data_model=CrmRecord,
    event="hubspot-connector.update_company",
    effects=["hubspot.crm_record.updated"],
)
async def update_company(ctx, params: UpdateObjectParams) -> ActionResult:
    """Pin object_type="companies" and delegate to the generic update_object tool."""
    return await update_object(ctx, _pin(params, "companies"))


@chat.function(
    name="archive_company",
    description="Archive (soft-delete) a company.",
    action_type="write",
    data_model=DeleteResult,
    event="hubspot-connector.archive_company",
    effects=["hubspot.crm_record.archived"],
)
async def archive_company(ctx, params: ArchiveObjectParams) -> ActionResult:
    """Pin object_type="companies" and delegate to the generic archive_object tool."""
    return await archive_object(ctx, _pin(params, "companies"))


# ── Deals ────────────────────────────────────────────────────────────────

@chat.function(name="list_deals", description="List deal records with their stage, amount, and pipeline.", data_model=CrmRecordList)
async def list_deals(ctx, params: ListObjectsParams) -> ActionResult:
    return await list_objects(ctx, _pin(params, "deals"))


@chat.function(name="get_deal", description="Read one deal in full -- stage, amount, close date, pipeline.", data_model=CrmRecord)
async def get_deal(ctx, params: GetObjectParams) -> ActionResult:
    return await get_object(ctx, _pin(params, "deals"))


@chat.function(
    name="create_deal",
    description="Create a new deal record.",
    action_type="write",
    data_model=CrmRecord,
    event="hubspot-connector.create_deal",
    effects=["hubspot.crm_record.created"],
)
async def create_deal(ctx, params: CreateObjectParams) -> ActionResult:
    """Pin object_type="deals" and delegate to the generic create_object tool."""
    return await create_object(ctx, _pin(params, "deals"))


@chat.function(
    name="update_deal",
    description="Update an existing deal's properties (e.g. move it to a new stage).",
    action_type="write",
    data_model=CrmRecord,
    event="hubspot-connector.update_deal",
    effects=["hubspot.crm_record.updated"],
)
async def update_deal(ctx, params: UpdateObjectParams) -> ActionResult:
    """Pin object_type="deals" and delegate to the generic update_object tool."""
    return await update_object(ctx, _pin(params, "deals"))


@chat.function(
    name="archive_deal",
    description="Archive (soft-delete) a deal.",
    action_type="write",
    data_model=DeleteResult,
    event="hubspot-connector.archive_deal",
    effects=["hubspot.crm_record.archived"],
)
async def archive_deal(ctx, params: ArchiveObjectParams) -> ActionResult:
    """Pin object_type="deals" and delegate to the generic archive_object tool."""
    return await archive_object(ctx, _pin(params, "deals"))


# ── Tickets ──────────────────────────────────────────────────────────────

@chat.function(name="list_tickets", description="List support ticket records.", data_model=CrmRecordList)
async def list_tickets(ctx, params: ListObjectsParams) -> ActionResult:
    return await list_objects(ctx, _pin(params, "tickets"))


@chat.function(name="get_ticket", description="Read one support ticket in full.", data_model=CrmRecord)
async def get_ticket(ctx, params: GetObjectParams) -> ActionResult:
    return await get_object(ctx, _pin(params, "tickets"))


@chat.function(
    name="create_ticket",
    description="Create a new support ticket.",
    action_type="write",
    data_model=CrmRecord,
    event="hubspot-connector.create_ticket",
    effects=["hubspot.crm_record.created"],
)
async def create_ticket(ctx, params: CreateObjectParams) -> ActionResult:
    """Pin object_type="tickets" and delegate to the generic create_object tool."""
    return await create_object(ctx, _pin(params, "tickets"))


@chat.function(
    name="update_ticket",
    description="Update an existing ticket's properties (e.g. status, priority).",
    action_type="write",
    data_model=CrmRecord,
    event="hubspot-connector.update_ticket",
    effects=["hubspot.crm_record.updated"],
)
async def update_ticket(ctx, params: UpdateObjectParams) -> ActionResult:
    """Pin object_type="tickets" and delegate to the generic update_object tool."""
    return await update_object(ctx, _pin(params, "tickets"))


@chat.function(
    name="archive_ticket",
    description="Archive (soft-delete) a support ticket.",
    action_type="write",
    data_model=DeleteResult,
    event="hubspot-connector.archive_ticket",
    effects=["hubspot.crm_record.archived"],
)
async def archive_ticket(ctx, params: ArchiveObjectParams) -> ActionResult:
    """Pin object_type="tickets" and delegate to the generic archive_object tool."""
    return await archive_object(ctx, _pin(params, "tickets"))


# ── Products ─────────────────────────────────────────────────────────────

@chat.function(name="list_products", description="List product catalog records.", data_model=CrmRecordList)
async def list_products(ctx, params: ListObjectsParams) -> ActionResult:
    return await list_objects(ctx, _pin(params, "products"))


@chat.function(name="get_product", description="Read one product catalog record in full.", data_model=CrmRecord)
async def get_product(ctx, params: GetObjectParams) -> ActionResult:
    return await get_object(ctx, _pin(params, "products"))


@chat.function(
    name="create_product",
    description="Create a new product catalog record.",
    action_type="write",
    data_model=CrmRecord,
    event="hubspot-connector.create_product",
    effects=["hubspot.crm_record.created"],
)
async def create_product(ctx, params: CreateObjectParams) -> ActionResult:
    """Pin object_type="products" and delegate to the generic create_object tool."""
    return await create_object(ctx, _pin(params, "products"))


@chat.function(
    name="update_product",
    description="Update an existing product's properties (name, price, description).",
    action_type="write",
    data_model=CrmRecord,
    event="hubspot-connector.update_product",
    effects=["hubspot.crm_record.updated"],
)
async def update_product(ctx, params: UpdateObjectParams) -> ActionResult:
    """Pin object_type="products" and delegate to the generic update_object tool."""
    return await update_object(ctx, _pin(params, "products"))


@chat.function(
    name="archive_product",
    description="Archive (soft-delete) a product catalog record.",
    action_type="write",
    data_model=DeleteResult,
    event="hubspot-connector.archive_product",
    effects=["hubspot.crm_record.archived"],
)
async def archive_product(ctx, params: ArchiveObjectParams) -> ActionResult:
    """Pin object_type="products" and delegate to the generic archive_object tool."""
    return await archive_object(ctx, _pin(params, "products"))


# ── Line items ───────────────────────────────────────────────────────────

@chat.function(name="list_line_items", description="List line-item records (individual products attached to a deal).", data_model=CrmRecordList)
async def list_line_items(ctx, params: ListObjectsParams) -> ActionResult:
    return await list_objects(ctx, _pin(params, "line_items"))


@chat.function(name="get_line_item", description="Read one line item in full.", data_model=CrmRecord)
async def get_line_item(ctx, params: GetObjectParams) -> ActionResult:
    return await get_object(ctx, _pin(params, "line_items"))


@chat.function(
    name="create_line_item",
    description="Create a new line item (attach it to a deal afterwards via associate_objects).",
    action_type="write",
    data_model=CrmRecord,
    event="hubspot-connector.create_line_item",
    effects=["hubspot.crm_record.created"],
)
async def create_line_item(ctx, params: CreateObjectParams) -> ActionResult:
    """Pin object_type="line_items" and delegate to the generic create_object tool."""
    return await create_object(ctx, _pin(params, "line_items"))


@chat.function(
    name="update_line_item",
    description="Update an existing line item's properties (quantity, price).",
    action_type="write",
    data_model=CrmRecord,
    event="hubspot-connector.update_line_item",
    effects=["hubspot.crm_record.updated"],
)
async def update_line_item(ctx, params: UpdateObjectParams) -> ActionResult:
    """Pin object_type="line_items" and delegate to the generic update_object tool."""
    return await update_object(ctx, _pin(params, "line_items"))


@chat.function(
    name="archive_line_item",
    description="Archive (soft-delete) a line item.",
    action_type="write",
    data_model=DeleteResult,
    event="hubspot-connector.archive_line_item",
    effects=["hubspot.crm_record.archived"],
)
async def archive_line_item(ctx, params: ArchiveObjectParams) -> ActionResult:
    """Pin object_type="line_items" and delegate to the generic archive_object tool."""
    return await archive_object(ctx, _pin(params, "line_items"))
