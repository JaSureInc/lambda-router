import abc

from typing import Any, Callable, Optional


class Event(abc.ABC):
    """
    Abstract interface for Events.
    """


class Router(abc.ABC):
    """
    Abstract interface for Routers.
    """

    @abc.abstractmethod
    def add_route(self, *, fn: Callable) -> None:
        raise NotImplementedError("This method must be implemented by a subclass.")

    @abc.abstractmethod
    def get_route(self, *, event: Optional[Any]) -> Callable:
        raise NotImplementedError("This method must be implemented by a subclass.")

    @abc.abstractmethod
    def dispatch(self, *, event: Any) -> Any:
        raise NotImplementedError("This method must be implemented by a subclass.")
