from typing import Any, Dict, Mapping

import attr

from .interfaces import Event


@attr.s(kw_only=True)
class LambdaEvent(Event):
    """
    A generic encapsulation of the Lambda event.

    :param raw: The raw event has received from the lambda execution.
    :param session: Per session / invocation storage.
    """

    raw: Mapping[str, Any] = attr.ib(repr=False)
    session: Dict[str, Any] = attr.ib(repr=False, factory=dict)
