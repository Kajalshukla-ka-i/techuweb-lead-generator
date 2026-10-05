import re
from urllib.parse import urlparse

from playwright.sync_api import Page


class LeadEnricher:

    def __init__(self, page: Page):
        self.page = page

    # ==================================================
    # PHONE
    # ==================================================

    def find_phone(self):
        """
        Find phone number from the currently opened
        Google Maps business page.
        """

        try:

            phone_elements = self.page.locator(
                '[aria-label*="Phone"]'
            )

            count = phone_elements.count()

            for i in range(count):

                try:

                    aria_label = (
                        phone_elements
                        .nth(i)
                        .get_attribute(
                            "aria-label"
                        )
                    )

                    if not aria_label:
                        continue

                    match = re.search(
                        r'(?:Phone:\s*)?'
                        r'(\+?[\d\s().-]{10,})',
                        aria_label
                    )

                    if match:

                        phone = (
                            match.group(1)
                            .strip()
                        )

                        digits = re.sub(
                            r"\D",
                            "",
                            phone
                        )

                        if 10 <= len(digits) <= 12:
                            return phone

                except Exception:
                    continue

        except Exception as e:

            print(
                f"Phone enrichment error: {e}"
            )

        return ""

    # ==================================================
    # WEBSITE
    # ==================================================

    def find_website(self):
        """
        Find the business website from Google Maps.
        """

        try:

            links = self.page.locator(
                'a[href]'
            )

            count = links.count()

            for i in range(count):

                try:

                    href = (
                        links
                        .nth(i)
                        .get_attribute(
                            "href"
                        )
                    )

                    if not href:
                        continue

                    # Google internal links are ignored
                    if "google.com" in href:
                        continue

                    parsed = urlparse(
                        href
                    )

                    if parsed.scheme in (
                        "http",
                        "https"
                    ):

                        return href

                except Exception:
                    continue

        except Exception as e:

            print(
                f"Website enrichment error: {e}"
            )

        return ""

    # ==================================================
    # ADDRESS
    # ==================================================

    def find_address(self):
        """
        Find business address from Google Maps.
        """

        try:

            # Google Maps address button
            address_elements = self.page.locator(
                'button[data-item-id*="address"]'
            )

            count = (
                address_elements.count()
            )

            for i in range(count):

                try:

                    text = (
                        address_elements
                        .nth(i)
                        .inner_text()
                        .strip()
                    )

                    if text:
                        return text

                except Exception:
                    continue

        except Exception as e:

            print(
                f"Address enrichment error: {e}"
            )

        return ""

    # ==================================================
    # ENRICH SINGLE LEAD
    # ==================================================

    def enrich_lead(self, lead):
        """
        Enrich only missing fields.
        """

        print(
            f"\nEnriching: "
            f"{lead.get('business_name')}"
        )

        # --------------------------------------------------
        # PHONE
        # --------------------------------------------------

        if not lead.get("phone"):

            phone = self.find_phone()

            if phone:

                lead["phone"] = phone

                print(
                    f"Phone found: {phone}"
                )

        # --------------------------------------------------
        # WEBSITE
        # --------------------------------------------------

        if not lead.get("website"):

            website = self.find_website()

            if website:

                lead["website"] = website

                print(
                    f"Website found: {website}"
                )

        # --------------------------------------------------
        # ADDRESS
        # --------------------------------------------------

        if not lead.get("address"):

            address = self.find_address()

            if address:

                lead["address"] = address

                print(
                    f"Address found: {address}"
                )

        return lead

    # ==================================================
    # ENRICH MULTIPLE LEADS
    # ==================================================

    def enrich_leads(self, leads):
        """
        Enrich a list of leads.
        """

        enriched = []

        for lead in leads:

            try:

                lead = self.enrich_lead(
                    lead
                )

                enriched.append(
                    lead
                )

            except Exception as e:

                print(
                    f"Error enriching "
                    f"{lead.get('business_name')}: "
                    f"{e}"
                )

                enriched.append(
                    lead
                )

        return enriched