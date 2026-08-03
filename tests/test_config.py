import unittest

from leetlift.config import Config


class ConfigTests(unittest.TestCase):
    def test_mail_channel_is_supported(self):
        config = Config.from_dict({"pushplus_channel": "mail"})
        self.assertEqual(config.pushplus_channel, "mail")

    def test_unknown_channel_is_rejected(self):
        with self.assertRaises(ValueError):
            Config.from_dict({"pushplus_channel": "unknown"})


if __name__ == "__main__":
    unittest.main()
