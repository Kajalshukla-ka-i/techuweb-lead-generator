from database.mongodb import MongoDB
from services.lead_cleanup import LeadCleanup


db = MongoDB()

try:
    cleanup = LeadCleanup(db)

    leads = cleanup.get_leads()
    groups = cleanup.build_duplicate_groups(leads)

    print("\n" + "=" * 80)
    print("TECHUWEB - DUPLICATE PREVIEW")
    print("=" * 80)

    print(f"\nTotal records   : {len(leads)}")
    print(f"Duplicate groups: {len(groups)}")

    duplicate_count = 0

    for number, group in enumerate(groups, start=1):

        # Sort by created date.
        group = sorted(
            group,
            key=lambda x: x.get("created_at") or ""
        )

        # Keep the oldest record.
        primary = group[0]

        print("\n" + "-" * 80)
        print(f"GROUP {number}")
        print("-" * 80)

        print("KEEP")
        print("ID      :", primary.get("_id"))
        print("Business:", primary.get("business_name"))
        print("City    :", primary.get("city"))

        # Everything after the first record is duplicate.
        for duplicate in group[1:]:

            duplicate_count += 1

            print("\nDELETE")
            print("ID      :", duplicate.get("_id"))
            print("Business:", duplicate.get("business_name"))
            print("City    :", duplicate.get("city"))

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    print("Total records    :", len(leads))
    print("Duplicate groups :", len(groups))
    print("Duplicates       :", duplicate_count)
    print("Records remaining:", len(leads) - duplicate_count)

    print("\nPREVIEW ONLY")
    print("Nothing was deleted.")

finally:
    db.close()