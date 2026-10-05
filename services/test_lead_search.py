from database.mongodb import MongoDB
from services.lead_search import LeadSearchService


def print_results(title, leads):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)

    print(f"Total Results: {len(leads)}")

    for index, lead in enumerate(leads, start=1):
        print(f"\n--- Lead {index} ---")
        print(f"Business    : {lead.get('business_name')}")
        print(f"Phone       : {lead.get('phone')}")
        print(f"Category    : {lead.get('category')}")
        print(f"City        : {lead.get('city')}")
        print(f"Website     : {lead.get('website')}")
        print(f"Score       : {lead.get('lead_score')}")
        print(f"Opportunity : {lead.get('opportunity')}")
        print(f"Status      : {lead.get('status')}")
        print(f"Data Status : {lead.get('data_status')}")


def main():

    print("=" * 70)
    print("LEAD SEARCH SERVICE TEST")
    print("=" * 70)

    db = MongoDB()
    search_service = LeadSearchService(db)

    try:

        # ==================================================
        # TEST 1
        # ==================================================

        results = search_service.search("Neelam")

        print_results(
            "TEST 1 - SEARCH: Neelam",
            results
        )

        # ==================================================
        # TEST 2
        # ==================================================

        results = search_service.search("noida")

        print_results(
            "TEST 2 - SEARCH: Noida",
            results
        )

        # ==================================================
        # TEST 3
        # ==================================================

        results = search_service.filter_leads(
            opportunity="HIGH"
        )

        print_results(
            "TEST 3 - FILTER: HIGH OPPORTUNITY",
            results
        )

        # ==================================================
        # TEST 4
        # ==================================================

        results = search_service.filter_leads(
            city="noida"
        )

        print_results(
            "TEST 4 - FILTER: CITY = NOIDA",
            results
        )

        # ==================================================
        # TEST 5
        # ==================================================

        results = search_service.filter_leads(
            min_score=70
        )

        print_results(
            "TEST 5 - FILTER: SCORE >= 70",
            results
        )

        # ==================================================
        # TEST 6
        # ==================================================

        results = search_service.filter_leads(
            has_website=False
        )

        print_results(
            "TEST 6 - FILTER: WITHOUT WEBSITE",
            results
        )

        # ==================================================
        # TEST 7
        # ==================================================

        results = search_service.filter_leads(
            has_website=True
        )

        print_results(
            "TEST 7 - FILTER: WITH WEBSITE",
            results
        )

        # ==================================================
        # TEST 8
        # ==================================================

        results = search_service.filter_leads(
            data_status="INCOMPLETE"
        )

        print_results(
            "TEST 8 - FILTER: INCOMPLETE",
            results
        )

        # ==================================================
        # TEST 9
        # ==================================================

        results = search_service.search_and_filter(
            query="salon",
            city="noida",
            opportunity="HIGH"
        )

        print_results(
            "TEST 9 - SEARCH + FILTER",
            results
        )

        # ==================================================
        # TEST 10
        # ==================================================

        results = search_service.search_and_filter(
            city="noida",
            opportunity="HIGH",
            min_score=70,
            has_website=False
        )

        print_results(
            "TEST 10 - COMPLEX FILTER",
            results
        )

        print("\n" + "=" * 70)
        print("ALL LEAD SEARCH TESTS COMPLETED")
        print("=" * 70)

    except Exception as e:

        print("\n❌ TEST ERROR")
        print(f"{type(e).__name__}: {e}")

    finally:

        db.close()
        print("\nMongoDB Connection Closed")


if __name__ == "__main__":
    main()