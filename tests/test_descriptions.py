import unittest

from app.validation import BOT_DESCRIPTION_MAX_LENGTH, normalize_bot_description


class BotDescriptionTests(unittest.TestCase):
    def test_trims_and_accepts_description_at_limit(self):
        value = "  " + "x" * BOT_DESCRIPTION_MAX_LENGTH + "  "
        self.assertEqual(normalize_bot_description(value), "x" * BOT_DESCRIPTION_MAX_LENGTH)

    def test_rejects_blank_description(self):
        with self.assertRaisesRegex(ValueError, "required"):
            normalize_bot_description(" \n\t ")

    def test_rejects_description_over_limit(self):
        with self.assertRaisesRegex(ValueError, "280"):
            normalize_bot_description("x" * (BOT_DESCRIPTION_MAX_LENGTH + 1))


if __name__ == "__main__":
    unittest.main()
