import json
import os
from database.mongodb import MongoDB


BACKUP_FILE = (
    "output/backup/leads_backup_20260912_173434.json"
)


def main():

    print("=" * 80)
    print("BACKUP INTEGRITY TEST")
    print("=" * 80)

    db = MongoDB()

    try:

        # =====================================================
        # TEST 1 - FILE EXISTS
        # =====================================================

        print("\n" + "=" * 80)
        print("TEST 1 - CHECK BACKUP FILE")
        print("=" * 80)

        if not os.path.exists(BACKUP_FILE):

            print(
                f"\n❌ Backup file not found:\n"
                f"{BACKUP_FILE}"
            )

            return

        print(
            f"\n✅ Backup file exists:\n"
            f"{BACKUP_FILE}"
        )

        # =====================================================
        # TEST 2 - LOAD JSON
        # =====================================================

        print("\n" + "=" * 80)
        print("TEST 2 - LOAD JSON BACKUP")
        print("=" * 80)

        with open(
            BACKUP_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            backup_data = json.load(file)

        print(
            "\n✅ JSON file loaded successfully"
        )

        # =====================================================
        # TEST 3 - RECORD COUNT
        # =====================================================

        print("\n" + "=" * 80)
        print("TEST 3 - VERIFY RECORD COUNT")
        print("=" * 80)

        database_count = (
            db.collection.count_documents({})
        )

        backup_count = len(backup_data)

        print(
            f"\nMongoDB records : {database_count}"
        )

        print(
            f"Backup records  : {backup_count}"
        )

        if database_count == backup_count:

            print(
                "\n✅ Record counts match"
            )

        else:

            print(
                "\n⚠️ Record counts do not match"
            )

        # =====================================================
        # TEST 4 - REQUIRED FIELDS
        # =====================================================

        print("\n" + "=" * 80)
        print("TEST 4 - VERIFY IMPORTANT FIELDS")
        print("=" * 80)

        required_fields = [
            "business_name",
            "phone",
            "website",
            "city"
        ]

        records_with_missing_fields = 0

        for index, lead in enumerate(
            backup_data,
            start=1
        ):

            missing_fields = [
                field
                for field in required_fields
                if field not in lead
            ]

            if missing_fields:

                records_with_missing_fields += 1

                print(
                    f"\nRecord {index} missing: "
                    f"{missing_fields}"
                )

        if records_with_missing_fields == 0:

            print(
                "\n✅ All records contain the required keys"
            )

        else:

            print(
                f"\n⚠️ "
                f"{records_with_missing_fields} records "
                f"have missing keys"
            )

        # =====================================================
        # TEST 5 - SAMPLE RECORD
        # =====================================================

        print("\n" + "=" * 80)
        print("TEST 5 - SAMPLE BACKUP RECORD")
        print("=" * 80)

        if backup_data:

            sample = backup_data[0]

            print(
                f"\nBusiness Name: "
                f"{sample.get('business_name')}"
            )

            print(
                f"Phone: "
                f"{sample.get('phone')}"
            )

            print(
                f"Website: "
                f"{sample.get('website')}"
            )

            print(
                f"City: "
                f"{sample.get('city')}"
            )

        # =====================================================
        # FINAL RESULT
        # =====================================================

        print("\n" + "=" * 80)
        print("BACKUP INTEGRITY TEST COMPLETED")
        print("=" * 80)

        print(
            "\n⚠️ No database records were modified."
        )

    except Exception as e:

        print("\n❌ BACKUP TEST ERROR")

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