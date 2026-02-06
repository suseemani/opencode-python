"""Installation management module for opencode."""

from opencode.installation.index import (
    InstallationInfo,
    UpgradeFailedError,
    VERSION,
    CHANNEL,
    USER_AGENT,
    info,
    is_preview,
    is_local,
    method,
    upgrade,
    latest,
    Event,
)

__all__ = [
    "InstallationInfo",
    "UpgradeFailedError",
    "VERSION",
    "CHANNEL",
    "USER_AGENT",
    "info",
    "is_preview",
    "is_local",
    "method",
    "upgrade",
    "latest",
    "Event",
]
