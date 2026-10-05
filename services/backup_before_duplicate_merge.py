import json
import os
from datetime import datetime

from database.mongodb import MongoDB


BACKUP_DIR = "output/backup"


def main():
    db = MongoDB()

    try:
        os.makedirs(BACKUP_DIR, exist_ok=True)

        leads = list(
            db.collection.find({})
        )

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        backup_file = os.path.join(
            BACKUP_DIR,
            f"leads_before_duplicate_merge_{timestamp}.json"
        )

        with open(
            backup_file,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                leads,
                file,
                indent=4,
                ensure_ascii=False,
                default=str
            )

        print("\n" + "=" * 80)
        print("TECHUWEB LEAD GENERATOR - DUPLICATE MERGE BACKUP")
        print("=" * 80)

        print(f"\nRecords backed up : {len(leads)}")
        print(f"Backup file       : {backup_file}")

        if len(leads) == 85:
            print("\nBACKUP STATUS : SUCCESS")
            print("85 records successfully backed up.")
        else:
            print("\nBACKUP STATUS : WARNING")
            print(f"Expected 85 records, but found {len(leads)}.")

        print("\nNO DATABASE RECORDS WERE MODIFIED.")
        print("NO DATABASE RECORDS WERE DELETED.")
        print("NO DATABASE RECORDS WERE MERGED.")

    finally:
        db.close()

        print("\n" + "=" * 80)
        print("MongoDB Connection Closed")
        print("=" * 80)


if __name__ == "__main__":
    main()