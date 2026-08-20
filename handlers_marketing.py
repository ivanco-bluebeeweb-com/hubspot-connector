"""Marketing Lists, Forms, Files -- non-CRM-object HubSpot surfaces that
still matter for a full connector: static contact lists, form submission
data, and the File Manager.
"""
from __future__ import annotations

from imperal_sdk import ActionResult

import hubspot_client_extra as hce
from hubspot_client import ClientFail
from app import chat
from schemas import (
    GetFileParams, GetFormSubmissionsParams, GetMarketingListParams,
    ListFilesParams, ListFormsParams, ListMarketingListsParams,
    ListMembershipParams, ModifyListMembershipParams, UploadFileParams,
)
from handlers import _conn, _fail_to_result


# ── Marketing Lists ─────────────────────────────────────────────────────

@chat.function(name="list_marketing_lists", description="List static/active contact lists defined in the portal.")
async def list_marketing_lists(ctx, params: ListMarketingListsParams) -> ActionResult:
    try:
        conn = await _conn(ctx, params.connection_id)
        data = await hce.list_marketing_lists(conn, params.limit, params.after)
    except ClientFail as exc:
        return _fail_to_result(exc)
    results = data.get("lists", data.get("results", []))
    return ActionResult.success({"items": results}, summary=f"{len(results)} marketing list(s).")


@chat.function(name="get_marketing_list", description="Read one contact list's definition (name, size, static or dynamic).")
async def get_marketing_list(ctx, params: GetMarketingListParams) -> ActionResult:
    try:
        conn = await _conn(ctx, params.connection_id)
        data = await hce.get_marketing_list(conn, params.list_id)
    except ClientFail as exc:
        return _fail_to_result(exc)
    return ActionResult.success(data, summary=f"List {params.list_id}.")


@chat.function(name="list_list_membership", description="List the contact ids belonging to one static list.")
async def list_list_membership(ctx, params: ListMembershipParams) -> ActionResult:
    try:
        conn = await _conn(ctx, params.connection_id)
        data = await hce.list_membership(conn, params.list_id, params.limit, params.after)
    except ClientFail as exc:
        return _fail_to_result(exc)
    results = data.get("results", [])
    return ActionResult.success({"items": results, "paging": data.get("paging", {})}, summary=f"{len(results)} member(s) of list {params.list_id}.")


@chat.function(name="add_contacts_to_list", description="Add contacts to a static list by their record ids.", action_type="write")
async def add_contacts_to_list(ctx, params: ModifyListMembershipParams) -> ActionResult:
    try:
        conn = await _conn(ctx, params.connection_id)
        data = await hce.add_to_list(conn, params.list_id, params.contact_ids)
    except ClientFail as exc:
        return _fail_to_result(exc)
    return ActionResult.success(data, summary=f"Added {len(params.contact_ids)} contact(s) to list {params.list_id}.")


@chat.function(name="remove_contacts_from_list", description="Remove contacts from a static list by their record ids.", action_type="write")
async def remove_contacts_from_list(ctx, params: ModifyListMembershipParams) -> ActionResult:
    try:
        conn = await _conn(ctx, params.connection_id)
        data = await hce.remove_from_list(conn, params.list_id, params.contact_ids)
    except ClientFail as exc:
        return _fail_to_result(exc)
    return ActionResult.success(data, summary=f"Removed {len(params.contact_ids)} contact(s) from list {params.list_id}.")


# ── Forms ────────────────────────────────────────────────────────────────

@chat.function(name="list_forms", description="List marketing forms defined in the portal.")
async def list_forms(ctx, params: ListFormsParams) -> ActionResult:
    try:
        conn = await _conn(ctx, params.connection_id)
        data = await hce.list_forms(conn, params.limit)
    except ClientFail as exc:
        return _fail_to_result(exc)
    results = data.get("results", data if isinstance(data, list) else [])
    return ActionResult.success({"items": results}, summary=f"{len(results)} form(s).")


@chat.function(name="get_form_submissions", description="List submissions received on one form, most recent first.")
async def get_form_submissions(ctx, params: GetFormSubmissionsParams) -> ActionResult:
    try:
        conn = await _conn(ctx, params.connection_id)
        data = await hce.get_form_submissions(conn, params.form_id, params.limit, params.after)
    except ClientFail as exc:
        return _fail_to_result(exc)
    results = data.get("results", [])
    return ActionResult.success({"items": results, "paging": data.get("paging", {})}, summary=f"{len(results)} submission(s) for form {params.form_id}.")


# ── Files ────────────────────────────────────────────────────────────────

@chat.function(name="list_files", description="List files stored in the portal's File Manager.")
async def list_files(ctx, params: ListFilesParams) -> ActionResult:
    try:
        conn = await _conn(ctx, params.connection_id)
        data = await hce.list_files(conn, params.limit, params.after)
    except ClientFail as exc:
        return _fail_to_result(exc)
    results = data.get("results", [])
    return ActionResult.success({"items": results, "paging": data.get("paging", {})}, summary=f"{len(results)} file(s).")


@chat.function(name="upload_file", description="Upload a file into the File Manager by fetching it from a publicly reachable URL.", action_type="write")
async def upload_file(ctx, params: UploadFileParams) -> ActionResult:
    try:
        conn = await _conn(ctx, params.connection_id)
        data = await hce.upload_file_from_url(conn, params.file_url, params.file_name, params.folder_path, params.access)
    except ClientFail as exc:
        return _fail_to_result(exc)
    return ActionResult.success(data, summary=f"Uploaded {params.file_name}.")


@chat.function(name="get_file", description="Read one file's metadata (URL, size, type) from the File Manager.")
async def get_file(ctx, params: GetFileParams) -> ActionResult:
    try:
        conn = await _conn(ctx, params.connection_id)
        data = await hce.get_file(conn, params.file_id)
    except ClientFail as exc:
        return _fail_to_result(exc)
    return ActionResult.success(data, summary=f"File {params.file_id}.")
