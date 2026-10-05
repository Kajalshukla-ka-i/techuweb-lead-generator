from pathlib import Path
from datetime import datetime
from pymongo import UpdateOne

from database.mongodb import MongoDB
from services.lead_normalizer import LeadNormalizer


class SafeNormalizationApply:
    """
    SAFE NORMALIZATION APPLY

    Purpose:
        Apply only explicitly approved, low-risk normalization changes.

    SAFETY RULES:
        - Backup before modification
        - No deletion
        - No merging
        - No lead_score modification
        - No opportunity modification
        - No created_at modification
        - No updated_at modification
        - No website modification
        - No missing_fields modification
        - No data_status modification
        - No valid_phone modification

    Approved changes:
        - email: None -> ""
        - maps_url: None -> ""
        - phone: None -> ""
        - whitespace-only cleanup for selected text fields
    """

    PROTECTED_FIELDS = {
        "lead_score",
        "opportunity",
        "created_at",
        "updated_at",
        "website",
        "missing_fields",
        "data_status",
        "valid_phone",
    }

    TEXT_FIELDS = {
        "business_name",
        "category",
        "city",
        "state",
        "keyword",
        "source",
        "status",
        "email",
        "address",
        "maps_url",
        "notes",
    }

    SAFE_NONE_TO_EMPTY = {
        "email",
        "maps_url",
        "phone",
    }

    def __init__(self, db):
        self.db = db
        self.collection = db.collection
        self.normalizer = LeadNormalizer(db)

    # =========================================================
    # BACKUP
    # =========================================================

    def create_backup(self, leads):
        backup_directory = (
            Path("output")
            / "backup"
        )

        backup_directory.mkdir(
            parents=True,
            exist_ok=True
        )

        timestamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )

        backup_path = (
            backup_directory
            / f"leads_before_safe_normalization_{timestamp}.json"
        )

        import json

        backup_data = []

        for lead in leads:
            record = dict(lead)

            if "_id" in record:
                record["_id"] = str(record["_id"])

            for field in [
                "created_at",
                "updated_at",
            ]:
                if field in record:
                    value = record[field]

                    if hasattr(value, "isoformat"):
                        record[field] = value.isoformat()
                    else:
                        record[field] = str(value)

            backup_data.append(record)

        with open(
            backup_path,
            "w",
            encoding="utf-8"
        ) as file:
            json.dump(
                backup_data,
                file,
                indent=4,
                ensure_ascii=False,
                default=str
            )

        return backup_path

    # =========================================================
    # SAFE CHANGE DETECTION
    # =========================================================

    def get_safe_changes(self, lead):
        changes = {}

        # -----------------------------------------------------
        # EMAIL
        # -----------------------------------------------------

        email = lead.get("email")

        if email is None:
            changes["email"] = ""

        elif (
            isinstance(email, str)
            and email != email.strip()
        ):
            changes["email"] = email.strip()

        # -----------------------------------------------------
        # MAPS URL
        # -----------------------------------------------------

        maps_url = lead.get("maps_url")

        if maps_url is None:
            changes["maps_url"] = ""

        elif (
            isinstance(maps_url, str)
            and maps_url != maps_url.strip()
        ):
            changes["maps_url"] = maps_url.strip()

        # -----------------------------------------------------
        # PHONE
        # -----------------------------------------------------

        phone = lead.get("phone")

        if phone is None:
            changes["phone"] = ""

        # -----------------------------------------------------
        # SAFE TEXT WHITESPACE
        # -----------------------------------------------------

        for field in {
            "business_name",
            "category",
            "city",
            "state",
            "keyword",
            "source",
            "status",
            "address",
            "notes",
        }:

            if field not in lead:
                continue

            value = lead.get(field)

            if (
                isinstance(value, str)
                and value != value.strip()
            ):
                changes[field] = value.strip()

        return changes

    # =========================================================
    # SAFETY CHECK
    # =========================================================

    def validate_changes(self, changes):
        for field in changes:

            if field in self.PROTECTED_FIELDS:
                raise RuntimeError(
                    f"PROTECTED FIELD CHANGE DETECTED: {field}"
                )

        return True

    # =========================================================
    # APPLY
    # =========================================================

    def apply_changes(self, leads):
        operations = []
        change_log = []

        for lead in leads:

            lead_id = lead.get("_id")

            if lead_id is None:
                continue

            changes = self.get_safe_changes(lead)

            if not changes:
                continue

            self.validate_changes(changes)

            operations.append(
                UpdateOne(
                    {"_id": lead_id},
                    {
                        "$set": changes
                    }
                )
            )

            change_log.append(
                {
                    "id": str(lead_id),
                    "business_name": lead.get(
                        "business_name",
                        ""
                    ),
                    "city": lead.get(
                        "city",
                        ""
                    ),
                    "changes": changes,
                }
            )

        if not operations:
            return {
                "modified_count": 0,
                "matched_count": 0,
                "change_log": [],
            }

        result = self.collection.bulk_write(
            operations,
            ordered=True
        )

        return {
            "modified_count": result.modified_count,
            "matched_count": result.matched_count,
            "change_log": change_log,
        }

    # =========================================================
    # VERIFY
    # =========================================================

    def verify_database(
        self,
        before_count,
        protected_snapshot
    ):
        after_count = self.collection.count_documents({})

        if before_count != after_count:
            raise RuntimeError(
                "DATABASE COUNT CHANGED! "
                f"Before={before_count}, "
                f"After={after_count}"
            )

        for lead_id, expected in protected_snapshot.items():

            current = self.collection.find_one(
                {"_id": lead_id}
            )

            if current is None:
                raise RuntimeError(
                    f"LEAD DISAPPEARED: {lead_id}"
                )

            for field, expected_value in expected.items():

                current_value = current.get(field)

                if current_value != expected_value:
                    raise RuntimeError(
                        "PROTECTED FIELD CHANGED: "
                        f"{field} "
                        f"for lead {lead_id}"
                    )

        return True

    # =========================================================
    # REPORT
    # =========================================================

    def save_report(
        self,
        backup_path,
        before_count,
        result
    ):
        report_directory = (
            Path("output")
            / "cleanup_reports"
        )

        report_directory.mkdir(
            parents=True,
            exist_ok=True
        )

        timestamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )

        report_path = (
            report_directory
            / f"safe_normalization_apply_{timestamp}.txt"
        )

        with open(
            report_path,
            "w",
            encoding="utf-8"
        ) as file:

            file.write(
                "TECHUWEB LEAD GENERATOR\n"
            )
            file.write(
                "SAFE NORMALIZATION APPLY REPORT\n"
            )
            file.write(
                "=" * 75 + "\n\n"
            )

            file.write(
                "MODE : SAFE APPLY\n"
            )
            file.write(
                "DELETE : DISABLED\n"
            )
            file.write(
                "MERGE : DISABLED\n"
            )
            file.write(
                "LEAD SCORE OVERWRITE : DISABLED\n"
            )
            file.write(
                "OPPORTUNITY OVERWRITE : DISABLED\n"
            )
            file.write(
                "WEBSITE OVERWRITE : DISABLED\n\n"
            )

            file.write(
                f"Backup : {backup_path}\n"
            )

            file.write(
                f"Records before : {before_count}\n"
            )

            file.write(
                f"Records matched : "
                f"{result['matched_count']}\n"
            )

            file.write(
                f"Records modified : "
                f"{result['modified_count']}\n\n"
            )

            file.write(
                "=" * 75 + "\n"
            )
            file.write(
                "CHANGE LOG\n"
            )
            file.write(
                "=" * 75 + "\n\n"
            )

            for item in result["change_log"]:

                file.write(
                    f"Business : "
                    f"{item['business_name']}\n"
                )

                file.write(
                    f"City : "
                    f"{item['city']}\n"
                )

                file.write(
                    f"ID : "
                    f"{item['id']}\n"
                )

                file.write(
                    f"Changes : "
                    f"{item['changes']}\n"
                )

                file.write(
                    "-" * 75 + "\n"
                )

        return report_path


