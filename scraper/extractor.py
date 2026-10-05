from playwright.sync_api import Page
from urllib.parse import urlparse, unquote
import re


class BusinessExtractor:
    """
    Extract and clean business details from the
    currently opened Google Maps business page.
    """

    def __init__(self, page: Page):
        self.page = page

    # ==================================================
    # BUSINESS NAME
    # ==================================================

    def extract_business_name(self):
        """
        Extract business name from Google Maps URL.
        """

        try:
            current_url = self.page.url

            parsed_url = urlparse(current_url)
            path = unquote(parsed_url.path)

            if "/maps/place/" in path:

                name_part = path.split(
                    "/maps/place/",
                    1
                )[1]

                name_part = name_part.split(
                    "/",
                    1
                )[0]

                business_name = (
                    name_part
                    .replace("+", " ")
                    .strip()
                )

                if business_name:
                    return business_name

        except Exception as e:
            print(
                f"Business name extraction error: {e}"
            )

        return ""

    # ==================================================
    # CATEGORY
    # ==================================================

    def extract_category(self):
        """
        Extract business category from Google Maps.
        """

        try:

            possible_categories = self.page.locator(
                'button[jsaction*="category"]'
            )

            count = possible_categories.count()

            for i in range(count):

                try:

                    category = (
                        possible_categories
                        .nth(i)
                        .inner_text()
                        .strip()
                    )

                    if category:
                        return category

                except Exception:
                    continue

        except Exception as e:
            print(
                f"Category extraction error: {e}"
            )

        return ""

    # ==================================================
    # RATING
    # ==================================================

    def extract_rating(self):
        """
        Extract business rating from Google Maps.
        """

        try:

            rating_elements = self.page.locator(
                '[role="img"][aria-label*="stars"]'
            )

            count = rating_elements.count()

            for i in range(count):

                try:

                    aria_label = (
                        rating_elements
                        .nth(i)
                        .get_attribute("aria-label")
                    )

                    if not aria_label:
                        continue

                    match = re.search(
                        r'(\d+(?:\.\d+)?)',
                        aria_label
                    )

                    if match:

                        rating = float(
                            match.group(1)
                        )

                        if 0 <= rating <= 5:
                            return rating

                except Exception:
                    continue

        except Exception as e:
            print(
                f"Rating extraction error: {e}"
            )

        return None

    # ==================================================
    # REVIEWS
    # ==================================================

    def extract_reviews(self):
        """
        Extract number of reviews from Google Maps.
        """

        try:

            # ------------------------------------------
            # Method 1: aria-label
            # ------------------------------------------

            review_elements = self.page.locator(
                '[aria-label*="review"]'
            )

            count = review_elements.count()

            for i in range(count):

                try:

                    aria_label = (
                        review_elements
                        .nth(i)
                        .get_attribute("aria-label")
                    )

                    if not aria_label:
                        continue

                    match = re.search(
                        r'([\d,]+)\s+reviews?',
                        aria_label,
                        re.IGNORECASE
                    )

                    if match:

                        reviews = (
                            match.group(1)
                            .replace(",", "")
                        )

                        return int(reviews)

                except Exception:
                    continue

            # ------------------------------------------
            # Method 2: visible page text
            # ------------------------------------------

            body_text = self.page.locator(
                "body"
            ).inner_text()

            for line in body_text.split("\n"):

                line = line.strip()

                if "review" not in line.lower():
                    continue

                match = re.search(
                    r'([\d,]+)\s+reviews?',
                    line,
                    re.IGNORECASE
                )

                if match:

                    reviews = (
                        match.group(1)
                        .replace(",", "")
                    )

                    return int(reviews)

        except Exception as e:
            print(
                f"Review extraction error: {e}"
            )

        return None

    # ==================================================
    # PHONE
    # ==================================================

    def extract_phone(self):
        """
        Extract and normalize Indian phone number
        from Google Maps.
        """

        try:

            # ------------------------------------------
            # Method 1: aria-label
            # ------------------------------------------

            phone_elements = self.page.locator(
                '[aria-label*="Phone"]'
            )

            count = phone_elements.count()

            for i in range(count):

                try:

                    aria_label = (
                        phone_elements
                        .nth(i)
                        .get_attribute("aria-label")
                    )

                    if not aria_label:
                        continue

                    print(
                        f"Phone aria-label: {aria_label}"
                    )

                    match = re.search(
                        r'(?:\+91[\s-]?)?'
                        r'[6-9][\d\s-]{9,}',
                        aria_label
                    )

                    if match:

                        phone = re.sub(
                            r"\D",
                            "",
                            match.group(0)
                        )

                        # Remove country code
                        if (
                            phone.startswith("91")
                            and len(phone) > 10
                        ):
                            phone = phone[-10:]

                        if len(phone) == 10:
                            return phone

                except Exception:
                    continue

            # ------------------------------------------
            # Method 2: visible page text
            # ------------------------------------------

            body_text = self.page.locator(
                "body"
            ).inner_text()

            # Search numbers even if spaces/dashes exist
            possible_numbers = re.findall(
                r'(?:\+91[\s-]?)?'
                r'[6-9][\d\s-]{9,}',
                body_text
            )

            for number in possible_numbers:

                phone = re.sub(
                    r"\D",
                    "",
                    number
                )

                if (
                    phone.startswith("91")
                    and len(phone) > 10
                ):
                    phone = phone[-10:]

                if len(phone) == 10:
                    return phone

        except Exception as e:
            print(
                f"Phone extraction error: {e}"
            )

        return ""

    # ==================================================
    # WEBSITE
    # ==================================================

    def extract_website(self):
        """
        Extract the actual business website.

        Avoid:
        - Google links
        - Booking websites
        - Social media
        - Directory websites
        - Tracking websites
        """

        try:

            website_links = self.page.locator(
                'a[href]'
            )

            count = website_links.count()

            blocked_domains = [

                # Google
                "google.com",
                "google.co.in",
                "google.co.uk",
                "googleusercontent.com",
                "googleapis.com",

                # Booking / third-party
                "luzo.app",

                # Social media
                "facebook.com",
                "instagram.com",
                "youtube.com",
                "linkedin.com",

                # Messaging
                "wa.me",
                "whatsapp.com",

                # Directories
                "justdial.com",
                "zomato.com",
                "swiggy.com"
            ]

            for i in range(count):

                try:

                    href = (
                        website_links
                        .nth(i)
                        .get_attribute("href")
                    )

                    if not href:
                        continue

                    href = href.strip()

                    if not href.startswith(
                        ("http://", "https://")
                    ):
                        continue

                    lower_href = href.lower()

                    # Ignore blocked domains
                    if any(
                        domain in lower_href
                        for domain in blocked_domains
                    ):
                        continue

                    return href

                except Exception:
                    continue

        except Exception as e:
            print(
                f"Website extraction error: {e}"
            )

        return ""

    # ==================================================
    # ADDRESS
    # ==================================================

    def extract_address(self):
        """
        Extract and clean business address
        from Google Maps.
        """

        try:

            address_elements = self.page.locator(
                'button[data-item-id="address"]'
            )

            count = address_elements.count()

            for i in range(count):

                try:

                    address = (
                        address_elements
                        .nth(i)
                        .inner_text()
                        .strip()
                    )

                    if not address:
                        continue

                    # Remove Google Maps icon
                    address = address.replace(
                        "\ue0c8",
                        ""
                    )

                    # Remove line breaks
                    address = address.replace(
                        "\n",
                        " "
                    )

                    # Normalize spaces
                    address = re.sub(
                        r"\s+",
                        " ",
                        address
                    ).strip()

                    if address:
                        return address

                except Exception:
                    continue

        except Exception as e:
            print(
                f"Address extraction error: {e}"
            )

        return ""

    # ==================================================
    # DATA QUALITY
    # ==================================================

    def check_missing_fields(self, lead):
        """
        Identify important missing fields.

        This does not reject the lead.
        It marks incomplete data for later
        Excel highlighting.
        """

        missing_fields = []

        if not lead.get("phone"):
            missing_fields.append("Phone")

        if not lead.get("website"):
            missing_fields.append("Website")

        if not lead.get("address"):
            missing_fields.append("Address")

        if missing_fields:

            lead["data_status"] = "INCOMPLETE"

            lead["missing_fields"] = ", ".join(
                missing_fields
            )

        else:

            lead["data_status"] = "COMPLETE"

            lead["missing_fields"] = ""

        return lead

    # ==================================================
    # EXTRACT ALL DETAILS
    # ==================================================

    def extract_details(self):
        """
        Extract all supported business details
        and check data quality.
        """

        lead = {

            "business_name":
                self.extract_business_name(),

            "category":
                self.extract_category(),

            "rating":
                self.extract_rating(),

            "reviews":
                self.extract_reviews(),

            "phone":
                self.extract_phone(),

            "website":
                self.extract_website(),

            "address":
                self.extract_address(),

            "maps_url":
                self.page.url
        }

        # Check for missing information
        lead = self.check_missing_fields(
            lead
        )

        return lead