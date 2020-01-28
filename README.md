# ``lambda_router``: Python Helpers for AWS Lambdas

``lambda_router`` is a Python package that provides a few helpers for writing Python-based AWS Lambda functions.

Its main goal is to reduce the boilerplate code when writing lambda functions that need to handle multiple routes.

## Getting Started

Install with:

```console
    $ pip install lambda_router
```

Creating a basic, single-route app:

```python
    import lambda_router


    config = lambda_router.Config()
    # Load all environment variables prefix with JSR_.
    config.load_from_environment(prefix="JSR_")
    app = lambda_router.App(name="example_lambda", config=config)


    app.route()
    def main(event):
        # This is the main route of your lambda
        return {"message": "success"}
```

Or a multi-route app that uses the `type` field in the lambda event for routing:

```python
    import lambda_router


    config = lambda_router.Config()
    # Load all environment variables prefix with JSR_.
    config.load_from_environment(prefix="JSR_")
    app = lambda_router.App(name="example_lambda", config=config, route=lambda_router.routers.EventField(key="type"))


    app.route("route_one")
    def main(event):
        return {"message": "success from route_one"}

    app.route("route_two")
    def main(event):
        return {"message": "success from route_two"}
```

## Contributing

Use `pipenv` to install the dev requirements:

```console
    $ pipenv install --dev
```

Install the git pre-commit hooks:

```console
    $ pipenv run pre-commit install
```
