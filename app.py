"""Extension declaration, secrets, lifecycle hooks.

WHY BYOK (bring-your-own-key), same reasoning as MuleSoft Connector /
Power Automate Connector / Make.com Connector / n8n Connector. The user's
HubSpot data (contacts, deals, tickets) lives inside THEIR OWN HubSpot
portal -- Imperal cannot and should not broker access to someone else's
CRM data centrally.

WHY PRIVATE APP ACCESS TOKEN, NOT PUBLIC OAUTH (see CONNECTOR_DISCOVERY.md
and PREPARATION.md §2 for the full reasoning, confirmed against
developers.hubspot.com 2026-08-20).

A HubSpot Private App is created directly inside the user's own portal
(Settings > Integrations > Private Apps) -- the owner picks exactly which
scopes to grant and gets a non-expiring access token immediately. No
chicken-and-egg (unlike Zapier, which needs external marketplace review
before any real API access exists). Public App OAuth (authorization code
+ refresh token, requiring a HubSpot Developer Account + App ID) is only
needed to distribute one app across MANY portals centrally via HubSpot's
own App Marketplace -- not needed for a BYOK connector where each user
connects their own portal directly.

WHY `write_mode="both"`, SAME REASONING AS n8n/Make.com/Power Automate/
MuleSoft CONNECTOR.

Declaring `write_mode="user"` would mean only the platform's generic
Secrets screen could write this -- leaving a first-time user with no
in-app screen explaining what a Private App even is or how to create one.
`"both"` keeps the generic Secrets screen as a fallback while letting
`connect_hubspot` be the friendly guided path.

WHY SCOPE IS PER-ACCOUNT, NOT APP-LEVEL, SAME AS n8n/Make.com/Power
Automate/MuleSoft CONNECTOR.

Each user connects their OWN HubSpot portal(s) -- these are not
developer-owned app credentials, so the connections secret is declared
per-account (default scope), not `scope="app"`.

WHY ONE SECRET HOLDING A JSON ARRAY, NOT A FLAT SECRET FOR "the" PORTAL.

HubSpot users (especially agencies) commonly manage more than one portal.
Same structural problem already solved for MuleSoft (`mulesoft_connections`),
Slack (`workspaces`), and Power Automate (`connections`): `ctx.secrets`
only supports a fixed, manifest-declared set of NAMES -- there is no "one
secret per connection_id" primitive. `hubspot_connections` holds a JSON
array of `{id, label, access_token, portal_id}` objects. `schemas.py`'s
`connection_id` parameter on every tool call addresses one specific entry
-- see `hubspot_client.py`'s `_load_connections`/`_save_connections`.
"""
from __future__ import annotations

from imperal_sdk import ChatExtension, Extension

ext = Extension(
    "hubspot-connector",
    version="0.1.0",
    display_name="HubSpot",
    description=(
        "Connect your own HubSpot portal(s) to manage your CRM and "
        "marketing data from Imperal -- contacts, companies, deals, "
        "tickets, products and line items with full CRUD, batch "
        "operations and search; associations between records; custom "
        "properties; pipelines and stages; owners; engagements (notes, "
        "calls, emails, meetings, tasks); marketing lists and form "
        "submissions; files; custom objects; webhook subscriptions; plus "
        "value-add reports like pipeline health and duplicate-contact "
        "detection. Uses your own HubSpot Private App access token -- "
        "nothing is hosted or proxied by Imperal beyond the request "
        "itself. Note: Quotes, Workflows automation, CMS Hub (sites/"
        "pages/blogs) and the Conversations inbox are out of scope -- "
        "different products/domains within HubSpot."
    ),
    icon="icon.svg",
    capabilities=[
        "hubspot:read",
        "hubspot:write",
    ],
    actions_explicit=True,
    system=False,
)

chat = ChatExtension(
    ext,
    tool_name="hubspot",
    description=(
        "HubSpot Connector -- connect your HubSpot portal via a Private "
        "App access token, then manage contacts/companies/deals/tickets/"
        "products/line items (CRUD, batch, search), associations, custom "
        "properties, pipelines/stages, owners, engagements (notes/calls/"
        "emails/meetings/tasks), marketing lists/forms, files, custom "
        "objects, webhooks, and run pipeline-health / duplicate-contact "
        "reports."
    ),
)

ext.secret(
    "hubspot_connections",
    (
        "Your connected HubSpot portal(s) -- stored as a JSON array, one "
        "entry per portal, each with its own Private App access token and "
        "portal_id/label. Managed through connect_hubspot / "
        "disconnect_hubspot -- you should not need to edit this directly."
    ),
    required=True,
    write_mode="both",
    max_bytes=65536,
    rotation_hint_days=180,
)(lambda: None)


@ext.health_check
async def health_check(ctx) -> dict:
    """Fast configuration health; no third-party call -- just confirms at
    least one portal connection is stored, same shape as MuleSoft
    Connector's health_check."""
    import json as _json
    raw = await ctx.secrets.get("hubspot_connections")
    try:
        count = len(_json.loads(raw)) if raw else 0
    except Exception:
        count = 0
    return {
        "healthy": True,
        "detail": (
            f"{count} HubSpot portal(s) connected." if count
            else "Not connected yet -- run connect_hubspot."
        ),
    }
