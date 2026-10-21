from pymongo import MongoClient, UpdateOne

from config.settings import (
    MONGODB_URI,
    DATABASE_NAME,
    COLLECTION_NAME,
    validate_settings,
)


class MongoDB:
    """
    MongoDB operations for TECHUWEB Lead Generator.

    Responsibilities:
    - Connect to MongoDB.
    - Create non-unique indexes.
    - Normalize business names and phone numbers.
    - Find existing leads.
    - Merge useful business information safely.
    - Preserve existing CRM-managed fields.
    - Save new leads and update incomplete records.

    This module does not automatically delete or merge
    separate database records.
    """

    CRM_MANAGED_FIELDS = {
        "status",
        "assigned_to",
        "notes",
    }

    BUSINESS_DATA_FIELDS = [
        "business_name",
        "category",
        "rating",
        "reviews",
        "phone",
        "website",
        "address",
        "email",
        "maps_url",
        "data_status",
        "missing_fields",
        "valid_phone",
        "lead_score",
        "opportunity",
        "source",
        "city",
        "state",
        "keyword",
    ]

    IMPROVEMENT_FIELDS = [
        "phone",
        "website",
        "address",
        "email",
        "reviews",
        "rating",
        "category",
    ]

    # ==================================================
    # INITIALIZE CONNECTION
    # ==================================================

    def __init__(self):
        validate_settings()

        self.client = MongoClient(
            MONGODB_URI,
            serverSelectionTimeoutMS=10000,
        )

        try:
            self.client.admin.command("ping")

            self.db = self.client[DATABASE_NAME]

            self.collection = self.db[COLLECTION_NAME]

            self.create_indexes()

        except Exception:
            self.client.close()

            raise RuntimeError(
                "Could not initialize MongoDB. "
                "Check your connection string, network access, "
                "database permissions, and Atlas configuration."
            ) from None

    # ==================================================
    # CREATE INDEXES
    # ==================================================

    def create_indexes(self):
        """
        Create non-unique indexes for common lookups.

        These indexes improve query performance but do not
        guarantee uniqueness.
        """

        fields = [
            "phone",
            "business_name",
            "city",
            "category",
            "status",
            "keyword",
            "maps_url",
        ]

        for field in fields:
            self.collection.create_index(field)

    # ==================================================
    # NORMALIZE PHONE
    # ==================================================

    @staticmethod
    def normalize_phone(phone):
        """
        Normalize phone numbers for comparison.

        Example:
            '+91 98765-43210' -> '9876543210'

        The leading Indian country code is removed only
        when the normalized number contains 12 digits
        beginning with 91.
        """

        if phone is None or isinstance(phone, bool):
            return ""

        digits = "".join(
            character
            for character in str(phone)
            if character.isdigit()
        )

        if len(digits) == 12 and digits.startswith("91"):
            digits = digits[2:]

        return digits

    # ==================================================
    # NORMALIZE BUSINESS NAME
    # ==================================================

    @staticmethod
    def normalize_business_name(business_name):
        """
        Normalize a business name for comparison.

        Example:
            ' ABC Clinic, Bengaluru '
            -> 'abc clinic bengaluru'
        """

        if business_name is None or isinstance(
            business_name,
            bool,
        ):
            return ""

        name = str(business_name).lower()

        name = "".join(
            character if character.isalnum() else " "
            for character in name
        )

        return " ".join(name.split())

    # ==================================================
    # NORMALIZE GENERAL TEXT
    # ==================================================

    @staticmethod
    def normalize_text(value):
        """Normalize text for comparison."""

        if value is None or isinstance(value, bool):
            return ""

        return " ".join(str(value).strip().lower().split())

    # ==================================================
    # FIND EXISTING LEAD
    # ==================================================

    def find_existing_lead(self, lead):
        """
        Find an existing lead using these checks:

        1. Exact Google Maps URL.
        2. Normalized phone + business name + city.
        3. Normalized business name + city.

        A phone number alone is not sufficient to identify a business.
        """

        maps_url = lead.get("maps_url")

        business_name = self.normalize_business_name(
            lead.get("business_name")
        )

        city = self.normalize_text(lead.get("city"))

        phone = self.normalize_phone(lead.get("phone"))

        # ----------------------------------------------
        # LEVEL 1: GOOGLE MAPS URL
        # ----------------------------------------------

        if maps_url:
            existing = self.collection.find_one(
                {"maps_url": maps_url}
            )

            if existing:
                return existing

        # ----------------------------------------------
        # LEVEL 2: PHONE + BUSINESS IDENTITY
        # ----------------------------------------------

        if phone and business_name and city:
            existing_leads = self.collection.find(
                {
                    "phone": {
                        "$exists": True,
                        "$nin": ["", None],
                    }
                }
            )

            for existing in existing_leads:
                existing_phone = self.normalize_phone(
                    existing.get("phone")
                )

                existing_name = self.normalize_business_name(
                    existing.get("business_name")
                )

                existing_city = self.normalize_text(
                    existing.get("city")
                )

                if (
                    existing_phone == phone
                    and existing_name == business_name
                    and existing_city == city
                ):
                    return existing

        # ----------------------------------------------
        # LEVEL 3: BUSINESS NAME + CITY
        # ----------------------------------------------

        if business_name and city:
            existing_leads = self.collection.find(
                {
                    "city": {
                        "$exists": True,
                        "$nin": ["", None],
                    }
                }
            )

            for existing in existing_leads:
                existing_name = self.normalize_business_name(
                    existing.get("business_name")
                )

                existing_city = self.normalize_text(
                    existing.get("city")
                )

                if (
                    existing_name == business_name
                    and existing_city == city
                ):
                    return existing

        return None

    # ==================================================
    # CHECK WHETHER NEW DATA IMPROVES EXISTING DATA
    # ==================================================

    def has_better_data(self, existing, new_lead):
        """
        Return True if the incoming lead fills at least
        one missing business-data field.

        Existing non-empty values are not considered missing.
        """

        for field in self.IMPROVEMENT_FIELDS:
            old_value = existing.get(field)
            new_value = new_lead.get(field)

            if (
                not self._has_value(old_value)
                and self._has_value(new_value)
            ):
                return True

        return False

    # ==================================================
    # CHECK WHETHER A VALUE EXISTS
    # ==================================================

    @staticmethod
    def _has_value(value):
        """Treat None, False, empty strings and empty lists as empty."""

        if value is None or isinstance(value, bool):
            return False

        if isinstance(value, str):
            return bool(value.strip())

        if isinstance(value, (list, tuple, dict, set)):
            return bool(value)

        return True

    # ==================================================
    # MERGE LEAD DATA
    # ==================================================

    def merge_leads(self, existing, new_lead):
        """
        Merge incoming business data into an existing lead.

        Safety rules:
        - Existing CRM status is preserved.
        - Existing assignee is preserved.
        - Existing notes are preserved.
        - Missing CRM values can be initialized from
          incoming data.
        - Existing _id is excluded from the update payload.
        - Existing business values are retained when incoming
          values are empty.
        """

        # Never include MongoDB's immutable _id in a $set update.
        merged = {
            key: value
            for key, value in existing.items()
            if key != "_id"
        }

        for field in self.BUSINESS_DATA_FIELDS:
            old_value = existing.get(field)
            new_value = new_lead.get(field)

            if not self._has_value(old_value) and self._has_value(new_value):
                merged[field] = new_value

        # Preserve existing CRM-managed values.
        for field in self.CRM_MANAGED_FIELDS:
            old_value = existing.get(field)
            new_value = new_lead.get(field)

            if self._has_value(old_value):
                merged[field] = old_value

            elif self._has_value(new_value):
                merged[field] = new_value

        return merged

    # ==================================================
    # SAVE LEADS
    # ==================================================

    def save_leads(self, leads):
        """
        Save new leads and improve existing records.

        Existing leads are updated only when an incoming
        business-data field fills a missing value.

        This method does not delete database records.
        """

        new_count = 0
        updated_count = 0
        duplicate_count = 0
        skipped_count = 0

        operations = []

        for lead in leads:
            business_name = lead.get("business_name")
            maps_url = lead.get("maps_url")
            city = lead.get("city")

            # ------------------------------------------
            # VALIDATE LEAD IDENTITY
            # ------------------------------------------

            if not self._has_value(business_name):
                print(
                    "Lead skipped: missing business name."
                )

                skipped_count += 1
                continue

            # ------------------------------------------
            # FIND EXISTING LEAD
            # ------------------------------------------

            existing_lead = self.find_existing_lead(lead)

            # ------------------------------------------
            # NEW LEAD
            # ------------------------------------------

            if not existing_lead:

                if self._has_value(maps_url):
                    identity_filter = {
                        "maps_url": maps_url
                    }

                elif (
                    self._has_value(business_name)
                    and self._has_value(city)
                ):
                    identity_filter = {
                        "business_name": business_name,
                        "city": city,
                    }

                else:
                    print(
                        f"Lead skipped: insufficient identity "
                        f"information for {business_name}."
                    )

                    skipped_count += 1
                    continue

                new_document = {
                    key: value
                    for key, value in lead.items()
                    if key != "_id"
                }

                new_document.setdefault("status", "NEW")

                operations.append(
                    UpdateOne(
                        identity_filter,
                        {
                            "$setOnInsert": new_document
                        },
                        upsert=True,
                    )
                )

                new_count += 1

                print(f"New lead queued: {business_name}")

                continue

            # ------------------------------------------
            # EXISTING LEAD
            # ------------------------------------------

            if self.has_better_data(existing_lead, lead):
                merged_lead = self.merge_leads(
                    existing_lead,
                    lead,
                )

                operations.append(
                    UpdateOne(
                        {
                            "_id": existing_lead["_id"]
                        },
                        {
                            "$set": merged_lead
                        },
                    )
                )

                updated_count += 1

                print(f"Lead update queued: {business_name}")

            else:
                duplicate_count += 1

                print(
                    f"Duplicate skipped: {business_name}"
                )

        # ----------------------------------------------
        # EXECUTE OPERATIONS
        # ----------------------------------------------

        if operations:
            result = self.collection.bulk_write(
                operations,
                ordered=False,
            )

            print("\nMongoDB write completed.")

            print(
                f"Matched records: {result.matched_count}"
            )

            print(
                f"Modified records: {result.modified_count}"
            )

            print(
                f"Upserted records: {len(result.upserted_ids)}"
            )

        # ----------------------------------------------
        # SUMMARY
        # ----------------------------------------------

        print("\n" + "=" * 50)
        print("TECHUWEB LEAD SAVE SUMMARY")
        print("=" * 50)

        print(f"New leads queued: {new_count}")
        print(f"Existing leads queued for update: {updated_count}")
        print(f"Duplicates skipped: {duplicate_count}")
        print(f"Invalid leads skipped: {skipped_count}")

        return {
            "new": new_count,
            "updated": updated_count,
            "duplicates": duplicate_count,
            "skipped": skipped_count,
        }

    # ==================================================
    # GET ALL LEADS
    # ==================================================

    def get_all(self):
        """Return all leads as a list."""

        return list(
            self.collection.find()
        )

    # ==================================================
    # CLOSE CONNECTION
    # ==================================================

    def close(self):
        """Close the MongoDB client connection."""

        if getattr(self, "client", None):
            self.client.close()