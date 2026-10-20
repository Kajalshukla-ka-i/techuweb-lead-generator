import unittest
from copy import deepcopy
from datetime import datetime

from services.crm import CRMService


class FakeResult:
    def __init__(self, modified_count=0, deleted_count=0):
        self.modified_count = modified_count
        self.deleted_count = deleted_count


class FakeCollection:
    def __init__(self, documents=None):
        self.documents = deepcopy(documents or [])

    def find_one(self, query, projection=None):
        for document in self.documents:
            if all(document.get(k) == v for k, v in query.items()):
                result = deepcopy(document)
                if projection and projection.get("_id") == 0:
                    result.pop("_id", None)
                return result
        return None

    def update_one(self, query, update):
        for document in self.documents:
            if all(document.get(k) == v for k, v in query.items()):
                changes = update.get("$set", {})
                modified = any(
                    document.get(k) != v for k, v in changes.items()
                )
                document.update(deepcopy(changes))
                return FakeResult(modified_count=int(modified))
        return FakeResult()

    def delete_one(self, query):
        for index, document in enumerate(self.documents):
            if all(document.get(k) == v for k, v in query.items()):
                del self.documents[index]
                return FakeResult(deleted_count=1)
        return FakeResult()


class FakeDatabase:
    def __init__(self, documents=None):
        self.collection = FakeCollection(documents)


class TestCRMService(unittest.TestCase):
    def setUp(self):
        self.business_name = "Example Dental Clinic"
        self.db = FakeDatabase([
            {
                "_id": "test-1",
                "business_name": self.business_name,
                "status": "NEW",
                "notes": "",
                "email": "",
                "phone": "",
                "website": "",
                "assigned_to": "",
            }
        ])
        self.crm = CRMService(self.db)

    def test_get_existing_lead(self):
        lead = self.crm.get_lead(self.business_name)
        self.assertIsNotNone(lead)
        self.assertEqual(lead["business_name"], self.business_name)
        self.assertNotIn("_id", lead)

    def test_get_missing_lead(self):
        self.assertIsNone(self.crm.get_lead("Missing Business"))

    def test_update_valid_status(self):
        self.assertTrue(
            self.crm.update_status(self.business_name, "contacted")
        )
        lead = self.db.collection.documents[0]
        self.assertEqual(lead["status"], "CONTACTED")
        self.assertIsInstance(lead["updated_at"], datetime)

    def test_reject_invalid_status(self):
        self.assertFalse(
            self.crm.update_status(self.business_name, "INVALID")
        )
        self.assertEqual(
            self.db.collection.documents[0]["status"], "NEW"
        )

    def test_update_notes(self):
        self.assertTrue(
            self.crm.update_notes(self.business_name, "Called the clinic.")
        )
        self.assertEqual(
            self.db.collection.documents[0]["notes"], "Called the clinic."
        )

    def test_assign_lead(self):
        self.assertTrue(
            self.crm.assign_lead(self.business_name, "Test User")
        )
        self.assertEqual(
            self.db.collection.documents[0]["assigned_to"], "Test User"
        )

    def test_update_contact_details(self):
        self.assertTrue(
            self.crm.update_email(self.business_name, "test@example.com")
        )
        self.assertTrue(
            self.crm.update_phone(self.business_name, "9876543210")
        )
        self.assertTrue(
            self.crm.update_website(
                self.business_name, "https://example.com"
            )
        )
        lead = self.db.collection.documents[0]
        self.assertEqual(lead["email"], "test@example.com")
        self.assertEqual(lead["phone"], "9876543210")
        self.assertEqual(lead["website"], "https://example.com")

    def test_updates_return_false_for_missing_lead(self):
        self.assertFalse(self.crm.update_notes("Missing Business", "Test"))
        self.assertFalse(
            self.crm.assign_lead("Missing Business", "Test User")
        )
        self.assertFalse(
            self.crm.update_email("Missing Business", "test@example.com")
        )
        self.assertFalse(
            self.crm.update_phone("Missing Business", "9876543210")
        )
        self.assertFalse(
            self.crm.update_website(
                "Missing Business", "https://example.com"
            )
        )

    def test_delete_lead(self):
        self.assertTrue(self.crm.delete_lead(self.business_name))
        self.assertEqual(self.db.collection.documents, [])

    def test_delete_missing_lead(self):
        self.assertFalse(self.crm.delete_lead("Missing Business"))
        self.assertEqual(len(self.db.collection.documents), 1)


if __name__ == "__main__":
    unittest.main()