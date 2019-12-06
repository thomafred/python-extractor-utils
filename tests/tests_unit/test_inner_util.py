import unittest

from cognite.extractorutils._inner_util import _EitherId, _MockLogger


class TestMockLogger(unittest.TestCase):
    def setUp(self):
        self.logger = _MockLogger()

    def test_log_calls(self):
        try:
            self.logger.info("Here is some random info!")
            self.logger.info("Here is some random info with formatting: %s!", "This should still work")

            self.logger.warning("Here is a warning")
            self.logger.error("Here is a error")
            self.logger.critical("Here is a critical")
            self.logger.debug("Here is a debug")
            self.logger.log(1, "Here is a generic log call")
            self.logger.exception("Here is an exception message")

        except:
            # Some of the calls threw an exception, fail the test
            self.fail()

    def test_either_id(self):
        with self.assertRaises(TypeError):
            _EitherId(123, "extId")
        with self.assertRaises(TypeError):
            _EitherId()

        self.assertEqual(_EitherId(externalId="extId").__repr__(), "externalId: extId")