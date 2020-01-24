from typing import Any


class DictProxy(dict):
    """
    A ``dict`` subclass that proxies attribute lookups to the dictonary.
    """

    def __getattr__(self, name: str) -> Any:
        if name in self:
            return self[name]
        else:
            raise AttributeError(f"No such attribute: {name}")

    def __setattr__(self, name: str, value: Any) -> None:
        self[name] = value

    def __delattr__(self, name: str) -> None:
        if name in self:
            del self[name]
        else:
            raise AttributeError(f"No such attribute: {name}")
