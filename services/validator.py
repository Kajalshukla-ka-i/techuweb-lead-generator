import re
from datetime import datetime


# ==================================================
# PHONE VALIDATION
# ==================================================

def validate_phone(phone):
    """
    Validate Indian phone number.

    Accepts 10 to 12 digits after removing:
    spaces, +, -, brackets, etc.
    """

    if not phone:
        return False

    phone = re.sub(
        r"\D",
        "",
        str(phone)
    )

    return bool(
        re.fullmatch(
            r"\d{10,12}",
            phone
        )
    )


# ==================================================
# RATING VALIDATION
# ==================================================

def validate_rating(rating):
    """
    Convert rating to float and validate range.
    """

    if rating is None:
        return None

    try:
        rating = float(rating)

        if 0 <= rating <= 5:
            return rating

    except (
        ValueError,
        TypeError
    ):
        pass

    return None


# ==================================================
# REVIEW VALIDATION
# ==================================================

def validate_reviews(reviews):
    """
    Convert review count to integer.
    """

    if reviews is None:
        return None

    try:
        reviews = int(
            str(reviews).replace(
                ",",
                ""
            )
        )

        if reviews >= 0:
            return reviews

    except (
        ValueError,
        TypeError
    ):
        pass

    return None


# ==================================================
# LEAD SCORE
# ==================================================

def calculate_lead_score(lead):
    """
    Calculate lead score based on:

    Rating
    Phone
    Website
    Reviews
    Address

    Maximum score = 100
    """

    score = 0

    # ==================================================
    # RATING
    # ==================================================

    rating = lead.get(
        "rating"
    )

    if rating is not None:

        if rating >= 4.8:
            score += 25

        elif rating >= 4.5:
            score += 20

        elif rating >= 4.0:
            score += 15

        elif rating >= 3.5:
            score += 10

    # ==================================================
    # PHONE
    # ==================================================

    if lead.get(
        "valid_phone"
    ):
        score += 20

    # ==================================================
    # WEBSITE
    # ==================================================

    website = lead.get(
        "website"
    )

    if website:

        # Business already has a website
        score += 10

    else:

        # No website = stronger prospect
        # for Techuweb web-development services
        score += 25

    # ==================================================
    # REVIEWS
    # ==================================================

    reviews = lead.get(
        "reviews"
    )

    if reviews is not None:

        if reviews >= 1000:
            score += 15

        elif reviews >= 500:
            score += 12

        elif reviews >= 100:
            score += 10

        elif reviews >= 50:
            score += 7

        elif reviews > 0:
            score += 5

    # ==================================================
    # ADDRESS
    # ==================================================

    if lead.get(
        "address"
    ):
        score += 5

    # ==================================================
    # MAXIMUM SCORE
    # ==================================================

    return min(
        score,
        100
    )


# ==================================================
# OPPORTUNITY
# ==================================================

def calculate_opportunity(
    lead_score,
    website
):
    """
    Determine lead opportunity.

    HIGH:
        - score >= 70
        - OR no website

    MEDIUM:
        - score >= 50

    LOW:
        - everything else
    """

    if lead_score >= 70:

        return "HIGH"

    elif not website:

        return "HIGH"

    elif lead_score >= 50:

        return "MEDIUM"

    else:

        return "LOW"


# ==================================================
# DATA STATUS
# ==================================================

def calculate_data_status(lead):
    """
    Determine the quality of available lead data.

    COMPLETE:
        Phone + Website + Address available.

    INCOMPLETE:
        One important field is missing.

    LOW_DATA:
        Multiple important fields are missing
        or business name itself is missing.
    """

    missing_fields = []

    # ==================================================
    # PHONE
    # ==================================================

    if not lead.get("phone"):
        missing_fields.append(
            "Phone"
        )

    # ==================================================
    # WEBSITE
    # ==================================================

    if not lead.get("website"):
        missing_fields.append(
            "Website"
        )

    # ==================================================
    # ADDRESS
    # ==================================================

    if not lead.get("address"):
        missing_fields.append(
            "Address"
        )

    # ==================================================
    # DATA STATUS
    # ==================================================

    if not lead.get("business_name"):

        data_status = "LOW_DATA"

    elif len(missing_fields) >= 2:

        data_status = "LOW_DATA"

    elif missing_fields:

        data_status = "INCOMPLETE"

    else:

        data_status = "COMPLETE"

    return (
        data_status,
        ", ".join(missing_fields)
    )


