"""Authentication module for opencode."""

from opencode.auth.index import (
    OAuthAuth,
    ApiAuth,
    WellKnownAuth,
    AuthInfo,
    OAUTH_DUMMY_KEY,
    get,
    set,
    all,
    remove,
)

__all__ = [
    "OAuthAuth",
    "ApiAuth",
    "WellKnownAuth",
    "AuthInfo",
    "OAUTH_DUMMY_KEY",
    "get",
    "set",
    "all",
    "remove",
]
