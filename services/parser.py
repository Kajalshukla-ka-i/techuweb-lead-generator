import re

from models.lead import Lead


# ==================================================
# PHONE EXTRACTION FROM RAW TEXT
# ==================================================

def extract_phone(text):
    """
    Extract phone number from raw Google Maps text.

    This is a fallback only.
    Primary phone data should come from
    BusinessExtractor / LeadEnricher.
    """

    if not text:
        return None

    phones = re.findall(
        r'\b\d{10,12}\b',
        text.replace(" ", "")
    )

    if phones:
        return phones[0]

    return None


# ==================================================
# RATING EXTRACTION FROM RAW TEXT
# ==================================================

def extract_rating(text):
    """
    Extract rating from raw Google Maps card text.
    """

    if not text:
        return None

    match = re.search(
        r'(\d\.\d)',
        text
    )

    if match:
        return float(
            match.group(1)
        )

    return None


# ==================================================
# CATEGORY EXTRACTION
# ==================================================

def extract_category(text):
    """
    Try to extract category from raw card text.
    """

    if not text:
        return None

    lines = [
        line.strip()
        for line in text.split("\n")
        if line.strip()
    ]

    for line in lines:

        lower_line = line.lower()

        categories = [
            "restaurant",
            "beauty parlour",
            "beauty salon",
            "salon",
            "dental clinic",
            "clinic",
            "hospital",
            "cafe",
            "bar",
            "hotel",
            "gym",
            "school",
        ]

        for category in categories:

            if category in lower_line:
                return line

    return None


# ==================================================
# PARSE SINGLE RESULT
# ==================================================

def parse_clinic(raw_result):
    """
    Convert scraper result into a clean lead.

    IMPORTANT:
    Uses extracted/enriched details first.
    Raw card text is used as fallback.
    """

    raw_text = raw_result.get(
        "text",
        ""
    )

    details = raw_result.get(
        "details",
        {}
    )

    if not isinstance(details, dict):
        details = {}

    # --------------------------------------------------
    # Raw text lines
    # --------------------------------------------------

    lines = [
        x.strip()
        for x in raw_text.split("\n")
        if x.strip()
    ]

    # ==================================================
    # BUSINESS NAME
    # ==================================================

    business_name = details.get(
        "business_name"
    )

    if not business_name:

        business_name = (
            lines[0]
            if lines
            else ""
        )

    # ==================================================
    # RATING
    # ==================================================

    rating = details.get(
        "rating"
    )

    if rating is None:

        rating = extract_rating(
            raw_text
        )

    # ==================================================
    # PHONE
    # ==================================================

    phone = details.get(
        "phone"
    )

    if not phone:

        phone = extract_phone(
            raw_text
        )

    # ==================================================
    # WEBSITE
    # ==================================================

    website = details.get(
        "website"
    )

    if not website:

        website = ""

    # ==================================================
    # ADDRESS
    # ==================================================

    address = details.get(
        "address"
    )

    if not address:

        address = ""

    # ==================================================
    # REVIEWS
    # ==================================================

    reviews = details.get(
        "reviews"
    )

    # ==================================================
    # CATEGORY
    # ==================================================

    category = details.get(
        "category"
    )

    if not category:

        category = extract_category(
            raw_text
        )

    # ==================================================
    # CREATE CLEAN LEAD
    # ==================================================

    lead = {

        "business_name":
            business_name,

        "category":
            category,

        "rating":
            rating,

        "reviews":
            reviews,

        "phone":
            phone,

        "website":
            website,

        "address":
            address,

        "maps_url":
            details.get(
                "maps_url",
                ""
            ),

        "email":
            details.get(
                "email"
            ),

        "keyword":
            "",

        "city":
            "",

        "state":
            "",

        "source":
            "Google Maps",

        "status":
            "NEW",

        "assigned_to":
            None,

        "notes":
            "",

        "lead_score":
            0,

        "raw":
            raw_text,

    }

    return lead


# ==================================================
# CLEAN ALL RESULTS
# ==================================================

def clean_data(raw_results):
    """
    Convert all scraped results into clean leads.
    """

    cleaned = []

    for item in raw_results:

        try:

            lead = parse_clinic(
                item
            )

            cleaned.append(
                lead
            )

        except Exception as e:

            print(
                f"Parser error: {e}"
            )

    return cleaned