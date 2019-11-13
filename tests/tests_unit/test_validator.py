import unittest

from cognite.extractorutils.configtools import DictValidator, import_missing, recursive_none_check


class CountingLogger:
    def __init__(self, verbose=False):
        self.infos = 0
        self.warnings = 0
        self.errors = 0
        self.criticals = 0

        self.verbose = verbose

        self.all = 0

    def info(self, *args, **kwargs):
        self.infos += 1
        self.all += 1
        if self.verbose:
            print(*args)

    def warning(self, *args, **kwargs):
        self.warnings += 1
        self.all += 1
        if self.verbose:
            print(*args)

    def error(self, *args, **kwargs):
        self.errors += 1
        self.all += 1
        if self.verbose:
            print(*args)

    def critical(self, *args, **kwargs):
        self.criticals += 1
        self.all += 1
        if self.verbose:
            print(*args)

    def log(self, *args, **kwargs):
        self.infos += 1
        self.all += 1
        if self.verbose:
            print(*args)

    def exception(self, *args, **kwargs):
        self.all += 1
        if self.verbose:
            print(*args)
        raise AssertionError("Unexpected exception given to logger from vaildator")


class TestValidator(unittest.TestCase):
    def setUp(self):
        self.dic = {
            "Key1": "Value1",
            "Key2": "Value2",
            "Key3": "Value3",
            "Key4": "Value4",
            "Key5": "Value5",
            "Key6": "Value6",
        }
        self.logger = CountingLogger()
        self.val = DictValidator(logger=self.logger)  # type: ignore

    def test_required(self):
        self.val.add_required_keys(["Key1"])

        self.assertTrue(self.val.validate(self.dic))
        self.assertEqual(self.logger.warnings, 5)

        self.val.add_required_keys(["Key2", "Key3", "Key4", "Key5", "Key6"])

        self.assertTrue(self.val.validate(self.dic))
        self.assertEqual(self.logger.warnings, 5)

        self.val.add_required_keys(["NoSuchKey"])
        self.assertFalse(self.val.validate(self.dic))
        self.assertEqual(self.logger.errors, 1)

    def test_optional(self):
        self.val.add_optional_keys(["Key1"])

        self.assertTrue(self.val.validate(self.dic))
        self.assertEqual(self.logger.warnings, 5)

        self.val.add_optional_keys(["Key2", "Key3", "Key4", "Key5", "Key6"])

        self.assertTrue(self.val.validate(self.dic))
        self.assertEqual(self.logger.warnings, 5)

        self.val.add_optional_keys(["NoSuchKey"])
        self.assertTrue(self.val.validate(self.dic))

    def test_require_if_present(self):
        self.val.add_optional_keys(["Key1", "Key2", "Key3"])
        self.val.require_if_present("Key4", ["Key5"])
        self.assertTrue(self.val.validate(self.dic))
        self.val.require_if_present("Key4", ["Key6"])
        self.assertTrue(self.val.validate(self.dic))
        self.val.require_if_present("Key3", ["Key4", "Key7"])
        self.assertFalse(self.val.validate(self.dic))
        self.assertEqual(self.logger.errors, 1)
        self.assertEqual(self.logger.warnings, 1)
        self.assertEqual(self.logger.all, 2)

    def test_require_only_if_present(self):
        self.val.add_optional_keys(["Key1", "Key2", "Key3"])
        self.val.require_only_if_present("Key4", ["Key5"])
        self.assertTrue(self.val.validate(self.dic))
        self.assertEqual(self.logger.warnings, 1)
        self.val.require_only_if_present("Key4", ["Key6"])
        self.assertTrue(self.val.validate(self.dic))
        self.assertEqual(self.logger.warnings, 2)
        self.val.require_only_if_present("Key3", ["Key4", "Key7"])
        self.assertFalse(self.val.validate(self.dic))
        self.assertEqual(self.logger.errors, 1)
        self.assertEqual(self.logger.warnings, 3)
        self.assertEqual(self.logger.all, 4)

    def test_require_if_value(self):
        self.val.require_if_value("Key1", "Value2", ["DummyKey"])
        self.val.require_if_value("Key2", "Value2", ["Key3", "Key4"])
        self.assertTrue(self.val.validate(self.dic))
        self.assertEqual(self.logger.warnings, 2)
        self.val.require_if_value("Key1", "Value1", ["DoesntExist"])
        self.val.add_optional_keys(["Key5", "Key6"])
        self.assertFalse(self.val.validate(self.dic))
        self.assertEqual(self.logger.warnings, 2)
        self.assertEqual(self.logger.errors, 1)

    def test_require_only_if_value(self):
        self.val.require_only_if_value("Key1", "Value2", ["DummyKey"])
        self.val.require_only_if_value("Key2", "Value1", ["Key3", "Key4"])
        self.val.require_only_if_value("Key2", "Value2", ["Key5", "Key6"])
        self.assertTrue(self.val.validate(self.dic))
        self.assertEqual(self.logger.warnings, 2)
        self.val.require_only_if_value("Key1", "Value1", ["DoesntExist"])
        self.assertFalse(self.val.validate(self.dic))
        self.assertEqual(self.logger.warnings, 4)
        self.assertEqual(self.logger.errors, 1)

    def test_legal_values(self):
        self.val.set_legal_values("Key1", ["Value1", "Value2", "Value3"])
        self.val.add_known_keys(["Key2", "Key3", "Key4", "Key5", "Key6"])

        self.assertTrue(self.val.validate(self.dic))
        self.assertEqual(self.logger.all, 0)

        self.val.set_legal_values("Key1", ["Value2", "Value3"])
        self.assertFalse(self.val.validate(self.dic))
        self.assertEqual(self.logger.errors, 1)
        self.assertEqual(self.logger.all, 1)

    def test_add_defaults(self):
        self.val.add_optional_keys(["Key7"])
        self.val.set_default("Key7", "Value7")
        self.val.add_known_keys(["Key1", "Key2", "Key3", "Key4", "Key5", "Key6"])

        self.assertEqual(self.dic.get("Key7"), None)
        self.val.validate(self.dic, apply_defaults=True)
        self.assertEqual(self.logger.warnings, 1)
        self.assertEqual(self.logger.all, 1)
        self.assertEqual(self.dic.get("Key7"), "Value7")


