from database.mongodb import MongoDB
from services.crm import CRMService


def print_lead(lead):

    print("\n" + "=" * 60)
    print("LEAD DETAILS")
    print("=" * 60)

    if not lead:
        print("❌ Lead not found")
        return

    print("Business:", lead.get("business_name"))
    print("Phone:", lead.get("phone"))
    print("Email:", lead.get("email"))
    print("Website:", lead.get("website"))
    print("Status:", lead.get("status"))
    print("Notes:", lead.get("notes"))
    print("Assigned To:", lead.get("assigned_to"))
    print("Lead Score:", lead.get("lead_score"))
    print("Opportunity:", lead.get("opportunity"))


def main():

    print("=" * 60)
    print("TEST CRM SERVICE")
    print("=" * 60)

    db = MongoDB()

    try:

        crm = CRMService(db)

        # ==================================================
        # TEST BUSINESS
        # ==================================================

        business_name = "Neelam Maid & Babysitter Services"

        # ==================================================
        # TEST 1: GET LEAD
        # ==================================================

        print("\n[TEST 1] GET LEAD")

        lead = crm.get_lead(
            business_name
        )

        print_lead(lead)

        # ==================================================
        # TEST 2: UPDATE STATUS
        # ==================================================

        print("\n[TEST 2] UPDATE STATUS")

        result = crm.update_status(
            business_name,
            "CONTACTED"
        )

        print(
            "Status Update:",
            "SUCCESS" if result else "FAILED"
        )

        # ==================================================
        # TEST 3: UPDATE NOTES
        # ==================================================

        print("\n[TEST 3] UPDATE NOTES")

        result = crm.update_notes(
            business_name,
            "Initial contact completed."
        )

        print(
            "Notes Update:",
            "SUCCESS" if result else "FAILED"
        )

        # ==================================================
        # TEST 4: ASSIGN LEAD
        # ==================================================

        print("\n[TEST 4] ASSIGN LEAD")

        result = crm.assign_lead(
            business_name,
            "Kajal"
        )

        print(
            "Assignment:",
            "SUCCESS" if result else "FAILED"
        )

        # ==================================================
        # TEST 5: UPDATE EMAIL
        # ==================================================

        print("\n[TEST 5] UPDATE EMAIL")

        result = crm.update_email(
            business_name,
            "test@example.com"
        )

        print(
            "Email Update:",
            "SUCCESS" if result else "FAILED"
        )

        # ==================================================
        # TEST 6: UPDATE PHONE
        # ==================================================

        print("\n[TEST 6] UPDATE PHONE")

        result = crm.update_phone(
            business_name,
            "9876543210"
        )

        print(
            "Phone Update:",
            "SUCCESS" if result else "FAILED"
        )

        # ==================================================
        # TEST 7: UPDATE WEBSITE
        # ==================================================

        print("\n[TEST 7] UPDATE WEBSITE")

        result = crm.update_website(
            business_name,
            "https://example.com"
        )

        print(
            "Website Update:",
            "SUCCESS" if result else "FAILED"
        )

        # ==================================================
        # TEST 8: GET UPDATED LEAD
        # ==================================================

        print("\n[TEST 8] GET UPDATED LEAD")

        lead = crm.get_lead(
            business_name
        )

        print_lead(lead)

        # ==================================================
        # TEST COMPLETE
        # ==================================================

        print("\n" + "=" * 60)
        print("ALL CRM TESTS COMPLETED")
        print("=" * 60)

    except Exception as e:

        print(
            f"\n❌ ERROR: {e}"
        )

    finally:

        db.close()

        print(
            "\nMongoDB Connection Closed"
        )


if __name__ == "__main__":
    main()