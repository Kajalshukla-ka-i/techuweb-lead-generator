from database.mongodb import MongoDB
from services.lead_normalizer import LeadNormalizer


def main():

    print("=" * 80)
    print("LEAD NORMALIZER TEST")
    print("=" * 80)

    db = MongoDB()

    try:

        normalizer = LeadNormalizer(db)

        # =====================================================
        # TEST 1 - WEBSITE
        # =====================================================

        print("\n" + "=" * 80)
        print("TEST 1 - WEBSITE NORMALIZATION")
        print("=" * 80)

        website_values = [
            None,
            "",
            False,
            True,
            "https://example.com",
            "  https://example.com  "
        ]

        for value in website_values:

            result = normalizer.normalize_website(
                value
            )

            print(
                f"{value!r:35} -> {result!r}"
            )

        # =====================================================
        # TEST 2 - PHONE
        # =====================================================

        print("\n" + "=" * 80)
        print("TEST 2 - PHONE NORMALIZATION")
        print("=" * 80)

        phone_values = [
            None,
            "",
            False,
            "9876543210",
            "+91 98765 43210",
            "09876543210"
        ]

        for value in phone_values:

            result = normalizer.normalize_phone(
                value
            )

            print(
                f"{value!r:35} -> {result!r}"
            )

        # =====================================================
        # TEST 3 - DATA QUALITY
        # =====================================================

        print("\n" + "=" * 80)
        print("TEST 3 - DATA QUALITY")
        print("=" * 80)

        test_lead = {
            "business_name": "Test Clinic",
            "category": "Dental Clinic",
            "city": "Noida",
            "phone": "",
            "website": "",
            "address": ""
        }

        quality = normalizer.calculate_data_quality(
            test_lead
        )

        print(
            f"Missing Fields : "
            f"{quality['missing_fields']}"
        )

        print(
            f"Data Status    : "
            f"{quality['data_status']}"
        )

        # =====================================================
        # TEST 4 - LEAD SCORE
        # =====================================================

        print("\n" + "=" * 80)
        print("TEST 4 - LEAD SCORE")
        print("=" * 80)

        test_lead = {
            "rating": "4.8",
            "reviews": "500",
            "phone": "9876543210",
            "website": "",
            "address": "Noida"
        }

        score = normalizer.calculate_lead_score(
            test_lead
        )

        opportunity = normalizer.calculate_opportunity(
            score,
            test_lead["website"]
        )

        print(
            f"Lead Score : {score}"
        )

        print(
            f"Opportunity: {opportunity}"
        )

        # =====================================================
        # TEST 5 - DUPLICATE DETECTION
        # =====================================================

        print("\n" + "=" * 80)
        print("TEST 5 - DUPLICATE DETECTION")
        print("=" * 80)

        test_leads = [
            {
                "business_name": "Test Salon",
                "city": "Noida",
                "phone": "",
                "address": "Sector 18"
            },
            {
                "business_name": "Test Salon",
                "city": "Noida",
                "phone": "",
                "address": "Sector 18"
            },
            {
                "business_name": "Different Salon",
                "city": "Noida",
                "phone": "",
                "address": "Sector 18"
            }
        ]

        duplicates = (
            normalizer.find_duplicate_candidates(
                test_leads
            )
        )

        print(
            f"Duplicate Candidates: "
            f"{len(duplicates)}"
        )

        for duplicate in duplicates:

            print(
                f"  {duplicate['lead_1']} "
                f"<-> "
                f"{duplicate['lead_2']}"
            )

            print(
                f"  Reason: "
                f"{', '.join(duplicate['reasons'])}"
            )

        # =====================================================
        # TEST 6 - REAL DATABASE DRY RUN
        # =====================================================

        print("\n" + "=" * 80)
        print("TEST 6 - REAL DATABASE DRY RUN")
        print("=" * 80)

        normalizer.dry_run()

        # =====================================================
        # COMPLETE
        # =====================================================

        print("\n" + "=" * 80)
        print("ALL NORMALIZER TESTS COMPLETED")
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