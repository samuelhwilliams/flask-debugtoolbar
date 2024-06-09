from __future__ import annotations

from flask import g

from . import DebugPanel


class InterceptRedirectsDebugPanel(DebugPanel):
    """A panel to allow toggling redirect intercepts via the fldt_active cookie."""

    name = "Intercept Redirects"
    has_content = False
    user_activate = True

    def nav_title(self) -> str:
        return "Intercept Redirects"
