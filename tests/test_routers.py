import pytest  # noqa: F401

from lambda_router import events, routers


class TestSingleRoute:
    def test_add_route(self):
        router = routers.SingleRoute()
        assert router.route is None

        def test_route(event):
            return {"message": "ok"}

        router.add_route(fn=test_route)
        assert router.route is not None
        assert test_route == router.route

    def test_add_route_duplicate(self):
        router = routers.SingleRoute()

        def test_route(event):
            return {"message": "ok"}

        def second_route(event):
            return {"mesage": "error"}

        router.add_route(fn=test_route)
        with pytest.raises(ValueError) as e:
            router.add_route(fn=second_route)
            assert "Single route is already defined" in str(e.value)

    def test_dispatch(self):
        router = routers.SingleRoute()

        def test_route(event):
            return {"message": "ok"}

        router.add_route(fn=test_route)
        response = router.dispatch(event={})
        assert {"message": "ok"} == response

    def test_dispatch_without_route(self):
        router = routers.SingleRoute()
        with pytest.raises(ValueError) as e:
            router.dispatch(event={})
            assert "No route defined" in str(e.value)


class TestEventField:
    def test_add_route(self):
        router = routers.EventField(key="field")

        def test_route_one(event):
            return {"message": "ok"}

        def test_route_two(event):
            return {"message": "ok"}

        router.add_route(fn=test_route_one, key="one")
        router.add_route(fn=test_route_two, key="two")
        assert router.routes
        assert 2 == len(router.routes)
        assert "one" in router.routes
        assert "two" in router.routes

    def test_get_route(self):
        router = routers.EventField(key="field")
        router.add_route(fn=lambda event: "ok", key="test")
        event = events.LambdaEvent(raw={"field": "test"})
        route = router.get_route(event=event)
        assert route is not None
        assert callable(route)

    def test_get_route_with_invalid_key(self):
        router = routers.EventField(key="field")
        router.add_route(fn=lambda event: "ok", key="test")
        event = events.LambdaEvent(raw={"field": "new"})
        with pytest.raises(ValueError) as e:
            router.get_route(event=event)
            assert "No route configured for given field (field)." in str(e.value)

    def test_get_route_with_missing_key(self):
        router = routers.EventField(key="route_on")
        router.add_route(fn=lambda event: "ok", key="test")
        event = events.LambdaEvent(raw={"field": "new"})
        with pytest.raises(ValueError) as e:
            router.get_route(event=event)
            assert "Routing key (route_on) is not present in the event." in str(e.value)

    def test_dispatch(self):
        router = routers.EventField(key="field")

        def test_route_one(event):
            return {"message": "ok"}

        def test_route_two(event):
            return {"message": "error"}

        router.add_route(fn=test_route_one, key="one")
        router.add_route(fn=test_route_two, key="two")
        response = router.dispatch(event=events.LambdaEvent(raw={"field": "one"}))
        assert {"message": "ok"} == response
        response = router.dispatch(event=events.LambdaEvent(raw={"field": "two"}))
        assert {"message": "error"} == response

    def test_dispatch_without_route(self):
        router = routers.EventField(key="field")
        with pytest.raises(ValueError) as e:
            router.dispatch(event=events.LambdaEvent(raw={}))
            assert "No route configured" in str(e.value)
