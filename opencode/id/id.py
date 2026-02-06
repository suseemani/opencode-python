"""ID generation utilities."""

import os
import time
from typing import Literal

Prefix = Literal["session", "message", "permission", "question", "user", "part", "pty", "tool"]

prefixes = {
    "session": "ses",
    "message": "msg",
    "permission": "per",
    "question": "que",
    "user": "usr",
    "part": "prt",
    "pty": "pty",
    "tool": "tool",
}

LENGTH = 26

# State for monotonic ID generation
_last_timestamp = 0
_counter = 0


def _random_base62(length: int) -> str:
    """Generate random base62 string of given length."""
    chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    result = ""
    bytes_data = os.urandom(length)
    for i in range(length):
        result += chars[bytes_data[i] % 62]
    return result


def create(prefix: Prefix, descending: bool, timestamp: int | None = None) -> str:
    """Create a new ID with the given prefix."""
    global _last_timestamp, _counter

    current_timestamp = timestamp or int(time.time() * 1000)

    if current_timestamp != _last_timestamp:
        _last_timestamp = current_timestamp
        _counter = 0
    _counter += 1

    now = (current_timestamp * 0x1000) + _counter

    if descending:
        now = ~now

    # Convert to 6 bytes
    time_bytes = bytearray(6)
    for i in range(6):
        time_bytes[i] = (now >> (40 - 8 * i)) & 0xFF

    return f"{prefixes[prefix]}_{time_bytes.hex()}{_random_base62(LENGTH - 12)}"


def ascending(prefix: Prefix, given: str | None = None) -> str:
    """Generate or validate an ascending ID."""
    if given is None:
        return create(prefix, False)

    if not given.startswith(prefixes[prefix]):
        raise ValueError(f"ID {given} does not start with {prefixes[prefix]}")
    return given


def descending(prefix: Prefix, given: str | None = None) -> str:
    """Generate or validate a descending ID."""
    if given is None:
        return create(prefix, True)

    if not given.startswith(prefixes[prefix]):
        raise ValueError(f"ID {given} does not start with {prefixes[prefix]}")
    return given


def schema(prefix: Prefix) -> str:
    """Get the schema prefix for validation."""
    return prefixes[prefix]


def timestamp(id: str) -> int:
    """Extract timestamp from an ascending ID. Does not work with descending IDs."""
    prefix = id.split("_")[0]
    hex_part = id[len(prefix) + 1 : len(prefix) + 13]
    encoded = int(hex_part, 16)
    return encoded // 0x1000
