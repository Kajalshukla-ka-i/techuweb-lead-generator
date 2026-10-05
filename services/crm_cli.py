from database.mongodb import MongoDB
from services.lead_service import LeadService


# ==================================================
# PRINT LEAD
# ==================================================

def print_lead(lead):

    print("\n" + "=" * 60)
    print("LEAD DETAILS")
    print("=" * 60)

    print("Business:", lead.get("business_name"))
    print("Category:", lead.get("category"))
    print("City:", lead.get("city"))
    print("Phone:", lead.get("phone"))
    print("Email:", lead.get("email"))
    print("Website:", lead.get("website"))
    print("Address:", lead.get("address"))
    print("Rating:", lead.get("rating"))
    print("Reviews:", lead.get("reviews"))
    print("Lead Score:", lead.get("lead_score"))
    print("Opportunity:", lead.get("opportunity"))
    print("Status:", lead.get("status"))
    print("Assigned To:", lead.get("assigned_to"))
    print("Notes:", lead.get("notes"))
    print("Data Status:", lead.get("data_status"))


# ==================================================
# PRINT LEADS
# ==================================================

def print_leads(leads):

    if not leads:
        print("\n❌ No leads found.")
        return

    print(f"\nFound {len(leads)} leads")

    for index, lead in enumerate(leads, start=1):

        print("\n" + "-" * 60)

        print(f"[{index}] {lead.get('business_name')}")

        print(
            f"Phone: {lead.get('phone')}"
        )

        print(
            f"Website: {lead.get('website')}"
        )

        print(
            f"City: {lead.get('city')}"
        )

        print(
            f"Score: {lead.get('lead_score')}"
        )

        print(
            f"Opportunity: {lead.get('opportunity')}"
        )

        print(
            f"Status: {lead.get('status')}"
        )


# ==================================================
# VIEW STATISTICS
# ==================================================

def show_statistics(service):

    statistics = service.get_statistics()

    print("\n" + "=" * 60)
    print("LEAD STATISTICS")
    print("=" * 60)

    print("Total Leads:", statistics["total"])
    print("High Opportunity:", statistics["high"])
    print("Medium Opportunity:", statistics["medium"])
    print("Low Opportunity:", statistics["low"])
    print("Incomplete:", statistics["incomplete"])
    print("Without Website:", statistics["without_website"])

    print("\nCRM STATUS")

    print("NEW:", statistics["new"])
    print("CONTACTED:", statistics["contacted"])
    print("INTERESTED:", statistics["interested"])
    print("CONVERTED:", statistics["converted"])


# ==================================================
# SEARCH LEAD
# ==================================================

def search_lead(service):

    business_name = input(
        "\nEnter Business Name: "
    ).strip()

    if not business_name:
        print("❌ Business name cannot be empty.")
        return

    leads = service.get_all_leads()

    matches = []

    for lead in leads:

        name = lead.get(
            "business_name",
            ""
        )

        if business_name.lower() in name.lower():

            matches.append(lead)

    print_leads(matches)


# ==================================================
# UPDATE STATUS
# ==================================================

def update_status(service):

    business_name = input(
        "\nEnter Business Name: "
    ).strip()

    if not business_name:
        print("❌ Business name cannot be empty.")
        return

    print("\nAvailable Status:")

    print("1. NEW")
    print("2. CONTACTED")
    print("3. INTERESTED")
    print("4. CONVERTED")

    choice = input(
        "\nSelect Status: "
    ).strip()

    status_map = {
        "1": "NEW",
        "2": "CONTACTED",
        "3": "INTERESTED",
        "4": "CONVERTED"
    }

    status = status_map.get(choice)

    if not status:

        print("❌ Invalid status.")

        return

    success = service.update_status(
        business_name,
        status
    )

    if success:

        print(
            f"✅ Status updated to {status}"
        )

    else:

        print(
            "❌ Lead not found or status unchanged."
        )


# ==================================================
# UPDATE NOTES
# ==================================================

def update_notes(service):

    business_name = input(
        "\nEnter Business Name: "
    ).strip()

    if not business_name:
        print("❌ Business name cannot be empty.")
        return

    notes = input(
        "Enter Notes: "
    ).strip()

    success = service.update_notes(
        business_name,
        notes
    )

    if success:

        print("✅ Notes updated successfully.")

    else:

        print(
            "❌ Lead not found or notes unchanged."
        )


# ==================================================
# ASSIGN LEAD
# ==================================================

def assign_lead(service):

    business_name = input(
        "\nEnter Business Name: "
    ).strip()

    if not business_name:
        print("❌ Business name cannot be empty.")
        return

    assigned_to = input(
        "Assign To: "
    ).strip()

    if not assigned_to:
        print("❌ Assignee cannot be empty.")
        return

    success = service.collection.update_one(
        {
            "business_name": business_name
        },
        {
            "$set": {
                "assigned_to": assigned_to
            }
        }
    )

    if success.modified_count > 0:

        print(
            f"✅ Lead assigned to {assigned_to}"
        )

    else:

        print(
            "❌ Lead not found or already assigned."
        )


# ==================================================
# MAIN MENU
# ==================================================

def main():

    print("=" * 60)
    print("TECHUWEB CRM")
    print("=" * 60)

    db = MongoDB()

    service = LeadService(db)

    try:

        while True:

            print("\n")
            print("=" * 60)
            print("CRM MENU")
            print("=" * 60)

            print("1. View All Leads")
            print("2. View High Opportunity Leads")
            print("3. View Leads Without Website")
            print("4. View Incomplete Leads")
            print("5. Search Lead")
            print("6. Update Lead Status")
            print("7. Add / Update Notes")
            print("8. Assign Lead")
            print("9. View Statistics")
            print("0. Exit")

            choice = input(
                "\nEnter Choice: "
            ).strip()

            # ==========================================
            # VIEW ALL
            # ==========================================

            if choice == "1":

                leads = service.get_all_leads()

                print_leads(leads)

            # ==========================================
            # HIGH OPPORTUNITY
            # ==========================================

            elif choice == "2":

                leads = (
                    service
                    .get_high_opportunity_leads()
                )

                print_leads(leads)

            # ==========================================
            # WITHOUT WEBSITE
            # ==========================================

            elif choice == "3":

                leads = (
                    service
                    .get_leads_without_website()
                )

                print_leads(leads)

            # ==========================================
            # INCOMPLETE
            # ==========================================

            elif choice == "4":

                leads = (
                    service
                    .get_incomplete_leads()
                )

                print_leads(leads)

            # ==========================================
            # SEARCH
            # ==========================================

            elif choice == "5":

                search_lead(service)

            # ==========================================
            # UPDATE STATUS
            # ==========================================

            elif choice == "6":

                update_status(service)

            # ==========================================
            # NOTES
            # ==========================================

            elif choice == "7":

                update_notes(service)

            # ==========================================
            # ASSIGN
            # ==========================================

            elif choice == "8":

                assign_lead(service)

            # ==========================================
            # STATISTICS
            # ==========================================

            elif choice == "9":

                show_statistics(service)

            # ==========================================
            # EXIT
            # ==========================================

            elif choice == "0":

                print(
                    "\n👋 Exiting Techuweb CRM..."
                )

                break

            else:

                print(
                    "\n❌ Invalid choice."
                )

    except Exception as e:

        print(
            f"\n❌ ERROR: {e}"
        )

    finally:

        db.close()

        print(
            "MongoDB Connection Closed"
        )


# ==================================================
# RUN
# ==================================================

if __name__ == "__main__":

    main()