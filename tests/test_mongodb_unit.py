import unittest
from unittest.mock import patch

from database.mongodb import MongoDB


class FakeUpdateOne:
    """Test replacement for PyMongo's UpdateOne."""

    def __init__(self, filter, update, upsert=False):
        self.filter = filter
        self.update = update
        self.upsert = upsert


class FakeResult:
    """Simulates the result returned by MongoDB bulk_write()."""

    def __init__(
        self,
        matched_count=0,
        modified_count=0,
        upserted_ids=None,
    ):
        self.matched_count = matched_count
        self.modified_count = modified_count
        self.upserted_ids = upserted_ids or {}


class FakeCollection:
    """In-memory collection for tests; never connects to MongoDB."""

    def __init__(self, existing=None):
        self.existing = existing
        self.operations = []
        self.bulk_write_called = False
        self.bulk_write_ordered = None

    def find_one(self, query):
        if self.existing is None:
            return None

        if "maps_url" in query:
            if query["maps_url"] == self.existing.get("maps_url"):
                return self.existing

        return None

    def find(self, query):
        if self.existing is None:
            return []

        return [self.existing]

    def bulk_write(self, operations, ordered=False):
        self.bulk_write_called = True
        self.operations = list(operations)
        self.bulk_write_ordered = ordered

        return FakeResult(
            matched_count=len(self.operations),
            modified_count=len(self.operations),
            upserted_ids={
                index: f"fake-id-{index}"
                for index, operation in enumerate(self.operations)
                if getattr(operation, "upsert", False)
            },
        )


