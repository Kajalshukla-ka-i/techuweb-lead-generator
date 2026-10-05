from database.mongodb import MongoDB
from services.lead_cleanup import LeadCleanup


db = MongoDB()

try:
    cleanup = LeadCleanup(db)

    leads = cleanup.get_leads()
    groups = cleanup.build_duplicate_groups(leads)

    print("\n" + "=" * 90)
    print(f"DUPLICATE GROUPS: {len(groups)}")
    print("=" * 90)

    for group_index, group in enumerate(groups, start=1):

        print("\n" + "=" * 90)
        print(f"GROUP {group_index}")
        print("=" * 90)

        for lead_index, lead in enumerate(group, start=1):

            print(f"\nLEAD {lead_index}")
            print("-" * 50)

            print("MongoDB _id      :", lead.get("_id"))
            print("Business Name    :", lead.get("business_name"))
            print("City             :", lead.get("city"))
            print("Category         :", lead.get("category"))
            print("Rating           :", lead.get("rating"))
            print("Phone            :", lead.get("phone"))
            print("Website          :", lead.get("website"))
            print("Address          :", lead.get("address"))
            print("Maps URL         :", lead.get("maps_url"))
            print("Lead Score       :", lead.get("lead_score"))
            print("Opportunity      :", lead.get("opportunity"))
            print("Created At       :", lead.get("created_at"))

finally:
    db.close()

    print("\n" + "=" * 90)
    print("MongoDB Connection Closed")
    print("=" * 90)