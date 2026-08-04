import unittest

from leetlift.config import Config


class ConfigTests(unittest.TestCase):
    def test_mail_channel_is_supported(self):
        config = Config.from_dict({"pushplus_channel": "mail"})
        self.assertEqual(config.pushplus_channel, "mail")

    def test_unknown_channel_is_rejected(self):
        with self.assertRaises(ValueError):
            Config.from_dict({"pushplus_channel": "unknown"})

    def test_smtp_provider_defaults_to_qq_mail(self):
        config = Config.from_dict({"delivery_provider": "smtp"})
        self.assertEqual(config.delivery_provider, "smtp")
        self.assertEqual(config.smtp_host, "smtp.qq.com")
        self.assertEqual(config.smtp_port, 465)

    def test_unknown_delivery_provider_is_rejected(self):
        with self.assertRaises(ValueError):
            Config.from_dict({"delivery_provider": "unknown"})

    def test_resend_provider_has_safe_default_sender(self):
        config = Config.from_dict({"delivery_provider": "resend"})
        self.assertEqual(config.delivery_provider, "resend")
        self.assertIn("onboarding@resend.dev", config.resend_from)


if __name__ == "__main__":
    unittest.main()
