import copy

import pytest  # noqa: F401

from lambda_router import appsync


@pytest.fixture(scope="module")
def example_request():
    return {
        "field": "getAssets",
        "details": {
            "arguments": {},
            "identity": {
                "claims": {
                    "sub": "2067d7de-8976-4790-921a-040892531db7",
                    "device_key": "eu-",
                    "event_id": "bab1a4b5-5055-4580-8e5f-8587a53d7e9a",
                    "token_use": "access",
                    "scope": "aws.cognito.signin.user.admin",
                    "auth_time": 1579158955,
                    "iss": "https: //cognito-idp.eu-west-1.amazonaws.com/eu-west-1_asdasdas",
                    "exp": 1579162555,
                    "iat": 1579158955,
                    "jti": "6e48da7c-7100-48a8-8faf-3d42a506f138",
                    "client_id": "abcde",
                    "username": "2067d7de-8976-4790-921a-040892531db7",
                },
                "defaultAuthStrategy": "ALLOW",
                "groups": None,
                "issuer": "https://cognito-idp.eu-west-1.amazonaws.com/eu-west-1_asdasdas",
                "sourceIp": ["1.1.1.2"],
                "sub": "2067d7de-8976-4790-921a-040892531db7",
                "username": "2067d7de-8976-4790-921a-040892531db7",
            },
            "source": None,
            "result": None,
            "request": {
                "headers": {
                    "x-forwarded-for": "1.1.1.2, 5.5.5.5",
                    "accept-encoding": "gzip, deflate",
                    "cloudfront-viewer-country": "ZA",
                    "cloudfront-is-tablet-viewer": "false",
                    "via": "1.1 abcde.cloudfront.net (CloudFront)",
                    "content-type": "application/json",
                    "cloudfront-forwarded-proto": "https",
                    "x-amzn-trace-id": "Root=1-",
                    "x-amz-cf-id": "aaa",
                    "authorization": "...",
                    "content-length": "105",
                    "x-forwarded-proto": "https",
                    "host": "a.appsync-api.eu-west-1.amazonaws.com",
                    "user-agent": "python-requests/2.20.1",
                    "cloudfront-is-desktop-viewer": "true",
                    "accept": "*/*",
                    "cloudfront-is-mobile-viewer": "false",
                    "x-forwarded-port": "443",
                    "cloudfront-is-smarttv-viewer": "false",
                }
            },
            "info": {"fieldName": "getAssets", "parentTypeName": "Query", "variables": {}},
            "error": None,
            "prev": None,
            "stash": {},
            "outErrors": [],
        },
    }


class TestAppSyncEvent:
    def test_create(self, example_request):
        template = {"context": "details"}
        event = appsync.AppSyncEvent.create(raw=example_request, app={}, template=template)
        assert isinstance(event, appsync.AppSyncEvent)
        assert "2067d7de-8976-4790-921a-040892531db7" == event.identity.username
        assert "getAssets" == event.info.field_name
        assert "content-length" in event.request.headers
        assert {} == event.arguments


class TestAppSyncField:
    def test_add_route(self):
        router = appsync.AppSyncField()

        def test_route_one(event):
            return {"message": "ok"}

        def test_route_two(event):
            return {"message": "ok"}

        router.add_route(fn=test_route_one, field="one")
        router.add_route(fn=test_route_two, field="two")
        assert router.routes
        assert 2 == len(router.routes)
        assert "one" in router.routes
        assert "two" in router.routes

    def test_get_route(self, example_request):
        router = appsync.AppSyncField()
        router.add_route(fn=lambda event: "ok", field="getAssets")
        event = appsync.AppSyncEvent.create(raw=example_request, app={}, template={"context": "details"})
        route = router.get_route(event=event)
        assert route is not None
        assert callable(route)

    def test_get_route_with_invalid_field(self, example_request):
        router = appsync.AppSyncField()
        router.add_route(fn=lambda event: "ok", field="getPeople")
        event = appsync.AppSyncEvent.create(raw=example_request, app={}, template={"context": "details"})
        with pytest.raises(ValueError) as e:
            router.get_route(event=event)
            assert "No route configured for given field (field)." in str(e.value)

    def test_dispatch(self, example_request):
        router = appsync.AppSyncField()

        def test_route_one(event):
            return {"message": "ok"}

        def test_route_two(event):
            return {"message": "error"}

        router.add_route(fn=test_route_one, field="getAssets")
        router.add_route(fn=test_route_two, field="getPeople")
        second_request = copy.deepcopy(example_request)
        second_request["details"]["info"]["fieldName"] = "getPeople"
        event = appsync.AppSyncEvent.create(raw=example_request, app={}, template={"context": "details"})
        event2 = appsync.AppSyncEvent.create(raw=second_request, app={}, template={"context": "details"})
        response = router.dispatch(event=event)
        assert {"message": "ok"} == response
        response = router.dispatch(event=event2)
        assert {"message": "error"} == response

    def test_dispatch_without_route(self, example_request):
        router = appsync.AppSyncField()
        with pytest.raises(ValueError) as e:
            event = appsync.AppSyncEvent.create(raw=example_request, app={}, template={"context": "details"})
            router.dispatch(event=event)
            assert "No route configured" in str(e.value)
