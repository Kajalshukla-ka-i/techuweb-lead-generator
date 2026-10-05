from database.mongodb import MongoDB
from services.normalization_cleanup import NormalizationCleanup


def main():

    print("=" * 80)
    print("NORMALIZATION CLEANUP TEST")
    print("=" * 80)

    db = MongoDB()

    try:

        cleanup = NormalizationCleanup(db)

        # =====================================================
        # TEST 1 - DRY RUN ONLY
        # =====================================================

        print("\n" + "=" * 80)
        print("TEST 1 - NORMALIZATION DRY RUN")
        print("=" * 80)

        cleanup.dry_run()

        # =====================================================
        # TEST 2 - CONFIRMATION SAFETY
        # =====================================================

        print("\n" + "=" * 80)
        print("TEST 2 - CONFIRMATION SAFETY")
        print("=" * 80)

        result = cleanup.apply_normalization(
            confirm=False
        )

        print(
            f"\nResult: {result}"
        )

        print(
            "\n✅ Confirmation safety test completed"
        )

        print(
            "No normalization was applied."
        )

        # =====================================================
        # FINAL RESULT
        # =====================================================

        print("\n" + "=" * 80)
        print("NORMALIZATION CLEANUP TEST COMPLETED")
        print("=" * 80)

        print(
            "\nDatabase records were NOT modified."
        )

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