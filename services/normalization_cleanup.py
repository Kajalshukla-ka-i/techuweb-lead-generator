from pathlib import Path
from datetime import datetime
from collections import Counter
from database.mongodb import MongoDB
from services.lead_normalizer import LeadNormalizer


class NormalizationCleanup:
    """
    NORMALIZATION PREVIEW V2

    Purpose:
        Safely inspect normalization changes before applying them.

    IMPORTANT:
        This version NEVER writes to MongoDB.

    It:
        - Reads existing records
        - Creates normalized copies in memory
        - Separates SAFE / REVIEW / PRESERVE changes
        - Preserves business-critical existing values
        - Generates a detailed report

    MongoDB operations:
        READ      : YES
        INSERT    : NO
        UPDATE    : NO
        DELETE    : NO
        MERGE     : NO
    """

    # =========================================================
    # INITIALIZATION
    # =========================================================

    def __init__(self, db):
        self.db = db
        self.collection = db.collection
        self.normalizer = LeadNormalizer(db)

    # =========================================================
    # FIELDS THAT MUST BE PRESERVED
    # =========================================================

    PRESERVE_FIELDS = {
        "lead_score",
        "opportunity",
        "created_at",
        "updated_at",
    }

    # =========================================================
    # TEXT FIELDS
    # =========================================================

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

    # =========================================================
    # SAFE NONE -> EMPTY FIELDS
    # =========================================================

    SAFE_EMPTY_FIELDS = {
        "email",
        "maps_url",
    }

    # =========================================================
    # PREPARE PREVIEW
    # =========================================================

    def prepare_preview_lead(self, lead):
        """
        Creates a normalized COPY.

        The original MongoDB document is never changed.
        """

        preview = dict(lead)

        # -----------------------------------------------------
        # BUSINESS / TEXT FIELDS
        # -----------------------------------------------------

        for field in self.TEXT_FIELDS:

            if field not in lead:
                continue

            preview[field] = self.normalizer.normalize_text(
                lead.get(field)
            )

        # -----------------------------------------------------
        # WEBSITE
        # -----------------------------------------------------

        website = lead.get("website")

        # IMPORTANT:
        # Only normalize obvious None / whitespace.
        # Do NOT convert True / False blindly.
        if website is None:
            preview["website"] = ""
        elif isinstance(website, str):
            preview["website"] = website.strip()
        else:
            # Preserve boolean / unexpected values for review.
            preview["website"] = website

        # -----------------------------------------------------
        # PHONE
        # -----------------------------------------------------

        phone = lead.get("phone")

        if phone is None:
            preview["phone"] = ""

        elif isinstance(phone, str):

            # Normalize only string phone values.
            preview["phone"] = self.normalizer.normalize_phone(
                phone
            )

        elif isinstance(phone, (int, float)):

            # Convert numeric phone safely to string.
            phone_string = str(phone)

            # Remove decimal .0 caused by numeric storage.
            if phone_string.endswith(".0"):
                phone_string = phone_string[:-2]

            preview["phone"] = (
                self.normalizer.normalize_phone(
                    phone_string
                )
            )

        else:
            # Unknown type → preserve for manual review.
            preview["phone"] = phone

        # -----------------------------------------------------
        # MISSING FIELDS
        # -----------------------------------------------------

        quality = (
            self.normalizer.calculate_data_quality(
                preview
            )
        )

        preview["missing_fields"] = quality.get(
            "missing_fields",
            []
        )

        # -----------------------------------------------------
        # DATA STATUS
        # -----------------------------------------------------

        preview["data_status"] = quality.get(
            "data_status",
            ""
        )

        # -----------------------------------------------------
        # VALID PHONE
        # -----------------------------------------------------

        phone_value = preview.get(
            "phone",
            ""
        )

        if isinstance(phone_value, str):

            digits = "".join(
                char
                for char in phone_value
                if char.isdigit()
            )

            preview["valid_phone"] = (
                10 <= len(digits) <= 12
            )

        else:

            preview["valid_phone"] = False

        # -----------------------------------------------------
        # IMPORTANT:
        # DO NOT RECALCULATE LEAD SCORE
        # DO NOT RECALCULATE OPPORTUNITY
        # -----------------------------------------------------

        if "lead_score" in lead:
            preview["lead_score"] = lead.get(
                "lead_score"
            )

        if "opportunity" in lead:
            preview["opportunity"] = lead.get(
                "opportunity"
            )

        return preview

    # =========================================================
    # CHANGE CLASSIFICATION
    # =========================================================

    def classify_change(
        self,
        field,
        old_value,
        new_value
    ):
        """
        Classification:

        SAFE:
            Clearly harmless formatting/default cleanup.

        REVIEW:
            Change requires manual verification.

        PRESERVE:
            Existing business/derived value must remain unchanged.
        """

        # -----------------------------------------------------
        # PRESERVE BUSINESS / SYSTEM FIELDS
        # -----------------------------------------------------

        if field in self.PRESERVE_FIELDS:
            return "PRESERVE"

        # -----------------------------------------------------
        # NONE -> EMPTY STRING
        # -----------------------------------------------------

        if (
            old_value is None
            and new_value == ""
        ):

            if field in self.SAFE_EMPTY_FIELDS:
                return "SAFE"

            if field == "phone":
                return "SAFE"

            if field == "website":
                return "REVIEW"

            return "REVIEW"

        # -----------------------------------------------------
        # WHITESPACE ONLY
        # -----------------------------------------------------

        if (
            isinstance(old_value, str)
            and isinstance(new_value, str)
            and old_value != new_value
            and old_value.strip() == new_value
        ):
            return "SAFE"

        # -----------------------------------------------------
        # WEBSITE
        # -----------------------------------------------------

        if field == "website":

            # None -> "" is review because website data
            # may have inconsistent historical representation.
            if old_value is None and new_value == "":
                return "REVIEW"

            # True / False -> "" MUST NOT happen automatically.
            if isinstance(old_value, bool):
                return "REVIEW"

            # Real website URL changed.
            if (
                isinstance(old_value, str)
                and isinstance(new_value, str)
            ):
                return "REVIEW"

            return "REVIEW"

        # -----------------------------------------------------
        # PHONE
        # -----------------------------------------------------

        if field == "phone":

            if old_value is None and new_value == "":
                return "SAFE"

            if (
                isinstance(old_value, str)
                and isinstance(new_value, str)
            ):

                # If only spaces/separators are removed,
                # still review because phone identity matters.
                return "REVIEW"

            return "REVIEW"

        # -----------------------------------------------------
        # MISSING FIELDS
        # -----------------------------------------------------

        if field == "missing_fields":
            return "REVIEW"

        # -----------------------------------------------------
        # DATA STATUS
        # -----------------------------------------------------

        if field == "data_status":
            return "REVIEW"

        # -----------------------------------------------------
        # VALID PHONE
        # -----------------------------------------------------

        if field == "valid_phone":
            return "REVIEW"

        # -----------------------------------------------------
        # EMAIL
        # -----------------------------------------------------

        if field == "email":

            if (
                old_value is None
                and new_value == ""
            ):
                return "SAFE"

            if (
                isinstance(old_value, str)
                and isinstance(new_value, str)
                and old_value.strip() == new_value
            ):
                return "SAFE"

            return "REVIEW"

        # -----------------------------------------------------
        # MAPS URL
        # -----------------------------------------------------

        if field == "maps_url":

            if (
                old_value is None
                and new_value == ""
            ):
                return "SAFE"

            if (
                isinstance(old_value, str)
                and isinstance(new_value, str)
                and old_value.strip() == new_value
            ):
                return "SAFE"

            return "REVIEW"

        # -----------------------------------------------------
        # OTHER TEXT FIELDS
        # -----------------------------------------------------

        if field in {
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

            if (
                isinstance(old_value, str)
                and isinstance(new_value, str)
                and old_value.strip() == new_value
            ):
                return "SAFE"

            return "REVIEW"

        # -----------------------------------------------------
        # DEFAULT
        # -----------------------------------------------------

        return "REVIEW"

    # =========================================================
    # FORMAT VALUE
    # =========================================================

    def format_value(self, value):

        if value is None:
            return "None"

        if isinstance(value, list):

            if not value:
                return "[]"

            return "[" + ", ".join(
                str(item)
                for item in value
            ) + "]"

        if isinstance(value, dict):
            return str(value)

        return str(value)

    # =========================================================
    # PRINT HEADER
    # =========================================================

    def print_header(self, title):

        print()
        print("=" * 75)
        print(title)
        print("=" * 75)

    # =========================================================
    # DRY RUN PREVIEW
    # =========================================================

    def dry_run_preview(self):

        self.print_header(
            "TECHUWEB LEAD GENERATOR - NORMALIZATION PREVIEW V2"
        )

        print(
            "MODE                    : PREVIEW ONLY"
        )

        print(
            "DATABASE MODIFICATION   : DISABLED"
        )

        print(
            "DELETE                  : DISABLED"
        )

        print(
            "MERGE                   : DISABLED"
        )

        print(
            "NORMALIZATION APPLY     : DISABLED"
        )

        print(
            "LEAD SCORE OVERWRITE    : DISABLED"
        )

        print(
            "OPPORTUNITY OVERWRITE   : DISABLED"
        )

        # =====================================================
        # LOAD RECORDS
        # =====================================================

        self.print_header(
            "LOADING LEADS"
        )

        leads = list(
            self.collection.find(
                {}
            )
        )

        total_records = len(leads)

        print(
            f"Total MongoDB records : {total_records}"
        )

        # =====================================================
        # COUNTERS
        # =====================================================

        records_with_changes = 0
        already_normalized = 0
        total_changes = 0

        safe_changes = 0
        review_changes = 0
        preserve_changes = 0

        field_counter = Counter()
        classification_counter = Counter()

        examples = {}

        # =====================================================
        # PROCESS RECORDS
        # =====================================================

        for lead in leads:

            preview = self.prepare_preview_lead(
                lead
            )

            ignored_fields = {
                "_id",
                "created_at",
                "updated_at",
            }

            all_fields = (
                set(lead.keys())
                | set(preview.keys())
            )

            record_changes = []

            for field in sorted(all_fields):

                if field in ignored_fields:
                    continue

                old_value = lead.get(field)
                new_value = preview.get(field)

                if old_value == new_value:
                    continue

                classification = (
                    self.classify_change(
                        field,
                        old_value,
                        new_value
                    )
                )

                change = {
                    "field": field,
                    "old": old_value,
                    "new": new_value,
                    "classification": classification,
                    "business_name": lead.get(
                        "business_name",
                        ""
                    ),
                    "city": lead.get(
                        "city",
                        ""
                    ),
                }

                record_changes.append(
                    change
                )

                total_changes += 1

                field_counter[field] += 1

                classification_counter[
                    classification
                ] += 1

                if classification == "SAFE":
                    safe_changes += 1

                elif classification == "REVIEW":
                    review_changes += 1

                elif classification == "PRESERVE":
                    preserve_changes += 1

                # Keep max 3 examples per field.
                if field not in examples:
                    examples[field] = []

                if len(examples[field]) < 3:
                    examples[field].append(
                        change
                    )

            if record_changes:

                records_with_changes += 1

            else:

                already_normalized += 1

        # =====================================================
        # FIELD SUMMARY
        # =====================================================

        self.print_header(
            "FIELD-WISE CHANGE SUMMARY"
        )

        if not field_counter:

            print(
                "No changes detected."
            )

        else:

            for field, count in sorted(
                field_counter.items(),
                key=lambda item: (
                    -item[1],
                    item[0]
                )
            ):

                print(
                    f"{field:<25} : {count}"
                )

        # =====================================================
        # CLASSIFICATION SUMMARY
        # =====================================================

        self.print_header(
            "CHANGE CLASSIFICATION"
        )

        print(
            f"SAFE                   : "
            f"{safe_changes}"
        )

        print(
            f"REVIEW                 : "
            f"{review_changes}"
        )

        print(
            f"PRESERVE               : "
            f"{preserve_changes}"
        )

        print(
            f"TOTAL                  : "
            f"{total_changes}"
        )

        # =====================================================
        # IMPORTANT FIELD STATUS
        # =====================================================

        self.print_header(
            "BUSINESS FIELD PROTECTION"
        )

        print(
            "lead_score              : PRESERVED"
        )

        print(
            "opportunity             : PRESERVED"
        )

        print(
            "created_at              : PRESERVED"
        )

        print(
            "updated_at              : PRESERVED"
        )

        print(
            "Real website values    : REVIEW BEFORE CHANGE"
        )

        # =====================================================
        # CHANGE EXAMPLES
        # =====================================================

        self.print_header(
            "CHANGE EXAMPLES"
        )

        if not examples:

            print(
                "No changes detected."
            )

        else:

            for field in sorted(
                examples.keys()
            ):

                print()
                print(
                    f"FIELD: {field}"
                )

                print(
                    "-" * 75
                )

                for example in examples[field]:

                    print(
                        f"Business        : "
                        f"{example['business_name']}"
                    )

                    print(
                        f"City            : "
                        f"{example['city']}"
                    )

                    print(
                        f"Classification  : "
                        f"{example['classification']}"
                    )

                    print(
                        f"OLD             : "
                        f"{self.format_value(example['old'])}"
                    )

                    print(
                        f"NEW             : "
                        f"{self.format_value(example['new'])}"
                    )

                    print()

        # =====================================================
        # FINAL SUMMARY
        # =====================================================

        self.print_header(
            "FINAL PREVIEW SUMMARY"
        )

        print(
            f"Total records              : "
            f"{total_records}"
        )

        print(
            f"Records with changes       : "
            f"{records_with_changes}"
        )

        print(
            f"Already normalized         : "
            f"{already_normalized}"
        )

        print(
            f"Total proposed changes     : "
            f"{total_changes}"
        )

        print(
            f"SAFE changes               : "
            f"{safe_changes}"
        )

        print(
            f"REVIEW changes             : "
            f"{review_changes}"
        )

        print(
            f"PRESERVE changes           : "
            f"{preserve_changes}"
        )

        # =====================================================
        # SAFETY STATUS
        # =====================================================

        self.print_header(
            "SAFETY STATUS"
        )

        print(
            "MongoDB records modified : 0"
        )

        print(
            "Records deleted          : 0"
        )

        print(
            "Records merged           : 0"
        )

        print(
            "Updates executed         : 0"
        )

        print(
            "Normalization applied    : NO"
        )

        print(
            "Database write operation : NONE"
        )

        print()
        print(
            "This is a PREVIEW ONLY."
        )

        print(
            "No MongoDB changes were made."
        )

        # =====================================================
        # NEXT STEP
        # =====================================================

        self.print_header(
            "NEXT STEP"
        )

        print(
            "Do NOT apply normalization yet."
        )

        print(
            "Review SAFE / REVIEW / PRESERVE "
            "changes first."
        )

        print(
            "Lead scores and opportunities "
            "will remain unchanged."
        )

        print(
            "No MongoDB changes were made."
        )

        # =====================================================
        # RETURN RESULT
        # =====================================================

        return {
            "total_records": total_records,
            "records_with_changes": records_with_changes,
            "already_normalized": already_normalized,
            "total_changes": total_changes,
            "safe_changes": safe_changes,
            "review_changes": review_changes,
            "preserve_changes": preserve_changes,
        }

    # =========================================================
    # SAVE REPORT
    # =========================================================

    def save_report(self, report_text):

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
            / f"normalization_preview_v2_{timestamp}.txt"
        )

        with open(
            report_path,
            "w",
            encoding="utf-8"
        ) as file:

            file.write(report_text)

        return report_path


