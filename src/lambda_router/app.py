import logging
import threading
from typing import Any, Callable, List, Mapping, Optional

import attr

from . import routers
from .config import Config
from .events import LambdaEvent
from .interfaces import Event, Router
from .proxies import DictProxy


@attr.s(kw_only=True)
class App:
    """
    Provides the central object and entry point for a lambda execution.

    :param name: The name of the application.
    :param config: The configuration to use for this App. Can be any dict-like object but
        generally is an instance of ``lambda_router.config.Config`.
    :param event_class: The class to use for representing lambda events.
    :param router:  The ``Router`` instance to use for this app.
    :param logger: The ``logging.Logger`` compatible logger instance to use for logging.
    """

    name: str = attr.ib()
    config: Config = attr.ib(factory=Config)
    event_class: Event = attr.ib(default=LambdaEvent)
    router: Router = attr.ib(factory=routers.SingleRoute)
    logger: logging.Logger = attr.ib(repr=False)
    local_context: threading.local = attr.ib(
        repr=False, init=False, factory=threading.local
    )
    execution_context: Optional[Any] = attr.ib(repr=False, init=False, default=None)
    middleware_chain: Optional[List[Callable]] = attr.ib(
        repr=False, init=False, default=None
    )
    exception_handlers: List[Callable] = attr.ib(repr=False, init=False, factory=list)

    @logger.default
    def _create_logger(self):
        logger = logging.getLogger(self.name)
        return logger

    def __attrs_post_init__(self):
        self.load_middleware()

    @property
    def globals(self):
        if not hasattr(self.local_context, "globals"):
            self.local_context.globals = DictProxy()
        return self.local_context.globals

    def route(self, **options: Mapping[str, Any]) -> Callable:
        def decorator(fn: Callable):
            self.router.add_route(fn=fn, **options)
            return fn

        return decorator

    def register_exception_handler(self, fn: Callable) -> Callable:
        self.exception_handlers.append(fn)

        def decorator(fn: Callable):
            return fn

        return decorator

    def load_middleware(self):
        dispatch = self.router.dispatch
        configured_middleware = self.config.get("MIDDLEWARE", [])
        for middleware in configured_middleware:
            mw_instance = middleware(dispatch)
            dispatch = mw_instance
        self.middleware_chain = dispatch

    def dispatch(self, *, event: Event) -> Any:
        return self.middleware_chain(event=event)

    def _create_event(self, raw_event: Mapping[str, Any]) -> Event:
        return self.event_class(raw=raw_event)

    def __call__(self, raw_event: Mapping[str, Any], lambda_context: Any) -> Any:
        event = self._create_event(raw_event)
        self.execution_context = lambda_context
        try:
            response = self.dispatch(event=event)
        except Exception as e:
            # The AWS Lambda environment catches all unhandled exceptions
            # without ever invoking the sys.excepthook handler, so this
            # mechanism is provided as a way to pass on those exceptions
            # without using sys.excepthook.
            for fn in self.exception_handlers:
                fn(self, event, e)
            raise
        return response
