import copy

from unittest import mock

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
        event = events.LambdaEvent(raw={"field": "test"}, app=None)
        route = router.get_route(event=event)
        assert route is not None
        assert callable(route)

    def test_get_route_with_invalid_key(self):
        router = routers.EventField(key="field")
        router.add_route(fn=lambda event: "ok", key="test")
        event = events.LambdaEvent(raw={"field": "new"}, app=None)
        with pytest.raises(ValueError) as e:
            router.get_route(event=event)
            assert "No route configured for given field (field)." in str(e.value)

    def test_get_route_with_missing_key(self):
        router = routers.EventField(key="route_on")
        router.add_route(fn=lambda event: "ok", key="test")
        event = events.LambdaEvent(raw={"field": "new"}, app=None)
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
        response = router.dispatch(event=events.LambdaEvent(raw={"field": "one"}, app=None))
        assert {"message": "ok"} == response
        response = router.dispatch(event=events.LambdaEvent(raw={"field": "two"}, app=None))
        assert {"message": "error"} == response

    def test_dispatch_without_route(self):
        router = routers.EventField(key="field")
        with pytest.raises(ValueError) as e:
            router.dispatch(event=events.LambdaEvent(raw={}, app=None))
            assert "No route configured" in str(e.value)


@pytest.fixture
def sqs_event():
    return events.LambdaEvent(
        raw={
            "Records": [
                {
                    "messageId": "a11e7a78-fb68-4c06-ae19-d391158f31ed",
                    "receiptHandle": "<...>",
                    "body": (
                        '{"people_id": "daf2ccee-8b09-4710-998e-9d82c7e9bf17", '
                        '"asset_id": "25ca5c11-2a01-4c00-96d2-8654807740c1"}'
                    ),
                    "attributes": {
                        "ApproximateReceiveCount": "1",
                        "SentTimestamp": "1579162532037",
                        "SenderId": "test",
                        "ApproximateFirstReceiveTimestamp": "1579162532048",
                    },
                    "messageAttributes": {
                        "key": {
                            "stringValue": "global.person_updated",
                            "stringListValues": [],
                            "binaryListValues": [],
                            "dataType": "String",
                        }
                    },
                    "md5OfMessageAttributes": "50c840a210e7560a053b1f43fb9d2bf5",
                    "md5OfBody": "cffa6aa7af0c2b20ef1fc63569ac299e",
                    "eventSource": "aws:sqs",
                    "eventSourceARN": "arn:aws:sqs:eu-west-1::events",
                    "awsRegion": "eu-west-1",
                }
            ]
        },
        app=None,
    )


class TestSQSMessage:
    def test_from_raw_sqs_message(self, sqs_event):
        raw_message = sqs_event.raw["Records"][0]
        message = routers.SQSMessage.from_raw_sqs_message(raw_message=raw_message, key_name="key", event=sqs_event)
        assert "global.person_updated" == message.key
        assert "a11e7a78-fb68-4c06-ae19-d391158f31ed" == message.meta["messageId"]


class TestSQSMessageField:
    def test_add_route(self):
        router = routers.SQSMessageField(key="key")

        def test_route_one(msg):
            return {"message": "ok"}

        def test_route_two(msg):
            return {"message": "ok"}

        router.add_route(fn=test_route_one, key="one")
        router.add_route(fn=test_route_two, key="two")
        assert router.routes
        assert 2 == len(router.routes)
        assert "one" in router.routes
        assert "two" in router.routes

    def test_get_route(self, sqs_event):
        router = routers.SQSMessageField(key="key")
        router.add_route(fn=lambda msg: "ok", key="global.person_updated")
        raw_message = sqs_event.raw["Records"][0]
        message = router._get_message(raw_message, event=sqs_event)
        route = router.get_route(message=message)
        assert route is not None
        assert callable(route)

    def test_get_route_with_invalid_key(self, sqs_event):
        router = routers.SQSMessageField(key="key")
        router.add_route(fn=lambda msg: "ok", key="test")
        raw_message = sqs_event.raw["Records"][0]
        message = router._get_message(raw_message, event=sqs_event)
        with pytest.raises(ValueError) as e:
            router.get_route(message=message)
            assert "No route configured for given field (field)." in str(e.value)

    def test_get_route_with_missing_key(self, sqs_event):
        router = routers.SQSMessageField(key="route_on")
        router.add_route(fn=lambda msg: "ok", key="test")
        raw_message = sqs_event.raw["Records"][0]
        message = router._get_message(raw_message, event=sqs_event)
        with pytest.raises(ValueError) as e:
            router.get_route(message=message)
            assert "Routing key (route_on) is not present in the event." in str(e.value)

    def test_dispatch(self, sqs_event):
        router = routers.SQSMessageField(key="key")
        test_message_handler = mock.MagicMock()
        router.add_route(fn=test_message_handler, key="global.person_updated")
        router.dispatch(event=sqs_event)
        test_message_handler.assert_called_once()

    def test_dispatch_multiple(self, sqs_event):
        router = routers.SQSMessageField(key="key")
        # Duplicate message.
        raw_message = copy.deepcopy(sqs_event.raw["Records"][0])
        sqs_event.raw["Records"].append(raw_message)
        test_message_handler = mock.MagicMock()
        router.add_route(fn=test_message_handler, key="global.person_updated")
        router.dispatch(event=sqs_event)
        assert 2 == test_message_handler.call_count

    def test_dispatch_multiple_with_different_keys(self, sqs_event):
        router = routers.SQSMessageField(key="key")
        # Duplicate message.
        raw_message = copy.deepcopy(sqs_event.raw["Records"][0])
        raw_message["messageAttributes"]["key"]["stringValue"] = "global.person_created"
        sqs_event.raw["Records"].append(raw_message)
        first_message_handler = mock.MagicMock()
        second_message_handler = mock.MagicMock()
        router.add_route(fn=first_message_handler, key="global.person_updated")
        router.add_route(fn=second_message_handler, key="global.person_created")
        router.dispatch(event=sqs_event)
        first_message_handler.assert_called_once()
        second_message_handler.assert_called_once()
