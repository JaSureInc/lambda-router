import os

from typing import Any, Dict, Mapping

from . import exceptions


def str_to_bool(bool_as_string: str) -> bool:
    """
    A converter that converts a string representation of ``True`` into a boolean.
    The following (case insensitive) strings will be return a ``True`` result:
    'true', 't', '1', 'yes', 'y', everything else will return a ``False``.

    :param bool_as_string: The string to be converted to a bool.
    :type bool_as_string: str
    :rtype: bool
    :raises TypeError: Raised when any type other than a string is passed.
    """
    if not isinstance(bool_as_string, str):
        raise TypeError("Only string types supported")
    return bool_as_string.lower() in ["true", "t", "1", "yes", "y"]


def _get_field_value(value: Any, *, params: Mapping[str, Any]) -> Any:
    """
    Returns the given value with any converters applied.
    """
    converter = params.get("converter", None)
    if converter is not None:
        return converter(value)
    return value


def _filter_with_template(unfiltered: Mapping[str, Any], *, template: Mapping[str, Any],) -> Dict[str, Any]:
    """
    Applies a given config template to a given mapping.

    :param unfiltered: The mapping to apply the config template to.
    :param template: The config template to apply.
    """
    filtered: dict = {}
    for field, params in template.items():
        if params.get("required", False):
            # Ensure required fields are present in the unfiltered dict.
            try:
                filtered[field] = _get_field_value(unfiltered[field], params=params)
            except KeyError:
                raise exceptions.ConfigError(f"Required config parameters ({field}) is missing")
        else:
            # Use the optional value from the unfiltered dict, otherwise fallback
            # to the default from the template.
            if field in unfiltered:
                filtered[field] = _get_field_value(unfiltered[field], params=params)
            else:
                if "default" in params:
                    filtered[field] = params["default"]
    return filtered


class Config(dict):
    """
    A subclass of ``dict`` that adds helper methods to load values
    from environment variables or another dictionary, optionally
    appling a congifuration template to the loaded variables.
    """

    def load_from_dict(
        self, unfiltered: Mapping[str, Any], *, prefix: str = None, template: Mapping[str, Any] = None,
    ) -> None:
        """
        Updates the config from an existing mapping, optionaly applying
        a configuration template or filtering out fields with that don't
        match a given prefix.

        :param unfiltered: The mapping to update the config from.
        :param prefix: The prefix to check for.
        :type prefix: str
        :param template: The config template to apply.

        """
        if template is not None:
            filtered = _filter_with_template(unfiltered, template=template)
        else:
            if prefix is not None:
                prefix_length = len(prefix)
                filtered = {key[prefix_length:]: value for key, value in unfiltered.items() if key.startswith(prefix)}
            else:
                filtered = unfiltered
        self.update(filtered)

    def load_from_environment(self, *, prefix: str = None, template: Mapping[str, Any] = None) -> None:
        """
        Updates the config from the current running environment, optionaly applying
        a configuration template or filtering out fields with that don't
        match a given prefix.

        :param prefix: The prefix to check for.
        :type prefix: str
        :param template: The config template to apply.
        """
        self.load_from_dict(os.environ, prefix=prefix, template=template)
