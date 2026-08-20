"""The single 'App settings' screen (center slot) -- connection management
(disconnect per connected portal) for HubSpot Connector. Split out of
panels.py per the same convention as MuleSoft Connector's / Power
Automate Connector's / n8n Connector's panels_settings.py.

Per ~/UI_INTERFACE_STANDARD.md: the left sidebar never wraps the connect
form in a Card, and disconnect (never exposed in the sidebar itself) lives
here, one row per connected portal. The one secondary "App settings"
button sits LAST at the bottom of the sidebar.
"""
from __future__ import annotations

from imperal_sdk import ui

from app import ext
import handlers as h


def _connection_row(c: dict) -> ui.UINode:
    label = c.get("label") or c.get("portal_id", "")
    return ui.Stack(direction="v", gap=1, align="start", children=[
        ui.Text(label, variant="body"),
        ui.Text(f"portal {c.get('portal_id', '')} · {c.get('hub_domain', '')}", variant="caption"),
        ui.Button(
            "Disconnect", variant="danger", size="sm",
            on_click=ui.Call("disconnect_hubspot", {"connection_id": c.get("id")}),
        ),
    ])


def _connections_section(connections: list[dict]) -> ui.UINode:
    if not connections:
        return ui.Stack(direction="v", gap=1, children=[
            ui.Text("Connections", variant="heading"),
            ui.Text("No HubSpot portals connected yet.", variant="caption"),
        ])
    children: list[ui.UINode] = [ui.Text("Connections", variant="heading")]
    for i, c in enumerate(connections):
        if i > 0:
            children.append(ui.Divider())
        children.append(_connection_row(c))
    return ui.Stack(direction="v", gap=2, children=children)


@ext.panel("hubspot_settings", slot="center")
async def hubspot_settings_panel(ctx, **kwargs) -> object:
    connections = await h._load_connections(ctx)
    return ui.Stack(direction="v", gap=4, align="stretch", children=[
        ui.Header(text="HubSpot -- App settings", level=2),
        _connections_section(connections),
    ])
