import json
import tempfile
import unittest
from pathlib import Path


REQUIRED_FIELDS = [
    "business_name",
    "phone",
    "website",
    "city",
]


def load_backup(file_path):
    """Load a JSON backup and validate its structure and required fields."""
    file_path = Path(file_path)

    if not file_path.is_file():
        raise FileNotFoundError(
            f"Backup file not found: {file_path}"
        )

    try:
        with file_path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Backup contains invalid JSON: {file_path}"
        ) from exc

    if not isinstance(data, list):
        raise ValueError(
            "Backup must contain a JSON list of records."
        )

    for index, record in enumerate(data, start=1):
        if not isinstance(record, dict):
            raise ValueError(
                f"Record {index} must be a JSON object."
            )

        missing_fields = [
            field
            for field in REQUIRED_FIELDS
            if field not in record
        ]

        if missing_fields:
            raise ValueError(
                f"Record {index} is missing required fields: "
                f"{', '.join(missing_fields)}"
            )

    return data


class TestBackupIntegrity(unittest.TestCase):

    def setUp(self):
        """Create an isolated temporary directory for each test."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.backup_file = (
            Path(self.temp_dir.name) / "test_backup.json"
        )

    def tearDown(self):
        """Remove temporary test files."""
        self.temp_dir.cleanup()

    def write_backup(self, data):
        """Write test data to a temporary JSON backup."""
        with self.backup_file.open(
            "w",
            encoding="utf-8"
        ) as file:
            json.dump(data, file)

    def test_backup_file_exists(self):
        self.write_backup([])

        self.assertTrue(self.backup_file.is_file())

    def test_backup_contains_valid_json(self):
        self.write_backup([])

        self.assertEqual(
            load_backup(self.backup_file),
            []
        )

    def test_every_record_is_a_dictionary(self):
        records = [
            {
                "business_name": "Example Clinic",
                "phone": "1234567890",
                "website": "",
                "city": "Bengaluru",
            }
        ]

        self.write_backup(records)
        data = load_backup(self.backup_file)

        for record in data:
            self.assertIsInstance(record, dict)

    def test_required_fields_are_present(self):
        record = {
            "business_name": "Example Clinic",
            "phone": "1234567890",
            "website": "",
            "city": "Bengaluru",
        }

        self.write_backup([record])
        data = load_backup(self.backup_file)

        for item in data:
            for field in REQUIRED_FIELDS:
                self.assertIn(field, item)

    def test_empty_backup_is_valid_json_list(self):
        self.write_backup([])

        self.assertEqual(
            load_backup(self.backup_file),
            []
        )

    def test_missing_backup_raises_error(self):
        with self.assertRaises(FileNotFoundError):
            load_backup(self.backup_file)

    def test_non_list_backup_raises_error(self):
        self.write_backup(
            {"business_name": "Example Clinic"}
        )

        with self.assertRaisesRegex(
            ValueError,
            "JSON list"
        ):
            load_backup(self.backup_file)

    def test_non_dictionary_record_raises_error(self):
        self.write_backup(["invalid record"])

        with self.assertRaisesRegex(
            ValueError,
            "JSON object"
        ):
            load_backup(self.backup_file)

    def test_missing_required_field_raises_error(self):
        record = {
            "business_name": "Example Clinic",
            "phone": "1234567890",
            "city": "Bengaluru",
        }

        self.write_backup([record])

        with self.assertRaisesRegex(
            ValueError,
            "website"
        ):
            load_backup(self.backup_file)

    def test_empty_required_field_value_is_allowed(self):
        record = {
            "business_name": "Example Clinic",
            "phone": "1234567890",
            "website": "",
            "city": "Bengaluru",
        }

        self.write_backup([record])
        data = load_backup(self.backup_file)

        self.assertEqual(data[0]["website"], "")


if __name__ == "__main__":
    unittest.main(verbosity=2)