# =============================================================
# MAIN
# =============================================================

def main():

    db = None

    try:

        # -----------------------------------------------------
        # CONNECT TO MONGODB
        # -----------------------------------------------------

        db = MongoDB()

        # -----------------------------------------------------
        # CREATE CLEANUP SERVICE
        # -----------------------------------------------------

        cleanup = NormalizationCleanup(
            db
        )

        # -----------------------------------------------------
        # CAPTURE REPORT
        # -----------------------------------------------------

        from io import StringIO
        from contextlib import redirect_stdout

        buffer = StringIO()

        with redirect_stdout(buffer):

            result = cleanup.dry_run_preview()

        report_text = buffer.getvalue()

        # -----------------------------------------------------
        # DISPLAY REPORT
        # -----------------------------------------------------

        print(report_text)

        # -----------------------------------------------------
        # SAVE REPORT
        # -----------------------------------------------------

        report_path = cleanup.save_report(
            report_text
        )

        print()
        print("=" * 75)
        print("PREVIEW REPORT SAVED")
        print("=" * 75)

        print(
            f"Report file : {report_path}"
        )

        print()
        print(
            "MongoDB was NOT modified."
        )

        print(
            "No normalization was applied."
        )

    except Exception as error:

        print()
        print("=" * 75)
        print("NORMALIZATION PREVIEW ERROR")
        print("=" * 75)

        print(
            f"Error: {error}"
        )

        raise

    finally:

        # -----------------------------------------------------
        # CLOSE DATABASE
        # -----------------------------------------------------

        if db is not None:

            try:

                db.close()

                print()
                print(
                    "MongoDB connection closed."
                )

            except Exception as close_error:

                print(
                    f"MongoDB close warning: "
                    f"{close_error}"
                )


# =============================================================
# ENTRY POINT
# =============================================================

if __name__ == "__main__":
    main()