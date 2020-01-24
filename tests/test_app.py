import pytest  # noqa: F401

from lambda_router.app import App, Config


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

        print(app.exception_handlers)
        assert app.exception_handlers

        @app.route()
        def main_route(event):
            raise ValueError("Things went wrong")

        with pytest.raises(ValueError):
            app({}, {})
            assert handled