class TestMongoDBMergeSafety(unittest.TestCase):
    """Tests for MongoDB normalization, merging, and write safety."""

    def setUp(self):
        # Bypass __init__ so no MongoDB connection is created.
        self.db = MongoDB.__new__(MongoDB)

    def save_with_fakes(self, leads):
        with (
            patch("database.mongodb.UpdateOne", FakeUpdateOne),
            patch("builtins.print"),
        ):
            return self.db.save_leads(leads)

    # ---------------------------------------------------------
    # Merge safety
    # ---------------------------------------------------------

    def test_merge_preserves_existing_crm_status(self):
        existing = {
            "business_name": "Example Clinic",
            "city": "Bengaluru",
            "status": "CONTACTED",
        }
        new_lead = {
            "business_name": "Example Clinic",
            "city": "Bengaluru",
            "status": "NEW",
        }

        merged = self.db.merge_leads(existing, new_lead)

        self.assertEqual(merged["status"], "CONTACTED")

    def test_merge_preserves_existing_assignment(self):
        existing = {
            "business_name": "Example Clinic",
            "assigned_to": "Kajal",
        }
        new_lead = {
            "business_name": "Example Clinic",
            "assigned_to": None,
        }

        merged = self.db.merge_leads(existing, new_lead)

        self.assertEqual(merged["assigned_to"], "Kajal")

    def test_merge_preserves_existing_notes(self):
        existing = {
            "business_name": "Example Clinic",
            "notes": "Call again next week",
        }
        new_lead = {
            "business_name": "Example Clinic",
            "notes": "",
        }

        merged = self.db.merge_leads(existing, new_lead)

        self.assertEqual(merged["notes"], "Call again next week")

    def test_merge_preserves_existing_business_data_and_fills_missing_fields(self):
        existing = {
            "business_name": "Example Clinic",
            "city": "Bengaluru",
            "phone": "9876543210",
            "website": "",
        }
        new_lead = {
            "business_name": "Example Clinic",
            "city": "Bengaluru",
            "phone": "9999999999",
            "website": "https://example.com",
        }

        merged = self.db.merge_leads(existing, new_lead)

        self.assertEqual(
            merged["phone"],
            "9876543210",
            "An existing populated phone number must not be overwritten.",
        )
        self.assertEqual(
            merged["website"],
            "https://example.com",
            "A missing website should be filled from incoming data.",
        )

    def test_merge_does_not_include_mongodb_id(self):
        existing = {
            "_id": "fake-id",
            "business_name": "Example Clinic",
            "phone": "",
        }
        new_lead = {
            "business_name": "Example Clinic",
            "phone": "9876543210",
        }

        merged = self.db.merge_leads(existing, new_lead)

        self.assertNotIn("_id", merged)
        self.assertEqual(merged["phone"], "9876543210")

    # ---------------------------------------------------------
    # Normalization
    # ---------------------------------------------------------

    def test_normalize_phone(self):
        self.assertEqual(
            self.db.normalize_phone("+91 98765-43210"),
            "9876543210",
        )

    def test_normalize_business_name(self):
        self.assertEqual(
            self.db.normalize_business_name(" ABC Clinic, Bengaluru "),
            "abc clinic bengaluru",
        )

    # ---------------------------------------------------------
    # Better-data detection
    # ---------------------------------------------------------

    def test_has_better_data_when_phone_is_missing(self):
        existing = {
            "business_name": "Example Clinic",
            "phone": "",
        }
        new_lead = {
            "business_name": "Example Clinic",
            "phone": "9876543210",
        }

        self.assertTrue(self.db.has_better_data(existing, new_lead))

    def test_no_better_data_when_fields_are_already_filled(self):
        existing = {
            "business_name": "Example Clinic",
            "phone": "9876543210",
            "website": "https://example.com",
        }
        new_lead = {
            "business_name": "Example Clinic",
            "phone": "9876543210",
            "website": "https://example.com",
        }

        self.assertFalse(self.db.has_better_data(existing, new_lead))

    # ---------------------------------------------------------
    # New-lead insert safety
    # ---------------------------------------------------------

    def test_new_lead_uses_set_on_insert(self):
        self.db.collection = FakeCollection()

        lead = {
            "business_name": "Example Clinic",
            "city": "Bengaluru",
            "maps_url": "https://maps.example/clinic-1",
        }

        result = self.save_with_fakes([lead])

        self.assertEqual(result["new"], 1)
        self.assertTrue(self.db.collection.bulk_write_called)
        self.assertEqual(len(self.db.collection.operations), 1)

        operation = self.db.collection.operations[0]

        self.assertIn("$setOnInsert", operation.update)
        self.assertNotIn("$set", operation.update)
        self.assertTrue(operation.upsert)

    # ---------------------------------------------------------
    # Existing-lead update safety
    # ---------------------------------------------------------

    def test_existing_lead_update_preserves_crm_fields(self):
        existing = {
            "_id": "existing-id",
            "business_name": "Example Clinic",
            "city": "Bengaluru",
            "maps_url": "https://maps.example/clinic-1",
            "phone": "",
            "status": "CONTACTED",
            "assigned_to": "Kajal",
            "notes": "Follow up next week",
        }
        self.db.collection = FakeCollection(existing=existing)

        lead = {
            "business_name": "Example Clinic",
            "city": "Bengaluru",
            "maps_url": "https://maps.example/clinic-1",
            "phone": "9876543210",
            "status": "NEW",
            "assigned_to": "Another User",
            "notes": "Overwritten note",
        }

        result = self.save_with_fakes([lead])

        self.assertEqual(result["updated"], 1)
        self.assertTrue(self.db.collection.bulk_write_called)

        operation = self.db.collection.operations[0]

        self.assertEqual(operation.filter, {"_id": "existing-id"})
        self.assertIn("$set", operation.update)

        update_document = operation.update["$set"]

        self.assertEqual(update_document["status"], "CONTACTED")
        self.assertEqual(update_document["assigned_to"], "Kajal")
        self.assertEqual(update_document["notes"], "Follow up next week")
        self.assertEqual(update_document["phone"], "9876543210")
        self.assertNotIn("_id", update_document)

    # ---------------------------------------------------------
    # Google Maps URL identity safety
    # ---------------------------------------------------------

    def test_conflicting_business_identity_on_same_maps_url_is_not_matched(self):
        existing = {
            "_id": "existing-id",
            "business_name": "Example Dental Clinic",
            "city": "Bengaluru",
            "maps_url": "https://maps.example/clinic-1",
            "phone": "9876543210",
        }
        self.db.collection = FakeCollection(existing=existing)

        incoming_lead = {
            "business_name": "Completely Different Hospital",
            "city": "Mysuru",
            "maps_url": "https://maps.example/clinic-1",
            "phone": "9123456780",
        }

        result = self.db.find_existing_lead(incoming_lead)

        self.assertIsNone(
            result,
            "Conflicting business identities must not be matched by Maps URL alone.",
        )

    def test_save_skips_conflicting_business_on_same_maps_url(self):
        existing = {
            "_id": "existing-id",
            "business_name": "Example Dental Clinic",
            "city": "Bengaluru",
            "maps_url": "https://maps.example/clinic-1",
            "phone": "9876543210",
        }
        self.db.collection = FakeCollection(existing=existing)

        incoming_lead = {
            "business_name": "Completely Different Hospital",
            "city": "Mysuru",
            "maps_url": "https://maps.example/clinic-1",
            "phone": "9123456780",
        }

        result = self.save_with_fakes([incoming_lead])

        self.assertEqual(result["skipped"], 1)
        self.assertFalse(self.db.collection.bulk_write_called)
        self.assertEqual(len(self.db.collection.operations), 0)

    # ---------------------------------------------------------
    # Duplicate-write prevention
    # ---------------------------------------------------------

    def test_unchanged_duplicate_does_not_write(self):
        existing = {
            "_id": "existing-id",
            "business_name": "Example Clinic",
            "city": "Bengaluru",
            "maps_url": "https://maps.example/clinic-1",
            "phone": "9876543210",
            "website": "https://example.com",
        }
        self.db.collection = FakeCollection(existing=existing)

        lead = {
            "business_name": "Example Clinic",
            "city": "Bengaluru",
            "maps_url": "https://maps.example/clinic-1",
            "phone": "9876543210",
            "website": "https://example.com",
        }

        result = self.save_with_fakes([lead])

        self.assertEqual(result["duplicates"], 1)
        self.assertFalse(self.db.collection.bulk_write_called)
        self.assertEqual(len(self.db.collection.operations), 0)

    # ---------------------------------------------------------
    # Phone matching safety
    # ---------------------------------------------------------

    def test_different_businesses_sharing_phone_are_not_merged(self):
        existing = {
            "_id": "existing-id",
            "business_name": "Example Dental Clinic",
            "city": "Bengaluru",
            "maps_url": "https://maps.example/clinic-1",
            "phone": "+91 98765-43210",
        }
        self.db.collection = FakeCollection(existing=existing)

        incoming_lead = {
            "business_name": "Different Dental Clinic",
            "city": "Bengaluru",
            "maps_url": "https://maps.example/clinic-2",
            "phone": "9876543210",
        }

        result = self.db.find_existing_lead(incoming_lead)

        self.assertIsNone(
            result,
            "Different businesses must not be matched by phone number alone.",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)