# ==================================================
# VALIDATE SINGLE LEAD
# ==================================================

def validate_lead(lead):

    # ==================================================
    # PHONE
    # ==================================================

    lead["valid_phone"] = validate_phone(
        lead.get("phone")
    )

    # ==================================================
    # RATING
    # ==================================================

    lead["rating"] = validate_rating(
        lead.get("rating")
    )

    # ==================================================
    # REVIEWS
    # ==================================================

    lead["reviews"] = validate_reviews(
        lead.get("reviews")
    )

    # ==================================================
    # DEFAULT CRM FIELDS
    # ==================================================

    lead.setdefault(
        "status",
        "NEW"
    )

    lead.setdefault(
        "assigned_to",
        None
    )

    lead.setdefault(
        "notes",
        ""
    )

    lead.setdefault(
        "source",
        "Google Maps"
    )

    # ==================================================
    # NORMALIZE WEBSITE
    # ==================================================

    # Never store False or None for missing website.
    # Always store empty string.

    if not lead.get("website"):
        lead["website"] = ""

    # ==================================================
    # OTHER CRM FIELDS
    # ==================================================

    lead.setdefault(
        "email",
        None
    )

    lead.setdefault(
        "address",
        ""
    )

    lead.setdefault(
        "city",
        ""
    )

    lead.setdefault(
        "state",
        ""
    )

    lead.setdefault(
        "keyword",
        ""
    )

    # ==================================================
    # LEAD SCORE
    # ==================================================

    lead["lead_score"] = calculate_lead_score(
        lead
    )

    # ==================================================
    # OPPORTUNITY
    # ==================================================

    lead["opportunity"] = calculate_opportunity(
        lead["lead_score"],
        lead["website"]
    )

    # ==================================================
    # DATA STATUS
    # ==================================================

    data_status, missing_fields = calculate_data_status(
        lead
    )

    lead["data_status"] = data_status

    lead["missing_fields"] = missing_fields

    # ==================================================
    # TIMESTAMPS
    # ==================================================

    now = datetime.utcnow()

    # Preserve original creation time.
    # Only create it if this is a new lead.

    if not lead.get("created_at"):
        lead["created_at"] = now

    # Always update the latest modification time.

    lead["updated_at"] = now

    return lead


# ==================================================
# VALIDATE ALL LEADS
# ==================================================

def validate_all(leads):

    validated = []

    for lead in leads:

        validated_lead = validate_lead(
            lead
        )

        # ==================================================
        # DEBUG / SCORE OUTPUT
        # ==================================================

        print(
            "\n===== LEAD SCORE ====="
        )

        print(
            "Business:",
            validated_lead.get(
                "business_name"
            )
        )

        print(
            "Rating:",
            validated_lead.get(
                "rating"
            )
        )

        print(
            "Reviews:",
            validated_lead.get(
                "reviews"
            )
        )

        print(
            "Phone:",
            validated_lead.get(
                "phone"
            )
        )

        print(
            "Website:",
            validated_lead.get(
                "website"
            )
        )

        print(
            "Address:",
            validated_lead.get(
                "address"
            )
        )

        print(
            "Lead Score:",
            validated_lead.get(
                "lead_score"
            )
        )

        print(
            "Opportunity:",
            validated_lead.get(
                "opportunity"
            )
        )

        print(
            "Data Status:",
            validated_lead.get(
                "data_status"
            )
        )

        print(
            "Missing Fields:",
            validated_lead.get(
                "missing_fields"
            )
        )

        print(
            "Valid Phone:",
            validated_lead.get(
                "valid_phone"
            )
        )

        print(
            "Status:",
            validated_lead.get(
                "status"
            )
        )

        # ==================================================
        # ADD TO VALIDATED LIST
        # ==================================================

        validated.append(
            validated_lead
        )

    return validated