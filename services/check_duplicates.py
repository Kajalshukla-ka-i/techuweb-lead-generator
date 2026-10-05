from database.mongodb import MongoDB
from services.lead_cleanup import LeadCleanup


db = MongoDB()

try:
    cleanup = LeadCleanup(db)

    leads = cleanup.get_leads()
    groups = cleanup.build_duplicate_groups(leads)

    print("\n" + "=" * 70)
    print("TECHUWEB - DATABASE CHECK")
    print("=" * 70)

    print("\nTotal records    :", len(leads))
    print("Duplicate groups :", len(groups))

    if len(groups) == 0:
        print("\nSTATUS : CLEAN")
        print("No duplicate records found.")
    else:
        print("\nSTATUS : DUPLICATES FOUND")

finally:
    db.close()