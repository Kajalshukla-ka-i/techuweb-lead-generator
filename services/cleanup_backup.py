import os
import json
from datetime import datetime


class CleanupBackup:

    def __init__(self, db):
        self.db = db
        self.collection = db.collection

    # =========================================================
    # CREATE DATABASE BACKUP
    # =========================================================

    def create_backup(self):

        leads = list(
            self.collection.find({})
        )

        timestamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )

        backup_directory = os.path.join(
            "output",
            "backup"
        )

        os.makedirs(
            backup_directory,
            exist_ok=True
        )

        backup_file = os.path.join(
            backup_directory,
            f"leads_backup_{timestamp}.json"
        )

        # Convert MongoDB-specific values
        # into JSON-compatible values.
        for lead in leads:

            if "_id" in lead:
                lead["_id"] = str(
                    lead["_id"]
                )

            for key, value in list(
                lead.items()
            ):

                if isinstance(
                    value,
                    datetime
                ):
                    lead[key] = value.isoformat()

        with open(
            backup_file,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                leads,
                file,
                indent=4,
                ensure_ascii=False
            )

        print("\n" + "=" * 80)
        print("DATABASE BACKUP CREATED")
        print("=" * 80)

        print(
            f"\nRecords backed up: {len(leads)}"
        )

        print(
            f"Backup file: {backup_file}"
        )

        return backup_file

    # =========================================================
    # CREATE CLEANUP REPORT
    # =========================================================

    def create_cleanup_report(
        self,
        total_records,
        normalization_count,
        duplicate_groups,
        auto_merge_count,
        review_count
    ):

        timestamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )

        report_directory = os.path.join(
            "output",
            "cleanup_reports"
        )

        os.makedirs(
            report_directory,
            exist_ok=True
        )

        report_file = os.path.join(
            report_directory,
            f"cleanup_report_{timestamp}.txt"
        )

        report = []

        report.append("=" * 80)
        report.append(
            "TECHUWEB LEAD CLEANUP REPORT"
        )
        report.append("=" * 80)

        report.append(
            f"\nGenerated at: "
            f"{datetime.now().isoformat()}"
        )

        report.append(
            f"\nTotal records: {total_records}"
        )

        report.append(
            f"Records requiring normalization: "
            f"{normalization_count}"
        )

        report.append(
            f"Duplicate groups: "
            f"{duplicate_groups}"
        )

        report.append(
            f"Auto-merge candidates: "
            f"{auto_merge_count}"
        )

        report.append(
            f"Manual review required: "
            f"{review_count}"
        )

        report.append("\n" + "=" * 80)
        report.append("SAFETY STATUS")
        report.append("=" * 80)

        report.append(
            "\nThis report was generated in dry-run mode."
        )

        report.append(
            "No records were modified."
        )

        report.append(
            "No records were deleted."
        )

        report.append(
            "No records were merged."
        )

        report.append("\n" + "=" * 80)

        with open(
            report_file,
            "w",
            encoding="utf-8"
        ) as file:

            file.write(
                "\n".join(report)
            )

        print("\n" + "=" * 80)
        print("CLEANUP REPORT CREATED")
        print("=" * 80)

        print(
            f"\nReport file: {report_file}"
        )

        return report_file