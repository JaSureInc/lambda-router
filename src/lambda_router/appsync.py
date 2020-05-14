import abc
import enum

from typing import Any, Dict, Mapping, Optional

import attr

from jsonpath_rw import parse

from . import exceptions, interfaces


class AuthorizationType(enum.Enum):
    COGNITO = "AMAZON_COGNITO_USER_POOLS"
    IAM = "AWS_IAM"


class Identity(abc.ABC):
    """Abstract class for AppSync identities."""

    @abc.abstractclassmethod
    def from_raw(cls, *, raw, app):
        raise NotImplementedError("This classmethod must be implemented by a subclass.")


@attr.s(kw_only=True, frozen=True)
class IAMIdentity(Identity):
    kind: AuthorizationType = attr.ib(default=AuthorizationType.IAM)
    raw: Mapping[str, Any] = attr.ib(repr=False)

    @classmethod
    def from_raw(cls, raw):
        return cls(raw=raw)


@attr.s(kw_only=True, frozen=True)
class CognitoIdentity(Identity):
    kind: AuthorizationType = attr.ib(default=AuthorizationType.COGNITO)
    claims: Mapping[str, Any] = attr.ib(repr=False)
    default_auth_strategy: str = attr.ib(repr=False)
    issuer: str = attr.ib(repr=False)
    source_ip: str = attr.ib(repr=False)
    sub: str = attr.ib(repr=False)
    username: str = attr.ib()

    @classmethod
    def from_raw(cls, raw):
        return cls(
            claims=raw["claims"],
            default_auth_strategy=raw["defaultAuthStrategy"],
            issuer=raw["issuer"],
            source_ip=raw["sourceIp"],
            sub=raw["sub"],
            username=raw["username"],
        )


def _create_identity_from_raw(raw: Mapping[str, Any]):
    if not raw:
        # API_KEY authorization types don't populate the identity field.
        return None
    if "sub" in raw:
        return CognitoIdentity.from_raw(raw)
    if "cognitoIdentityPoolId":
        return IAMIdentity.from_raw(raw)


@attr.s(kw_only=True, frozen=True)
class Info:
    field_name: str = attr.ib()
    parent_type_name: str = attr.ib(repr=False)
    variables: Mapping[str, Any] = attr.ib(repr=False)

    @classmethod
    def from_raw(cls, raw):
        return cls(field_name=raw["fieldName"], parent_type_name=raw["parentTypeName"], variables=raw["variables"])


@attr.s(kw_only=True, frozen=True)
class Request:
    headers: Mapping[str, Any] = attr.ib(repr=False)

    @classmethod
    def from_raw(cls, raw):
        return cls(headers=raw["headers"])


@attr.s(kw_only=True, frozen=True)
class AppSyncEvent(interfaces.Event):
    """
    An AWS AppSync encapsulation of the Lambda event.
    """

    raw: Mapping[str, Any] = attr.ib(repr=False)
    session: Dict[str, Any] = attr.ib(repr=False, factory=dict)
    app = attr.ib(repr=False)
    arguments: Mapping[str, Any] = attr.ib(factory=dict)
    identity: Optional[Identity] = attr.ib(default=None)
    info: Info = attr.ib(default=None)
    request: Request = attr.ib(factory=dict)

    @classmethod
    def create(cls, *, raw, app, template):
        if not isinstance(template, dict):
            raise exceptions.ConfigError(
                "AppSyncEvent template must specifiy at least the location of the context field"
            )

        try:
            context_location = template["context"]
        except KeyError:
            raise exceptions.ConfigError(
                "AppSyncEvent template must specifiy at least the location of the context field"
            )

        raw_context = parse(context_location).find(raw)
        raw_context = raw_context[0].value

        try:
            arguments = raw_context["arguments"]
            identity = _create_identity_from_raw(raw_context["identity"])
            info = Info.from_raw(raw_context["info"])
            request = Request.from_raw(raw_context["request"])
        except KeyError as excinfo:
            raise exceptions.ConfigError(f"Could not load {excinfo} fields from context")

        return cls(raw=raw, app=app, arguments=arguments, identity=identity, info=info, request=request)
