"""Bus event definitions."""

from pydantic import BaseModel, Field


class InstanceDisposedEvent(BaseModel):
    """Event emitted when an instance is disposed."""

    directory: str = Field(description="Directory of the disposed instance")


class BusEvent:
    """Namespace for bus event definitions."""

    @staticmethod
    def define(name: str, schema: type[BaseModel]) -> type[BaseModel]:
        """Define a new bus event type."""
        schema.__event_name__ = name  # type: ignore
        return schema


# Common event types
InstanceDisposed = BusEvent.define("server.instance.disposed", InstanceDisposedEvent)
