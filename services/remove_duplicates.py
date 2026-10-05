from database.mongodb import MongoDB
from services.lead_cleanup import LeadCleanup


db = MongoDB()

try:
    cleanup = LeadCleanup(db)

    leads = cleanup.get_leads()
    groups = cleanup.build_duplicate_groups(leads)

    print("\n" + "=" * 80)
    print("TECHUWEB - REMOVE DUPLICATES")
    print("=" * 80)

    print(f"\nBefore cleanup : {len(leads)}")
    print(f"Duplicate groups: {len(groups)}")

    deleted = 0

    for number, group in enumerate(groups, start=1):

        # Oldest record stays.
        group = sorted(
            group,
            key=lambda x: x.get("created_at") or ""
        )

        keep = group[0]

        print("\n" + "-" * 80)
        print(f"GROUP {number}")
        print("-" * 80)

        print("KEEP   :", keep.get("business_name"))
        print("KEEP ID:", keep.get("_id"))

        # Delete duplicate records.
        for duplicate in group[1:]:

            duplicate_id = duplicate.get("_id")

            print("\nDELETE :", duplicate.get("business_name"))
            print("DELETE ID:", duplicate_id)

            result = db.collection.delete_one(
                {"_id": duplicate_id}
            )

            if result.deleted_count == 1:
                deleted += 1
                print("STATUS : DELETED")
            else:
                print("STATUS : NOT DELETED")

    # Check final count.
    remaining = db.collection.count_documents({})

    print("\n" + "=" * 80)
    print("CLEANUP COMPLETE")
    print("=" * 80)

    print("\nBefore cleanup :", len(leads))
    print("Deleted        :", deleted)
    print("After cleanup  :", remaining)

finally:
    db.close()