import pytest  # noqa: F401

from lambda_router import config


@pytest.fixture()
def basic_env():
    return {
        "JSR_ACCESS_KEY": "key",
        "JSR_BUCKET_NAME": "s3",
        "JSR_BUGSNAG_KEY": "key",
        "JSR_DATABASE_URL": "postgresql://postgres:@10.200.10.1/db",
        "JSR_SECRET_KEY": "secret",
        "JSR_WAIT_FOR_CONFIRM": "True",
        "DEBUG": "True",
        "EXTERNAL_HOST": "http://",
        "WAIT_IN_SECONDS": "400",
    }


@pytest.fixture()
def template():
    return {
        "JSR_ACCESS_KEY": {"required": True},
        "JSR_BUCKET_NAME": {"required": True},
        "JSR_DATABASE_URL": {"required": True},
        "JSR_SECRET_KEY": {"default": "not set"},
        "JSR_WAIT_TIME": {"default": 60},
        "JSR_WAIT_FOR_CONFIRM": {},
        "JSR_SERVICE_ID": {},
        "DEBUG": {"converter": config.str_to_bool},
        "WAIT_IN_SECONDS": {"converter": int},
    }


class TestConfigTemplate:
    def test_filter_with_template(self, basic_env, template):
        filtered = config._filter_with_template(basic_env, template=template)
        assert 8 == len(filtered)
        # Ensure default isn't used if value was already given.
        assert "secret" == filtered["JSR_SECRET_KEY"]
        # Ensure default is used when value wasn't given.
        assert 60 == filtered["JSR_WAIT_TIME"]
        # Ensure value is used as-is when no parameters were given.
        assert "True" == filtered["JSR_WAIT_FOR_CONFIRM"]
        # Ensure values present in template
        assert "JSR_SERVICE_ID" not in filtered
        # Ensure converter was called.
        assert type(filtered["DEBUG"]) == bool
        assert filtered["DEBUG"]
        assert type(filtered["WAIT_IN_SECONDS"]) == int
        assert 400 == filtered["WAIT_IN_SECONDS"]


class TestConfig:
    def test_load_from_dict(self, basic_env):
        conf = config.Config()
        conf.load_from_dict(basic_env)
        # Ensure all items in basic_env are in conf
        assert basic_env == conf

    def test_load_from_dict_with_template(self, basic_env, template):
        conf = config.Config()
        conf.load_from_dict(basic_env, template=template)
        # Ensure items not in template are not in conf.
        assert 8 == len(conf)
        assert "EXTERNAL_HOST" not in conf

    def test_load_from_dict_with_prefix(self, basic_env):
        conf = config.Config()
        prefix = "JSR_"
        conf.load_from_dict(basic_env, prefix=prefix)
        # Ensure items without prefix are not in conf.
        assert 6 == len(conf)
        # Ensure prefix has been removed from items in the conf.
        for key in conf.keys():
            assert not key.startswith(prefix)


class TestStrToBool:
    @pytest.mark.parametrize("true_str", ["true", "t", "1", "yes", "y", "TRUE", "True", "T"])
    def test_str_to_bool_with_true_strings(self, true_str):
        assert config.str_to_bool(true_str)

    @pytest.mark.parametrize("false_str", ["false", "FALSE", "0", "hello", "this is false"])
    def test_str_to_bool_with_false_strings(self, false_str):
        assert not config.str_to_bool(false_str)

    def test_str_to_bool_with_incorrect_type(self):
        with pytest.raises(TypeError):
            config.str_to_bool(1)
            config.str_to_bool(1.0)
            config.str_to_bool({})
            config.str_to_bool(())
            config.str_to_bool((False,))
