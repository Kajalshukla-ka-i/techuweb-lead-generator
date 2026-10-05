from playwright.sync_api import sync_playwright

from scraper.extractor import BusinessExtractor
from services.enrichment import LeadEnricher


def scrape_google_maps(keyword):
    """
    Scrape Google Maps search results.

    Args:
        keyword (str):
            Example:
            Dental Clinic Faridabad

    Returns:
        list:
            List of scraped business leads
    """

    leads = []

    # ==========================================
    # BUILD GOOGLE MAPS SEARCH URL
    # ==========================================

    search_keyword = keyword.replace(
        " ",
        "%20"
    )

    url = (
        f"https://www.google.com/maps/search/"
        f"{search_keyword}"
    )

    print(f"\nOpening: {url}")

    with sync_playwright() as p:

        browser = None

        try:

            # ==========================================
            # START BROWSER
            # ==========================================

            browser = p.chromium.launch(
                headless=False
            )

            page = browser.new_page()

            # ==========================================
            # OPEN GOOGLE MAPS WITH RETRY
            # ==========================================

            max_retries = 3

            for attempt in range(
                1,
                max_retries + 1
            ):

                try:

                    print(
                        f"\nOpening Google Maps "
                        f"(Attempt {attempt}/{max_retries})"
                    )

                    page.goto(
                        url,
                        wait_until="domcontentloaded",
                        timeout=60000
                    )

                    print(
                        "Google Maps loaded successfully."
                    )

                    break

                except Exception as e:

                    print(
                        f"Google Maps loading failed: {e}"
                    )

                    if attempt == max_retries:

                        print(
                            "\n❌ Google Maps could not "
                            "be loaded after 3 attempts."
                        )

                        return []

                    print(
                        "Retrying..."
                    )

            # ==========================================
            # WAIT FOR PAGE
            # ==========================================

            page.wait_for_timeout(
                5000
            )

            print(
                page.title()
            )

            print(
                page.url
            )

            # ==========================================
            # SCROLL RESULTS
            # ==========================================

            for _ in range(5):

                try:

                    page.mouse.wheel(
                        0,
                        1000
                    )

                    page.wait_for_timeout(
                        2000
                    )

                except Exception as e:

                    print(
                        f"Scroll error: {e}"
                    )

                    break

            # ==========================================
            # LOCATE BUSINESS CARDS
            # ==========================================

            clinics = page.locator(
                'div[role="article"]'
            )

            try:

                count = clinics.count()

            except Exception as e:

                print(
                    f"\n❌ Could not read "
                    f"Google Maps results: {e}"
                )

                return []

            print(
                f"\nTotal Results Found: {count}"
            )

            if count == 0:

                print(
                    "\n⚠️ No business results found."
                )

                return []

            # ==========================================
            # INITIALIZE EXTRACTOR
            # ==========================================

            extractor = BusinessExtractor(
                page
            )

            # ==========================================
            # INITIALIZE ENRICHER
            # ==========================================

            enricher = LeadEnricher(
                page
            )

            # ==========================================
            # PROCESS BUSINESS CARDS
            # ==========================================

            for i in range(
                min(count, 10)
            ):

                try:

                    print(
                        f"\n========== "
                        f"Business {i + 1} "
                        f"=========="
                    )

                    # ----------------------------------
                    # GET CARD
                    # ----------------------------------

                    clinic = clinics.nth(i)

                    clinic.scroll_into_view_if_needed()

                    page.wait_for_timeout(
                        1000
                    )

                    # ----------------------------------
                    # READ RAW CARD
                    # ----------------------------------

                    raw_text = clinic.inner_text()

                    # ----------------------------------
                    # CLICK BUSINESS
                    # ----------------------------------

                    try:

                        clinic.click()

                        page.wait_for_timeout(
                            3000
                        )

                    except Exception as click_error:

                        print(
                            f"Could not click "
                            f"business: "
                            f"{click_error}"
                        )

                        continue

                    # ==================================
                    # EXTRACT BUSINESS DETAILS
                    # ==================================

                    details = (
                        extractor.extract_details()
                    )

                    print(
                        "\n===== Extracted Details ====="
                    )

                    print(
                        details
                    )

                    # ==================================
                    # CREATE LEAD
                    # ==================================

                    lead = details.copy()

                    lead["text"] = raw_text

                    # ==================================
                    # ENRICH MISSING DATA
                    # ==================================

                    print(
                        "\n===== ENRICHMENT ====="
                    )

                    lead = enricher.enrich_lead(
                        lead
                    )

                    # ==================================
                    # SHOW ENRICHED DATA
                    # ==================================

                    print(
                        "\n===== Enriched Lead ====="
                    )

                    print(
                        f"Business: "
                        f"{lead.get('business_name')}"
                    )

                    print(
                        f"Phone: "
                        f"{lead.get('phone')}"
                    )

                    print(
                        f"Website: "
                        f"{lead.get('website')}"
                    )

                    print(
                        f"Address: "
                        f"{lead.get('address')}"
                    )

                    # ==================================
                    # ADD TO RESULTS
                    # ==================================

                    leads.append(
                        {
                            "text": raw_text,
                            "details": lead
                        }
                    )

                    # ==================================
                    # RAW CARD
                    # ==================================

                    print(
                        "\n===== Raw Card ====="
                    )

                    print(
                        raw_text
                    )

                except Exception as e:

                    print(
                        f"\n⚠️ Error processing "
                        f"business {i + 1}: {e}"
                    )

                    print(
                        "Skipping this business "
                        "and continuing..."
                    )

            # ==========================================
            # SCRAPING COMPLETE
            # ==========================================

            print(
                f"\n✅ Scraping completed."
            )

            print(
                f"Successfully processed: "
                f"{len(leads)} businesses"
            )

            return leads

        except Exception as e:

            print(
                f"\n❌ Scraper error: {e}"
            )

            return []

        finally:

            # ==========================================
            # CLOSE BROWSER SAFELY
            # ==========================================

            if browser:

                try:

                    browser.close()

                    print(
                        "Browser closed."
                    )

                except Exception as e:

                    print(
                        f"Browser close error: {e}"
                    )
