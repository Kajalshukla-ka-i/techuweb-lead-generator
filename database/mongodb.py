from pymongo import MongoClient, UpdateOne

from config.settings import (
    MONGODB_URI,
    DATABASE_NAME,
    COLLECTION_NAME,
)


class MongoDB:

    def __init__(self):

        self.client = MongoClient(
            MONGODB_URI
        )

        self.db = self.client[
            DATABASE_NAME
        ]

        self.collection = self.db[
            COLLECTION_NAME
        ]

        self.create_indexes()

    # ==================================================
    # CREATE INDEXES
    # ==================================================

    def create_indexes(self):

        self.collection.create_index(
            "phone"
        )

        self.collection.create_index(
            "business_name"
        )

        self.collection.create_index(
            "city"
        )

        self.collection.create_index(
            "category"
        )

        self.collection.create_index(
            "status"
        )

        self.collection.create_index(
            "keyword"
        )

        self.collection.create_index(
            "maps_url"
        )

    # ==================================================
    # NORMALIZE PHONE
    # ==================================================

    def normalize_phone(self, phone):

        if not phone:
            return ""

        phone = (
            str(phone)
            .replace(" ", "")
            .replace("-", "")
            .replace("(", "")
            .replace(")", "")
        )

        if phone.startswith("+91"):
            phone = phone[3:]

        return phone

    # ==================================================
    # NORMALIZE BUSINESS NAME
    # ==================================================

    def normalize_business_name(
        self,
        business_name
    ):

        if not business_name:
            return ""

        name = str(
            business_name
        ).lower()

        name = "".join(
            char
            if char.isalnum()
            else " "
            for char in name
        )

        name = " ".join(
            name.split()
        )

        return name

    # ==================================================
    # FIND EXISTING LEAD
    # ==================================================

    def find_existing_lead(
        self,
        lead
    ):

        business_name = lead.get(
            "business_name"
        )

        city = lead.get(
            "city"
        )

        phone = self.normalize_phone(
            lead.get("phone")
        )

        maps_url = lead.get(
            "maps_url"
        )

        # ==================================================
        # LEVEL 1: GOOGLE MAPS URL
        # ==================================================

        if maps_url:

            existing = self.collection.find_one(
                {
                    "maps_url": maps_url
                }
            )

            if existing:
                return existing

        # ==================================================
        # LEVEL 2: PHONE
        # ==================================================

        if phone:

            existing_leads = self.collection.find(
                {
                    "phone": phone
                }
            )

            for existing in existing_leads:

                existing_phone = self.normalize_phone(
                    existing.get("phone")
                )

                if existing_phone == phone:

                    return existing

        # ==================================================
        # LEVEL 3: BUSINESS NAME + CITY
        # ==================================================

        if business_name and city:

            normalized_name = (
                self.normalize_business_name(
                    business_name
                )
            )

            existing_leads = self.collection.find(
                {
                    "city": city
                }
            )

            for existing in existing_leads:

                existing_name = (
                    self.normalize_business_name(
                        existing.get(
                            "business_name"
                        )
                    )
                )

                if (
                    normalized_name
                    and
                    normalized_name == existing_name
                ):

                    return existing

        return None

    # ==================================================
    # CHECK WHETHER NEW DATA IS BETTER
    # ==================================================

    def has_better_data(
        self,
        existing,
        new_lead
    ):

        fields = [
            "phone",
            "website",
            "address",
            "email",
            "reviews",
            "rating",
            "category",
        ]

        for field in fields:

            old_value = existing.get(
                field
            )

            new_value = new_lead.get(
                field
            )

            if (
                not old_value
                and new_value
            ):

                return True

        return False

    # ==================================================
    # MERGE LEAD DATA
    # ==================================================

    def merge_leads(
        self,
        existing,
        new_lead
    ):

        merged = existing.copy()

        fields = [
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
            "status",
            "assigned_to",
            "notes",
        ]

        for field in fields:

            new_value = new_lead.get(
                field
            )

            old_value = existing.get(
                field
            )

            if new_value:
                merged[field] = new_value

            elif old_value:
                merged[field] = old_value

        return merged

    # ==================================================
    # SAVE LEADS
    # ==================================================

    def save_leads(
        self,
        leads
    ):

        new_count = 0
        duplicate_count = 0
        updated_count = 0

        operations = []

        for lead in leads:

            business_name = lead.get(
                "business_name"
            )

            # ==================================================
            # FIND EXISTING LEAD
            # ==================================================

            existing_lead = (
                self.find_existing_lead(
                    lead
                )
            )

            # ==================================================
            # NEW LEAD
            # ==================================================

            if not existing_lead:

                # ----------------------------------------------
                # MAPS URL AVAILABLE
                # ----------------------------------------------

                if lead.get("maps_url"):

                    operations.append(
                        UpdateOne(
                            {
                                "maps_url":
                                    lead.get(
                                        "maps_url"
                                    )
                            },
                            {
                                "$set":
                                    lead
                            },
                            upsert=True
                        )
                    )

                # ----------------------------------------------
                # NO MAPS URL
                # ----------------------------------------------

                else:

                    operations.append(
                        UpdateOne(
                            {
                                "business_name":
                                    lead.get(
                                        "business_name"
                                    ),
                                "city":
                                    lead.get(
                                        "city"
                                    )
                            },
                            {
                                "$set":
                                    lead
                            },
                            upsert=True
                        )
                    )

                new_count += 1

                print(
                    f"New lead: {business_name}"
                )

                continue

            # ==================================================
            # EXISTING LEAD
            # ==================================================

            if self.has_better_data(
                existing_lead,
                lead
            ):

                merged_lead = (
                    self.merge_leads(
                        existing_lead,
                        lead
                    )
                )

                operations.append(
                    UpdateOne(
                        {
                            "_id":
                                existing_lead[
                                    "_id"
                                ]
                        },
                        {
                            "$set":
                                merged_lead
                        }
                    )
                )

                updated_count += 1

                print(
                    f"Lead updated: {business_name}"
                )

            # ==================================================
            # DUPLICATE
            # ==================================================

            else:

                duplicate_count += 1

                print(
                    f"Duplicate skipped: "
                    f"{business_name}"
                )

        # ==================================================
        # EXECUTE OPERATIONS
        # ==================================================

        if operations:

            self.collection.bulk_write(
                operations
            )

        # ==================================================
        # RESULT
        # ==================================================

        print(
            f"{new_count} new leads saved to MongoDB"
        )

        print(
            f"{updated_count} leads updated"
        )

        print(
            f"{duplicate_count} duplicate leads skipped"
        )

    # ==================================================
    # GET ALL LEADS
    # ==================================================

    def get_all(self):

        return list(
            self.collection.find()
        )

    # ==================================================
    # CLOSE CONNECTION
    # ==================================================

    def close(self):

        self.client.close()
