from database.mongodb import MongoDB
from services.lead_cleanup import LeadCleanup
from services.cleanup_backup import CleanupBackup


def main():

    print("=" * 80)
    print("BACKUP AND CLEANUP REPORT TEST")
    print("=" * 80)

    db = MongoDB()

    try:

        cleanup = LeadCleanup(db)
        backup = CleanupBackup(db)

        # =====================================================
        # TEST 1 - ANALYZE CURRENT DATABASE
        # =====================================================

        print("\n" + "=" * 80)
        print("TEST 1 - CLEANUP ANALYSIS")
        print("=" * 80)

        leads = cleanup.get_leads()

        duplicate_groups = (
            cleanup.build_duplicate_groups(
                leads
            )
        )

        normalization_count = 0

        for lead in leads:

            normalized = (
                cleanup.prepare_normalized_lead(
                    lead
                )
            )

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

            changes_found = False

            for field in fields:

                if (
                    lead.get(field)
                    != normalized.get(field)
                ):

                    changes_found = True
                    break

            if changes_found:
                normalization_count += 1

        auto_merge_count = 0
        review_count = 0

        for group in duplicate_groups:

            base_lead = group[0]

            for other_lead in group[1:]:

                safe, reason = (
                    cleanup.can_auto_merge(
                        base_lead,
                        other_lead
                    )
                )

                if safe:
                    auto_merge_count += 1
                else:
                    review_count += 1

        print(
            f"\nTotal records: "
            f"{len(leads)}"
        )

        print(
            f"Normalization updates: "
            f"{normalization_count}"
        )

        print(
            f"Duplicate groups: "
            f"{len(duplicate_groups)}"
        )

        print(
            f"Auto-merge candidates: "
            f"{auto_merge_count}"
        )

        print(
            f"Manual review required: "
            f"{review_count}"
        )

        # =====================================================
        # TEST 2 - CREATE BACKUP
        # =====================================================

        print("\n" + "=" * 80)
        print("TEST 2 - CREATE DATABASE BACKUP")
        print("=" * 80)

        backup_file = (
            backup.create_backup()
        )

        # =====================================================
        # TEST 3 - CREATE REPORT
        # =====================================================

        print("\n" + "=" * 80)
        print("TEST 3 - CREATE CLEANUP REPORT")
        print("=" * 80)

        report_file = (
            backup.create_cleanup_report(
                total_records=len(leads),
                normalization_count=(
                    normalization_count
                ),
                duplicate_groups=(
                    len(duplicate_groups)
                ),
                auto_merge_count=(
                    auto_merge_count
                ),
                review_count=(
                    review_count
                )
            )
        )

        # =====================================================
        # FINAL RESULT
        # =====================================================

        print("\n" + "=" * 80)
        print("BACKUP AND REPORT TEST COMPLETED")
        print("=" * 80)

        print(
            f"\nBackup created:"
            f"\n{backup_file}"
        )

        print(
            f"\nReport created:"
            f"\n{report_file}"
        )

        print(
            "\nDatabase records were NOT modified."
        )

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