# =============================================================
# MAIN
# =============================================================

def main():

    print()
    print("=" * 75)
    print("TECHUWEB LEAD GENERATOR")
    print("SAFE NORMALIZATION APPLY")
    print("=" * 75)

    print()
    print("IMPORTANT:")
    print("This operation will modify MongoDB.")
    print("A backup will be created first.")
    print()
    print("Protected fields:")
    print("  lead_score")
    print("  opportunity")
    print("  website")
    print("  missing_fields")
    print("  data_status")
    print("  valid_phone")
    print("  created_at")
    print("  updated_at")

    print()
    confirmation = input(
        "Type APPLY_SAFE_NORMALIZATION to continue: "
    ).strip()

    if confirmation != "APPLY_SAFE_NORMALIZATION":
        print()
        print("Operation cancelled.")
        print("MongoDB was NOT modified.")
        return

    db = None

    try:

        db = MongoDB()

        cleanup = SafeNormalizationApply(db)

        # -----------------------------------------------------
        # LOAD
        # -----------------------------------------------------

        print()
        print("=" * 75)
        print("LOADING MONGODB")
        print("=" * 75)

        leads = list(
            cleanup.collection.find({})
        )

        before_count = len(leads)

        print(
            f"Records loaded : {before_count}"
        )

        # -----------------------------------------------------
        # SNAPSHOT PROTECTED FIELDS
        # -----------------------------------------------------

        protected_snapshot = {}

        for lead in leads:

            lead_id = lead.get("_id")

            protected_snapshot[lead_id] = {
                "lead_score": lead.get(
                    "lead_score"
                ),
                "opportunity": lead.get(
                    "opportunity"
                ),
                "website": lead.get(
                    "website"
                ),
                "missing_fields": lead.get(
                    "missing_fields"
                ),
                "data_status": lead.get(
                    "data_status"
                ),
                "valid_phone": lead.get(
                    "valid_phone"
                ),
                "created_at": lead.get(
                    "created_at"
                ),
                "updated_at": lead.get(
                    "updated_at"
                ),
            }

        # -----------------------------------------------------
        # BACKUP
        # -----------------------------------------------------

        print()
        print("=" * 75)
        print("CREATING BACKUP")
        print("=" * 75)

        backup_path = cleanup.create_backup(
            leads
        )

        print(
            f"Backup created : {backup_path}"
        )

        # -----------------------------------------------------
        # APPLY
        # -----------------------------------------------------

        print()
        print("=" * 75)
        print("APPLYING SAFE NORMALIZATION")
        print("=" * 75)

        result = cleanup.apply_changes(
            leads
        )

        print(
            f"Matched records  : "
            f"{result['matched_count']}"
        )

        print(
            f"Modified records : "
            f"{result['modified_count']}"
        )

        # -----------------------------------------------------
        # VERIFY
        # -----------------------------------------------------

        print()
        print("=" * 75)
        print("VERIFYING DATABASE")
        print("=" * 75)

        cleanup.verify_database(
            before_count,
            protected_snapshot
        )

        print(
            "Record count verified."
        )

        print(
            "Protected fields verified."
        )

        # -----------------------------------------------------
        # REPORT
        # -----------------------------------------------------

        report_path = cleanup.save_report(
            backup_path,
            before_count,
            result
        )

        print()
        print("=" * 75)
        print("SAFE NORMALIZATION COMPLETED")
        print("=" * 75)

        print(
            f"Backup : {backup_path}"
        )

        print(
            f"Report : {report_path}"
        )

        print()
        print(
            "MongoDB changes were limited "
            "to approved safe normalization."
        )

        print(
            "lead_score was preserved."
        )

        print(
            "opportunity was preserved."
        )

        print(
            "website was preserved."
        )

    except Exception as error:

        print()
        print("=" * 75)
        print("SAFE NORMALIZATION ERROR")
        print("=" * 75)

        print(
            f"Error : {error}"
        )

        print()
        print(
            "IMPORTANT: Review the backup before "
            "attempting another database operation."
        )

        raise

    finally:

        if db is not None:

            try:
                db.close()

                print()
                print(
                    "MongoDB connection closed."
                )

            except Exception as error:

                print(
                    f"MongoDB close warning: "
                    f"{error}"
                )


if __name__ == "__main__":
    main()