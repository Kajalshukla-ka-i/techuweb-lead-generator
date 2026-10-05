from database.mongodb import MongoDB
from services.lead_cleanup import LeadCleanup


def main():

    print("=" * 80)
    print("LEAD CLEANUP TEST")
    print("=" * 80)

    db = MongoDB()

    try:

        cleanup = LeadCleanup(db)

        # =====================================================
        # TEST 1 - NORMALIZATION
        # =====================================================

        print("\n" + "=" * 80)
        print("TEST 1 - NORMALIZED LEAD")
        print("=" * 80)

        test_lead = {
            "business_name": "Test Salon",
            "category": "Salon",
            "city": "Noida",
            "phone": None,
            "website": False,
            "email": None,
            "address": "",
            "rating": "4.8",
            "reviews": "500"
        }

        normalized = (
            cleanup.prepare_normalized_lead(
                test_lead
            )
        )

        print(
            f"Website      : "
            f"{normalized.get('website')!r}"
        )

        print(
            f"Phone        : "
            f"{normalized.get('phone')!r}"
        )

        print(
            f"Data Status  : "
            f"{normalized.get('data_status')}"
        )

        print(
            f"Missing      : "
            f"{normalized.get('missing_fields')}"
        )

        print(
            f"Valid Phone  : "
            f"{normalized.get('valid_phone')}"
        )

        print(
            f"Lead Score   : "
            f"{normalized.get('lead_score')}"
        )

        print(
            f"Opportunity  : "
            f"{normalized.get('opportunity')}"
        )

        # =====================================================
        # TEST 2 - SAFE DUPLICATE
        # =====================================================

        print("\n" + "=" * 80)
        print("TEST 2 - SAFE DUPLICATE")
        print("=" * 80)

        lead_a = {
            "business_name": "Test Salon",
            "city": "Noida",
            "phone": "9876543210",
            "address": "Sector 18",
            "maps_url": ""
        }

        lead_b = {
            "business_name": "Test Salon",
            "city": "Noida",
            "phone": "9876543210",
            "address": "",
            "maps_url": ""
        }

        safe, reason = cleanup.can_auto_merge(
            lead_a,
            lead_b
        )

        print(
            f"Can Auto Merge: {safe}"
        )

        print(
            f"Reason         : {reason}"
        )

        # =====================================================
        # TEST 3 - MANUAL REVIEW
        # =====================================================

        print("\n" + "=" * 80)
        print("TEST 3 - MANUAL REVIEW")
        print("=" * 80)

        lead_a = {
            "business_name": "Lakme Salon",
            "city": "Noida",
            "phone": "",
            "address": "",
            "maps_url": ""
        }

        lead_b = {
            "business_name": "Lakme Salon",
            "city": "Noida",
            "phone": "",
            "address": "",
            "maps_url": ""
        }

        safe, reason = cleanup.can_auto_merge(
            lead_a,
            lead_b
        )

        print(
            f"Can Auto Merge: {safe}"
        )

        print(
            f"Reason         : {reason}"
        )

        # =====================================================
        # TEST 4 - MERGE DATA
        # =====================================================

        print("\n" + "=" * 80)
        print("TEST 4 - MERGE DATA")
        print("=" * 80)

        lead_a = {
            "business_name": "Test Clinic",
            "phone": "",
            "website": "",
            "address": "Sector 18"
        }

        lead_b = {
            "business_name": "Test Clinic",
            "phone": "9876543210",
            "website": "https://example.com",
            "address": ""
        }

        merged = cleanup.merge_leads(
            lead_a,
            lead_b
        )

        print(
            f"Business : "
            f"{merged.get('business_name')}"
        )

        print(
            f"Phone    : "
            f"{merged.get('phone')}"
        )

        print(
            f"Website  : "
            f"{merged.get('website')}"
        )

        print(
            f"Address  : "
            f"{merged.get('address')}"
        )

        # =====================================================
        # TEST 5 - REAL DATABASE DRY RUN
        # =====================================================

        print("\n" + "=" * 80)
        print("TEST 5 - REAL DATABASE CLEANUP DRY RUN")
        print("=" * 80)

        cleanup.dry_run()

        # =====================================================
        # COMPLETE
        # =====================================================

        print("\n" + "=" * 80)
        print("ALL CLEANUP TESTS COMPLETED")
        print("=" * 80)

    except Exception as e:

        print("\n❌ TEST ERROR")

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