class TestConfigtoolsMethods(unittest.TestCase):
    def test_import_missing(self):
        d1 = {"key1": "val1", "key2": "val2", "key3": "val3"}
        d2 = {"key4": "val4", "key5": "val5", "key6": "val6"}

        import_missing(from_dict=d1, to_dict=d2, keys=["key1"])

        self.assertDictEqual(d2, {"key1": "val1", "key4": "val4", "key5": "val5", "key6": "val6"})
        self.assertDictEqual(d1, {"key1": "val1", "key2": "val2", "key3": "val3"})

        import_missing(from_dict={"key1": "dont overwrite this"}, to_dict=d1)
        self.assertDictEqual(d1, {"key1": "val1", "key2": "val2", "key3": "val3"})

        import_missing(from_dict=d1, to_dict=d2)

        self.assertDictEqual(
            d2, {"key1": "val1", "key2": "val2", "key3": "val3", "key4": "val4", "key5": "val5", "key6": "val6"}
        )

    def test_recursive_none_check(self):
        d1 = {"key1": "val1", "key2": "val2", "key3": "val3"}
        d2 = {"key1": "val1", "key2": "val2", "key3": None}
        d3 = {"key1": "val1", "key2": "val2", "key3": ["v1", "v2", "v3"]}
        d4 = {"key1": "val1", "key2": "val2", "key3": ["v1", "v2", None]}
        d5 = {"key1": "val1", "key2": "val2", "key3": ["v1", "v2", {"check": None}]}

        self.assertEqual(recursive_none_check(d1), (False, None))
        self.assertEqual(recursive_none_check(d2), (True, "key3"))
        self.assertEqual(recursive_none_check(d3), (False, None))
        self.assertEqual(recursive_none_check(d4), (True, 2))
        self.assertEqual(recursive_none_check(d5), (True, "check"))