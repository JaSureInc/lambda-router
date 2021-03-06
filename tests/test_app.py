import pytest  # noqa: F401

from lambda_router.app import App, Config, exceptions, routers


class TestApp:
    def test_default_config(self):
        app = App(name="test_default_config")

        @app.route()
        def main_route(event):
            return {"result": "success"}

        assert app.router.route is not None

        event = {}
        context = {}
        result = app(event, context)
        assert result is not None
        assert "result" in result
        assert "success" == result["result"]

    def test_double_route(self):
        app = App(name="test_double_route")

        @app.route()
        def main_route(event):
            return {"result": "success"}

        with pytest.raises(ValueError) as e:

            @app.route()
            def second_route(event):
                return {"result": "success"}

            assert "Main route is already defined" in str(e)

    def test_middlware(self):
        event_order = []

        def test_middleware(dispatch):
            def middleware(event):
                # Pre dispatch
                event_order.append("pre")
                response = dispatch(event=event)
                # Post dispatch
                event_order.append("post")
                return response

            return middleware

        config = Config()
        config["MIDDLEWARE"] = [test_middleware]
        app = App(name="test_middleware", config=config)

        @app.route()
        def main_route(event):
            event_order.append("request")
            return {"result": "success"}

        # Ensure middleware initiliased correctly:
        assert app.middleware_chain is not None
        response = app({}, {})
        assert ["pre", "request", "post"] == event_order
        assert {"result": "success"} == response

    def test_register_exception_handler(self):
        app = App(name="test_register_exception_handler")
        handled = False

        @app.register_exception_handler
        def handle_exceptions(app, event, e):
            handled = True
            print(f"handled: {handled}")

        assert app.exception_handlers

        @app.route()
        def main_route(event):
            raise ValueError("Things went wrong")

        with pytest.raises(ValueError):
            app({}, {})
            assert handled

    def test_register_exception_handler_with_handled_error(self):
        app = App(name="test_register_exception_handler_with_handled_error")
        handled = False

        @app.register_exception_handler
        def handle_exceptions(app, event, e):
            handled = True
            print(f"handled: {handled}")

        assert app.exception_handlers

        @app.route()
        def main_route(event):
            raise exceptions.HandledError("Things went wrong")

        with pytest.raises(exceptions.HandledError):
            app({}, {})
            assert not handled

    def test_event_field(self):
        app = App(name="test_default_config", router=routers.EventField(key="field"))

        @app.route(key="main")
        def main_route(event):
            return {"result": "success"}

        @app.route(key="alt")
        def alt_route(event):
            return {"result": "failure"}

        event = {"field": "main"}
        context = {}
        result = app(event, context)
        assert {"result": "success"} == result
        event = {"field": "alt"}
        result = app(event, context)
        assert {"result": "failure"} == result
