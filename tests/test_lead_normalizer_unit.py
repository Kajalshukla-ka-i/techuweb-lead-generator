import unittest

from services.lead_normalizer import LeadNormalizer


class FakeDatabase:
    """Provide a placeholder without connecting to MongoDB."""

    collection = None


class TestLeadNormalizer(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.normalizer = LeadNormalizer(FakeDatabase())

    def test_normalize_website(self):
        self.assertEqual(
            self.normalizer.normalize_website(
                "  https://example.com  "
            ),
            "https://example.com",
        )

    def test_empty_website(self):
        for value in (None, "", False, True):
            with self.subTest(value=value):
                self.assertEqual(
                    self.normalizer.normalize_website(value),
                    "",
                )

    def test_normalize_phone(self):
        self.assertEqual(
            self.normalizer.normalize_phone(
                "+91 98765 43210"
            ),
            "919876543210",
        )

    def test_empty_phone(self):
        for value in (None, "", False):
            with self.subTest(value=value):
                self.assertEqual(
                    self.normalizer.normalize_phone(value),
                    "",
                )

    def test_normalize_text(self):
        self.assertEqual(
            self.normalizer.normalize_text("  Noida  "),
            "Noida",
        )

    def test_empty_text(self):
        for value in (None, "", False):
            with self.subTest(value=value):
                self.assertEqual(
                    self.normalizer.normalize_text(value),
                    "",
                )


if __name__ == "__main__":
    unittest.main()
