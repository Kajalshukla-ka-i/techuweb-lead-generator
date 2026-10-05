from database.mongodb import MongoDB
from services.lead_normalizer import LeadNormalizer


class LeadCleanup:

    def __init__(self, db):
        self.db = db
        self.collection = db.collection
        self.normalizer = LeadNormalizer(db)

    # =========================================================
    # LOAD LEADS
    # =========================================================

    def get_leads(self):
        return list(
            self.collection.find({})
        )

    # =========================================================
    # PREPARE NORMALIZED LEAD
    # =========================================================

    def prepare_normalized_lead(self, lead):

        normalized = lead.copy()

        normalized["website"] = (
            self.normalizer.normalize_website(
                lead.get("website")
            )
        )

        normalized["phone"] = (
            self.normalizer.normalize_phone(
                lead.get("phone")
            )
        )

        text_fields = [
            "business_name",
            "category",
            "city",
            "state",
            "address",
            "email",
            "keyword",
            "status",
            "source"
        ]

        for field in text_fields:

            normalized[field] = (
                self.normalizer.normalize_text(
                    lead.get(field)
                )
            )

        # Data quality
        quality = (
            self.normalizer.calculate_data_quality(
                normalized
            )
        )

        normalized["missing_fields"] = (
            quality["missing_fields"]
        )

        normalized["data_status"] = (
            quality["data_status"]
        )

        # Phone validation
        phone = normalized["phone"]

        normalized["valid_phone"] = (
            True
            if 10 <= len(phone) <= 12
            else False
        )

        # Lead score
        normalized["lead_score"] = (
            self.normalizer.calculate_lead_score(
                normalized
            )
        )

        # Opportunity
        normalized["opportunity"] = (
            self.normalizer.calculate_opportunity(
                normalized["lead_score"],
                normalized["website"]
            )
        )

        return normalized

    # =========================================================
    # DUPLICATE GROUPING
    # =========================================================

    def build_duplicate_groups(self, leads):

        groups = {}

        for lead in leads:

            business_name = (
                self.normalizer.normalize_text(
                    lead.get("business_name")
                ).lower()
            )

            city = (
                self.normalizer.normalize_text(
                    lead.get("city")
                ).lower()
            )

            if not business_name or not city:
                continue

            key = (
                business_name,
                city
            )

            if key not in groups:
                groups[key] = []

            groups[key].append(lead)

        duplicate_groups = []

        for key, group in groups.items():

            if len(group) > 1:

                duplicate_groups.append(group)

        return duplicate_groups

    # =========================================================
    # DUPLICATE SAFETY CHECK
    # =========================================================

    def can_auto_merge(self, lead_a, lead_b):

        name_a = (
            self.normalizer.normalize_text(
                lead_a.get("business_name")
            ).lower()
        )

        name_b = (
            self.normalizer.normalize_text(
                lead_b.get("business_name")
            ).lower()
        )

        city_a = (
            self.normalizer.normalize_text(
                lead_a.get("city")
            ).lower()
        )

        city_b = (
            self.normalizer.normalize_text(
                lead_b.get("city")
            ).lower()
        )

        phone_a = (
            self.normalizer.normalize_phone(
                lead_a.get("phone")
            )
        )

        phone_b = (
            self.normalizer.normalize_phone(
                lead_b.get("phone")
            )
        )

        address_a = (
            self.normalizer.normalize_text(
                lead_a.get("address")
            ).lower()
        )

        address_b = (
            self.normalizer.normalize_text(
                lead_b.get("address")
            ).lower()
        )

        maps_a = (
            self.normalizer.normalize_text(
                lead_a.get("maps_url")
            )
        )

        maps_b = (
            self.normalizer.normalize_text(
                lead_b.get("maps_url")
            )
        )

        # Must have same business + city
        if not (
            name_a
            and name_b
            and name_a == name_b
            and city_a
            and city_a == city_b
        ):
            return False, "Different business or city"

        # Strong duplicate signal:
        # Same Maps URL
        if (
            maps_a
            and maps_b
            and maps_a == maps_b
        ):
            return True, "Same Maps URL"

        # Strong duplicate signal:
        # Same phone
        if (
            phone_a
            and phone_b
            and phone_a == phone_b
        ):
            return True, "Same phone number"

        # Strong duplicate signal:
        # Same address
        if (
            address_a
            and address_b
            and address_a == address_b
        ):
            return True, "Same address"

        # Same name + city but no strong identifier
        return False, (
            "Same name and city, "
            "but insufficient evidence"
        )

    # =========================================================
    # MERGE LEADS
    # =========================================================

    def merge_leads(self, lead_a, lead_b):

        merged = lead_a.copy()

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
            "notes"
        ]

        for field in fields:

            value_a = lead_a.get(field)
            value_b = lead_b.get(field)

            # Missing in A -> use B
            if not value_a and value_b:
                merged[field] = value_b

        return merged

    # =========================================================
    # DRY RUN
    # =========================================================

    def dry_run(self):

        leads = self.get_leads()

        print("=" * 80)
        print("TECHUWEB LEAD CLEANUP - DRY RUN")
        print("=" * 80)

        print(
            f"\nTotal database records: "
            f"{len(leads)}"
        )

        # -----------------------------------------------------
        # NORMALIZATION
        # -----------------------------------------------------

        print("\n" + "=" * 80)
        print("NORMALIZATION PREVIEW")
        print("=" * 80)

        normalization_count = 0

        for index, lead in enumerate(
            leads,
            start=1
        ):

            normalized = (
                self.prepare_normalized_lead(
                    lead
                )
            )

            changes = []

            fields = [
                "website",
                "phone",
                "email",
                "address",
                "missing_fields",
                "data_status",
                "valid_phone",
                "lead_score",
                "opportunity"
            ]

            for field in fields:

                old_value = lead.get(field)
                new_value = normalized.get(field)

                if old_value != new_value:

                    changes.append(
                        (
                            field,
                            old_value,
                            new_value
                        )
                    )

            if changes:

                normalization_count += 1

                print(
                    f"\nLead {index}: "
                    f"{lead.get('business_name')}"
                )

                for field, old, new in changes:

                    print(
                        f"  {field}: "
                        f"{old!r} -> {new!r}"
                    )

        print(
            f"\nRecords requiring updates: "
            f"{normalization_count}"
        )

        # -----------------------------------------------------
        # DUPLICATES
        # -----------------------------------------------------

        print("\n" + "=" * 80)
        print("DUPLICATE MERGE SAFETY ANALYSIS")
        print("=" * 80)

        duplicate_groups = (
            self.build_duplicate_groups(
                leads
            )
        )

        auto_merge_count = 0
        review_count = 0

        print(
            f"\nDuplicate groups found: "
            f"{len(duplicate_groups)}"
        )

        for group_index, group in enumerate(
            duplicate_groups,
            start=1
        ):

            print(
                f"\nDuplicate Group {group_index}"
            )

            for lead_index, lead in enumerate(
                group,
                start=1
            ):

                print(
                    f"  Lead {lead_index}: "
                    f"{lead.get('business_name')}"
                )

                print(
                    f"    Phone   : "
                    f"{lead.get('phone')}"
                )

                print(
                    f"    Address : "
                    f"{lead.get('address')}"
                )

                print(
                    f"    Maps URL: "
                    f"{lead.get('maps_url')}"
                )

            # Compare first lead with others
            base_lead = group[0]

            for other_lead in group[1:]:

                safe, reason = (
                    self.can_auto_merge(
                        base_lead,
                        other_lead
                    )
                )

                if safe:

                    auto_merge_count += 1

                    print(
                        f"  ✅ AUTO-MERGE CANDIDATE"
                    )

                    print(
                        f"     Reason: "
                        f"{reason}"
                    )

                else:

                    review_count += 1

                    print(
                        f"  ⚠️ MANUAL REVIEW REQUIRED"
                    )

                    print(
                        f"     Reason: "
                        f"{reason}"
                    )

        # -----------------------------------------------------
        # SUMMARY
        # -----------------------------------------------------

        print("\n" + "=" * 80)
        print("CLEANUP DRY RUN SUMMARY")
        print("=" * 80)

        print(
            f"\nTotal records              : "
            f"{len(leads)}"
        )

        print(
            f"Records requiring updates : "
            f"{normalization_count}"
        )

        print(
            f"Duplicate groups           : "
            f"{len(duplicate_groups)}"
        )

        print(
            f"Auto-merge candidates      : "
            f"{auto_merge_count}"
        )

        print(
            f"Manual review required     : "
            f"{review_count}"
        )

        print("\n" + "=" * 80)

        print(
            "⚠️ DRY RUN ONLY"
        )

        print(
            "⚠️ NO DATABASE RECORDS WERE MODIFIED."
        )

        print(
            "⚠️ NO RECORDS WERE DELETED."
        )

        print(
            "⚠️ NO RECORDS WERE MERGED."
        )

        print("=" * 80)


def main():

    db = MongoDB()

    try:

        cleanup = LeadCleanup(db)

        cleanup.dry_run()

    except Exception as e:

        print("\n❌ CLEANUP ERROR")

        print(
            f"{type(e).__name__}: {e}"
        )

    finally:

        db.close()

        print(
            "\nMongoDB Connection Closed"
        )


if __name__ == "__main__":
    main()