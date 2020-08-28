import logging
import threading

from typing import Any, Callable, Dict, List, Mapping, Optional

import attr

from . import exceptions, routers
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
    event_params: Optional[Dict[str, Any]] = attr.ib(default=None, repr=False)
    router: Router = attr.ib(factory=routers.SingleRoute)
    logger: logging.Logger = attr.ib(repr=False)
    local_context: threading.local = attr.ib(repr=False, init=False, factory=threading.local)
    execution_context: Optional[Any] = attr.ib(repr=False, init=False, default=None)
    middleware_chain: Optional[List[Callable]] = attr.ib(repr=False, init=False, default=None)
    exception_handlers: List[Callable] = attr.ib(repr=False, init=False, factory=list)

    @logger.default
    def _create_logger(self):
        """
        Default initialiser that creates a stdlib logger.
        """
        logger = logging.getLogger(self.name)
        return logger

    def __attrs_post_init__(self):
        """
        Post-init hook. Used to load the middlware from the config. This requires the
        config to already have been initialised before creating the App.
        """
        self.load_middleware()

    @property
    def globals(self):
        """
        Provides a proxied dict in the ``local_context``.
        """
        if not hasattr(self.local_context, "globals"):
            self.local_context.globals = DictProxy()
        return self.local_context.globals

    def route(self, **options: Mapping[str, Any]) -> Callable:
        """
        Provides a decorator for adding a route via the configured router.
        """

        def decorator(fn: Callable):
            self.router.add_route(fn=fn, **options)
            return fn

        return decorator

    def register_exception_handler(self, fn: Callable) -> Callable:
        """
        Provides a decorator that registers a handler for any uncaught exceptions.
        """
        self.exception_handlers.append(fn)

        def decorator(fn: Callable):
            return fn

        return decorator

    def load_middleware(self):
        """
        Initialises the middlware from the app config.
        """
        dispatch = self.router.dispatch
        configured_middleware = self.config.get("MIDDLEWARE", [])
        for middleware in configured_middleware:
            mw_instance = middleware(dispatch)
            dispatch = mw_instance
        self.middleware_chain = dispatch

    def dispatch(self, *, event: Event) -> Any:
        """
        Dispatches a request via the configured middleware chain.

        :param event: The ``Event`` object pass on to the middleware chain.
        """
        return self.middleware_chain(event=event)

    def _create_event(self, raw_event: Mapping[str, Any]) -> Event:
        """
        Helper to create an event from the configured ``event_class``.
        """
        params = {
            "raw": raw_event,
            "app": self,
        }
        if self.event_params is not None:
            params.update(self.event_params)
        return self.event_class.create(**params)

    def __call__(self, raw_event: Mapping[str, Any], lambda_context: Any) -> Any:
        """
        The main entry point that is invoked by the lambda runtime environment.

        :param raw_event: The raw event mapping passed in from the lambda runtime.
        :param lambda_context: The execution contect object passed in from the lambda runtime.
        """
        event = self._create_event(raw_event)
        self.execution_context = lambda_context
        try:
            response = self.dispatch(event=event)
        except Exception as e:
            # The AWS Lambda environment catches all unhandled exceptions
            # without ever invoking the sys.excepthook handler, so this
            # mechanism is provided as a way to pass on those exceptions
            # without using sys.excepthook.
            if not isinstance(e, exceptions.HandledError):
                for fn in self.exception_handlers:
                    fn(self, event, e)
            raise
        return response
