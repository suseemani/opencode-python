"""Event bus system for decoupled communication."""

from collections.abc import Callable
from typing import Any

from pydantic import BaseModel


class BusEventDefinition(BaseModel):
    """Definition of a bus event type."""

    type: str
    properties: type[BaseModel]

    class Config:
        arbitrary_types_allowed = True


class EventBus:
    """Event bus for publishing and subscribing to events."""

    def __init__(self) -> None:
        self._subscriptions: dict[str, list[Callable[[Any], Any]]] = {}

    def publish(self, event_type: str, properties: dict[str, Any]) -> None:
        """Publish an event to all subscribers."""
        payload = {"type": event_type, "properties": properties}

        # Notify specific subscribers
        for callback in self._subscriptions.get(event_type, []):
            try:
                callback(payload)
            except Exception:
                pass

        # Notify wildcard subscribers
        for callback in self._subscriptions.get("*", []):
            try:
                callback(payload)
            except Exception:
                pass

    def subscribe(
        self, event_type: str, callback: Callable[[Any], Any]
    ) -> Callable[[], None]:
        """Subscribe to an event type."""
        if event_type not in self._subscriptions:
            self._subscriptions[event_type] = []

        self._subscriptions[event_type].append(callback)

        def unsubscribe() -> None:
            if event_type in self._subscriptions:
                try:
                    self._subscriptions[event_type].remove(callback)
                except ValueError:
                    pass

        return unsubscribe

    def subscribe_all(self, callback: Callable[[Any], Any]) -> Callable[[], None]:
        """Subscribe to all events."""
        return self.subscribe("*", callback)

    def once(
        self, event_type: str, callback: Callable[[Any], str | None]
    ) -> Callable[[], None]:
        """Subscribe to an event once."""
        unsub: Callable[[], None] | None = None

        def wrapped(event: Any) -> None:
            result = callback(event)
            if result == "done" and unsub:
                unsub()

        unsub = self.subscribe(event_type, wrapped)
        return unsub


# Global event bus instance
_global_bus = EventBus()


def get_bus() -> EventBus:
    """Get the global event bus."""
    return _global_bus


# Instance-specific event bus management
_instance_buses: dict[str, EventBus] = {}


def get_instance_bus(instance_id: str) -> EventBus:
    """Get or create an event bus for a specific instance."""
    if instance_id not in _instance_buses:
        _instance_buses[instance_id] = EventBus()
    return _instance_buses[instance_id]


def remove_instance_bus(instance_id: str) -> None:
    """Remove an instance-specific event bus."""
    _instance_buses.pop(instance_id, None)
