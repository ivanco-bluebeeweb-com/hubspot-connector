"""Panel UI -- connections list/connect form + a quick portal snapshot.

SIDEBAR CONTENT -- NO CARDS ANYWHERE, per ~/UI_INTERFACE_STANDARD.md's
"left sidebar, no decorated cards" rule (same convention as MuleSoft
Connector's / Power Automate Connector's / n8n Connector's panels.py).

Every section (connections, connect form, snapshot) is a plain ui.Stack,
content stacked vertically and left-aligned, sections separated by
ui.Divider() -- no Card border/background/shadow anywhere in this slot.
Disconnect lives only in the "App settings" screen (panels_settings.py).
The one secondary "App settings" button is always the LAST element at the
bottom of the sidebar.

WHY A SINGLE TOKEN FIELD, NOT A MULTI-FIELD FORM LIKE MULESOFT/POWER
AUTOMATE.

A HubSpot Private App access token is self-contained -- it already
encodes the portal and its granted scopes server-side (see app.py's
module docstring). Unlike MuleSoft's Connected App (client_id + secret +
org_id + environment_id) there is nothing else to ask for beyond the
token itself and an optional friendly label.
"""
from __future__ import annotations

from imperal_sdk import ui

import hubspot_client as hc
from app import ext
import handlers as h


def _settings_button() -> ui.UINode:
    """The one required secondary entry point into the settings screen --
    always the last element at the bottom of the sidebar."""
    return ui.Button(
        "App settings", variant="secondary", size="sm", full_width=True,
        icon="settings", on_click=ui.Call("__panel__hubspot_settings"),
    )


def _connection_row(c: dict) -> ui.UINode:
    label = c.get("label") or c.get("portal_id", "")
    return ui.Stack(direction="v", gap=1, children=[
        ui.Text(label, variant="body"),
        ui.Text(f"portal {c.get('portal_id', '')} · {c.get('hub_domain', '')}", variant="caption"),
    ])


def _connections_section(connections: list[dict]) -> ui.UINode:
    if not connections:
        return ui.Text("No HubSpot portals connected yet.", variant="caption")
    children: list[ui.UINode] = []
    for i, c in enumerate(connections):
        if i > 0:
            children.append(ui.Divider())
        children.append(_connection_row(c))
    return ui.Stack(direction="v", gap=2, children=children)


def _connect_section() -> ui.UINode:
    """Plain content, no Card wrapper. Stretched full-width per
    UI_INTERFACE_STANDARD.md (2026-08-20). No intro heading/description
    text here -- the Private App walkthrough lives ONLY in
    hubspot_connect_help's modal (button below opens it); repeating it
    here would duplicate that instruction."""
    return ui.Stack(direction="v", gap=3, align="stretch", children=[
        ui.Button("How do I set this up?", variant="ghost", size="sm",
                  icon="HelpCircle",
                  on_click=ui.Call("__panel__hubspot_connect_help")),
        ui.Form(
            action="connect_hubspot",
            submit_label="Verify and connect",
            children=[
                ui.Stack(direction="v", gap=1, children=[
                    ui.Text("Private App access token", variant="caption"),
                    ui.Password(param_name="access_token",
                                 placeholder="pat-na1-..."),
                ]),
                ui.Stack(direction="v", gap=1, children=[
                    ui.Text("Label (optional)", variant="caption"),
                    ui.Input(param_name="label", placeholder="e.g. Production portal"),
                ]),
            ],
        ),
    ])


def _snapshot_row(record: dict) -> ui.UINode:
    props = record.get("properties", {}) or {}
    title = props.get("dealname") or props.get("email") or props.get("name") or record.get("id", "")
    return ui.Stack(direction="v", gap=1, children=[
        ui.Text(str(title), variant="body"),
    ])


def _snapshot_section(records: list[dict]) -> ui.UINode:
    if not records:
        return ui.Text("No recent contacts to show.", variant="caption")
    children: list[ui.UINode] = []
    for i, r in enumerate(records):
        if i > 0:
            children.append(ui.Divider())
        children.append(_snapshot_row(r))
    return ui.Stack(direction="v", gap=2, children=children)


@ext.panel("hubspot_connect", slot="left", title="HubSpot", icon="🧡",
           default_width=320, min_width=260, max_width=420)
async def hubspot_connect_panel(ctx, **kwargs) -> object:
    connections = await h._load_connections(ctx)
    connected = bool(connections)

    header = ui.Header(text="HubSpot", level=2,
                        subtitle="Manage your HubSpot CRM and marketing data from Imperal")

    if not connected:
        return ui.Stack(direction="v", gap=4, align="stretch", children=[
            header,
            _connect_section(),
            ui.Divider(),
            _settings_button(),
        ])

    records: list = []
    first = connections[0]
    try:
        data = await hc.list_objects(first, "contacts", 5, "", ["email", "firstname", "lastname"])
        records = data.get("results", [])
    except hc.ClientFail:
        records = []

    return ui.Stack(direction="v", gap=4, align="stretch", children=[
        header,
        ui.Text("Connected portals", variant="subtitle"),
        _connections_section(connections),
        ui.Divider(),
        _connect_section(),
        ui.Divider(),
        ui.Text(f"Recent contacts -- {first.get('label') or first.get('portal_id', '')}", variant="subtitle"),
        _snapshot_section(records),
        ui.Divider(),
        _settings_button(),
    ])


@ext.panel("hubspot_connect_help", slot="center",
           title="How to connect HubSpot", center_overlay=True)
async def hubspot_connect_help(ctx, **kwargs) -> object:
    content = ui.Stack(direction="v", gap=3, children=[
        ui.Text("1. In your HubSpot portal, open Settings > Integrations > Private Apps."),
        ui.Text("2. Click \"Create a private app\", give it a name."),
        ui.Text("3. Under the Scopes tab, grant the CRM/marketing scopes you want to use (e.g. crm.objects.contacts.read/write)."),
        ui.Text("4. Click \"Create app\", confirm, then copy the Access token shown."),
        ui.Text("5. Paste that token below -- it never expires unless you regenerate or delete the app."),
        ui.Divider(),
        ui.Alert(
            title="CRM and marketing scope only",
            message=(
                "This manages contacts/companies/deals/tickets/products/line "
                "items, associations, properties, pipelines, owners, "
                "engagements, marketing lists/forms, files, custom objects "
                "and webhooks. Quotes, Workflows automation, CMS Hub (sites/"
                "pages/blogs) and the Conversations inbox are out of scope."
            ),
            type="warning",
        ),
        ui.Divider(),
        ui.Link(
            label="Open HubSpot's official Private Apps guide",
            href="https://developers.hubspot.com/docs/api/private-apps",
        ),
    ])
    return ui.Dialog(
        title="How to connect HubSpot",
        content=content,
        confirm_label="",
        cancel_label="Close",
    )


@ext.panel("hubspot_center", slot="center", title="HubSpot", icon="🧡", center_overlay=True)
async def hubspot_center_panel(ctx, **kwargs) -> object:
    """Base center panel -- per UI_INTERFACE_STANDARD.md (2026-08-20).
    This app has no list/detail content of its own to show in the center
    by default (everything lives in the sidebar). MUST carry
    center_overlay=True: per docs.imperal.io/en/concepts/panels, a plain
    slot="center" panel is registered but the Panel app never fetches it
    at session-init without that flag. Text is the shared canonical
    wording -- must stay identical across every app in this situation."""
    return ui.Empty(
        message="Nothing to show here -- this app is managed entirely from the sidebar.",
        icon="👈",
    )
