import os

from playwright.sync_api import sync_playwright

from scraper.extractor import BusinessExtractor
from services.enrichment import LeadEnricher


def scrape_google_maps(keyword):
    """
    Scrape business information from Google Maps.

    Args:
        keyword (str): Search keyword, e.g. Dental Clinic Faridabad.

    Returns:
        list: Scraped business leads.
    """

    leads = []
    browser = None

    # Configure browser mode using an environment variable.
    headless = (
        os.getenv("PLAYWRIGHT_HEADLESS", "false").strip().lower()
        == "true"
    )

    # Build Google Maps search URL.
    search_keyword = keyword.strip().replace(" ", "%20")
    url = f"https://www.google.com/maps/search/{search_keyword}"

    print(f"\nOpening: {url}")
    print(f"Browser mode: {'Headless' if headless else 'Visible'}")

    try:
        with sync_playwright() as p:

            try:
                # ==========================================
                # START BROWSER
                # ==========================================

                browser = p.chromium.launch(
                    headless=headless
                )

                page = browser.new_page()

                # ==========================================
                # OPEN GOOGLE MAPS WITH RETRIES
                # ==========================================

                max_retries = 3
                page_loaded = False

                for attempt in range(1, max_retries + 1):

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

                        print("Google Maps loaded successfully.")
                        page_loaded = True
                        break

                    except Exception as e:
                        print(f"Google Maps loading failed: {e}")

                        if attempt < max_retries:
                            print("Retrying...")

                if not page_loaded:
                    print(
                        "\nGoogle Maps could not be loaded "
                        "after all retry attempts."
                    )
                    return []

                # ==========================================
                # WAIT FOR PAGE
                # ==========================================

                page.wait_for_timeout(5000)

                print(f"Page title: {page.title()}")
                print(f"Page URL: {page.url}")

                # ==========================================
                # SCROLL RESULTS
                # ==========================================

                for _ in range(5):
                    try:
                        page.mouse.wheel(0, 1000)
                        page.wait_for_timeout(2000)

                    except Exception as e:
                        print(f"Scroll error: {e}")
                        break

                # ==========================================
                # LOCATE BUSINESS CARDS
                # ==========================================

                clinics = page.locator('div[role="article"]')

                try:
                    count = clinics.count()

                except Exception as e:
                    print(f"Could not read Google Maps results: {e}")
                    return []

                print(f"\nTotal Results Found: {count}")

                if count == 0:
                    print(
                        "\nNo business cards found. "
                        "Google Maps may not have loaded the results."
                    )
                    return []

                # ==========================================
                # INITIALIZE EXTRACTOR AND ENRICHER
                # ==========================================

                extractor = BusinessExtractor(page)
                enricher = LeadEnricher(page)

                # ==========================================
                # PROCESS BUSINESS CARDS
                # ==========================================

                for i in range(min(count, 10)):

                    print(
                        f"\n========== Business {i + 1} =========="
                    )

                    try:
                        # Get the business card.
                        clinic = clinics.nth(i)

                        clinic.scroll_into_view_if_needed()
                        page.wait_for_timeout(1000)

                        # Read the original card text.
                        raw_text = clinic.inner_text()

                        # Open the business details.
                        try:
                            clinic.click()
                            page.wait_for_timeout(3000)

                        except Exception as e:
                            print(f"Could not open business: {e}")
                            continue

                        # ==================================
                        # EXTRACT BUSINESS DETAILS
                        # ==================================

                        details = extractor.extract_details()

                        print("\n===== Extracted Details =====")
                        print(details)

                        # Create a lead from the extracted data.
                        lead = details.copy()
                        lead["text"] = raw_text

                        # ==================================
                        # ENRICH MISSING DATA
                        # ==================================

                        print("\n===== ENRICHMENT =====")

                        lead = enricher.enrich_lead(lead)

                        # ==================================
                        # DISPLAY ENRICHED DATA
                        # ==================================

                        print("\n===== Enriched Lead =====")
                        print(f"Business: {lead.get('business_name')}")
                        print(f"Phone: {lead.get('phone')}")
                        print(f"Website: {lead.get('website')}")
                        print(f"Address: {lead.get('address')}")

                        # ==================================
                        # SAVE TO RESULTS LIST
                        # ==================================

                        leads.append(
                            {
                                "text": raw_text,
                                "details": lead
                            }
                        )

                        print("\n===== Raw Card =====")
                        print(raw_text)

                    except Exception as e:
                        print(
                            f"\nError processing business {i + 1}: {e}"
                        )
                        print("Skipping this business and continuing.")

                # ==========================================
                # SCRAPING COMPLETE
                # ==========================================

                print("\nScraping completed.")
                print(
                    f"Successfully processed: {len(leads)} businesses"
                )

                return leads

            finally:
                # ==========================================
                # CLOSE BROWSER SAFELY
                # ==========================================

                if browser:
                    try:
                        browser.close()
                        print("Browser closed.")

                    except Exception as e:
                        print(f"Browser close error: {e}")

    except Exception as e:
        print(f"\nScraper error: {e}")
        return []