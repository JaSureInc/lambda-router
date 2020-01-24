from typing import Any, Callable, Dict, Optional

import attr

from .interfaces import Event, Router


@attr.s(kw_only=True)
class SingleRoute(Router):
    """
    Routes to a single defined route without any conditions.

    :param route: The single defined route. Only set via ``add_route``.
    """

    route: Optional[Callable] = attr.ib(init=False, default=None)

    def add_route(self, *, fn: Callable) -> None:
        """
        Adds the single route.

        :param fn: The callable to route to.
        :type fn: callable
        :raises ValueError: Raised when a single route has already been defined.
        """
        if self.route is not None:
            raise ValueError(
                "Single route is already defined. SingleRoute can only have a single defined route."
            )

        self.route = fn

    def get_route(self, *, event: Optional[Event]) -> Callable:
        """
        Returns the defined route

        :raises ValueError: Raised if no route is defined.
        :rtype: callable
        """
        if self.route is None:
            raise ValueError("No route defined.")

        return self.route

    def dispatch(self, *, event: Event) -> Any:
        """
        Gets the configured route and invokes the callable.

        :param event: The event to pass to the callable route.
        """
        route = self.get_route(event=event)
        return route(event=event)


@attr.s(kw_only=True)
class EventField(Router):
    """
    Routes on a the value of the specified top-level ``key`` in the
    given ``Event.raw`` dict.

    :param key: The name of the top-level key to look for when routing.
    :param routes: The routes mapping. Only set via ``add_route``
    """

    key: str = attr.ib(kw_only=True)
    routes: Dict[str, Callable] = attr.ib(init=False, factory=dict)

    def add_route(self, *, fn: Callable, key: str) -> None:
        """
        Adds the route with the given key.

        :param fn: The callable to route to.
        :type fn: callable
        :param key: The key to associate the route with.
        :type fn: str
        """
        self.routes[key] = fn

    def get_route(self, *, event: Event) -> Callable:
        """
        Returns the matching route for thevalue of the ``key`` in the
        given event.

        :raises ValueError: Raised if no route is defined or routing key is
            not present in the event.
        :rtype: callable
        """
        field_value: str = event.raw.get(self.key, None)
        if field_value is None:
            raise ValueError(f"Routing key ({self.key}) not present in the event.")
        try:
            return self.routes[field_value]
        except KeyError:
            raise ValueError(f"No route configured for given field ({field_value}).")

    def dispatch(self, *, event: Event) -> Any:
        """
        Gets the configured route and invokes the callable.

        :param event: The event to pass to the callable route.
        """
        route = self.get_route(event=event)
        return route(event=event)
