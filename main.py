"""Entrypoint for the web-kernel and CLI tools (imperal validate/build).

Sets up sys.path, purges stale module cache, then imports ext/chat and all
handler modules so their decorators register on the same Extension
instance -- same pattern as MuleSoft Connector's / Power Automate
Connector's main.py.
"""

import os
import sys

_EXT_DIR = os.path.dirname(os.path.abspath(__file__))
if _EXT_DIR not in sys.path:
    sys.path.insert(0, _EXT_DIR)

_LOCAL = (
    "app", "schemas", "hubspot_client", "hubspot_client_extra",
    "handlers", "handlers_crm", "handlers_crm_named", "handlers_relations",
    "handlers_engagements", "handlers_marketing", "handlers_admin",
    "handlers_value_add", "panels", "panels_settings",
)
for _mod in _LOCAL:
    sys.modules.pop(_mod, None)

from app import ext, chat  # noqa: E402,F401
import handlers  # noqa: E402,F401
import handlers_crm  # noqa: E402,F401
import handlers_crm_named  # noqa: E402,F401
import handlers_relations  # noqa: E402,F401
import handlers_engagements  # noqa: E402,F401
import handlers_marketing  # noqa: E402,F401
import handlers_admin  # noqa: E402,F401
import handlers_value_add  # noqa: E402,F401
import panels  # noqa: E402,F401
import panels_settings  # noqa: E402,F401
