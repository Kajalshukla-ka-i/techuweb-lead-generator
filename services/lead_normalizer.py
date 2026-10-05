from database.mongodb import MongoDB


class LeadNormalizer:

    def __init__(self, db):
        self.db = db
        self.collection = db.collection

    # =========================================================
    # NORMALIZATION
    # =========================================================

    def normalize_website(self, value):
        """
        Normalize website values.

        Valid URL -> keep
        True/False/None/empty -> ""
        """

        if value is None:
            return ""

        if isinstance(value, bool):
            return ""

        if isinstance(value, str):
            value = value.strip()

            if not value:
                return ""

            return value

        return ""

    def normalize_phone(self, value):
        """
        Normalize phone number into digits only.
        """

        if value is None:
            return ""

        if isinstance(value, bool):
            return ""

        value = str(value).strip()

        if not value:
            return ""

        return "".join(
            char for char in value
            if char.isdigit()
        )

    def normalize_text(self, value):
        """
        Normalize text fields.
        """

        if value is None:
            return ""

        if isinstance(value, bool):
            return ""

        return str(value).strip()

    # =========================================================
    # DATA QUALITY
    # =========================================================

    def calculate_data_quality(self, lead):
        """
        Calculate missing fields and data status.
        """

        missing_fields = []

        business_name = self.normalize_text(
            lead.get("business_name")
        )

        category = self.normalize_text(
            lead.get("category")
        )

        city = self.normalize_text(
            lead.get("city")
        )

        phone = self.normalize_phone(
            lead.get("phone")
        )

        website = self.normalize_website(
            lead.get("website")
        )

        address = self.normalize_text(
            lead.get("address")
        )

        if not business_name:
            missing_fields.append("business_name")

        if not category:
            missing_fields.append("category")

        if not city:
            missing_fields.append("city")

        if not phone:
            missing_fields.append("phone")

        if not website:
            missing_fields.append("website")

        if not address:
            missing_fields.append("address")

        data_status = (
            "COMPLETE"
            if not missing_fields
            else "INCOMPLETE"
        )

        return {
            "missing_fields": missing_fields,
            "data_status": data_status
        }

    # =========================================================
    # LEAD SCORE
    # =========================================================

    def calculate_lead_score(self, lead):
        """
        Recalculate lead score.
        """

        score = 0

        rating = lead.get("rating")
        reviews = lead.get("reviews")

        phone = self.normalize_phone(
            lead.get("phone")
        )

        website = self.normalize_website(
            lead.get("website")
        )

        address = self.normalize_text(
            lead.get("address")
        )

        # Rating
        try:
            rating = float(rating)
        except (TypeError, ValueError):
            rating = 0

        if rating >= 4.8:
            score += 25
        elif rating >= 4.5:
            score += 20
        elif rating >= 4.0:
            score += 15
        elif rating >= 3.5:
            score += 10

        # Phone
        if phone:
            score += 20

        # Website
        if website:
            score += 10
        else:
            score += 25

        # Reviews
        try:
            reviews = int(reviews)
        except (TypeError, ValueError):
            reviews = 0

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

        # Address
        if address:
            score += 5

        return min(score, 100)

    # =========================================================
    # OPPORTUNITY
    # =========================================================

    def calculate_opportunity(self, score, website):
        """
        Calculate sales opportunity.
        """

        website = self.normalize_website(
            website
        )

        if score >= 70:
            return "HIGH"

        if not website:
            return "HIGH"

        if score >= 50:
            return "MEDIUM"

        return "LOW"

    # =========================================================
    # ANALYZE LEAD
    # =========================================================

    def analyze_lead(self, lead):
        """
        Analyze one lead.

        IMPORTANT:
        This does not modify MongoDB.
        """

        changes = {}

        normalized = lead.copy()

        # -------------------------
        # Normalize basic fields
        # -------------------------

        normalized["website"] = (
            self.normalize_website(
                lead.get("website")
            )
        )

        normalized["phone"] = (
            self.normalize_phone(
                lead.get("phone")
            )
        )

        text_fields = [
            "business_name",
            "category",
            "city",
            "state",
            "address",
            "email",
            "keyword",
            "status",
            "source"
        ]

        for field in text_fields:
            normalized[field] = (
                self.normalize_text(
                    lead.get(field)
                )
            )

        # -------------------------
        # Data quality
        # -------------------------

        quality = self.calculate_data_quality(
            normalized
        )

        normalized["missing_fields"] = (
            quality["missing_fields"]
        )

        normalized["data_status"] = (
            quality["data_status"]
        )

        # -------------------------
        # Phone validity
        # -------------------------

        phone = normalized["phone"]

        normalized["valid_phone"] = (
            True
            if 10 <= len(phone) <= 12
            else False
        )

        # -------------------------
        # Lead score
        # -------------------------

        normalized["lead_score"] = (
            self.calculate_lead_score(
                normalized
            )
        )

        # -------------------------
        # Opportunity
        # -------------------------

        normalized["opportunity"] = (
            self.calculate_opportunity(
                normalized["lead_score"],
                normalized["website"]
            )
        )

        # -------------------------
        # Detect changes
        # -------------------------

        fields_to_check = [
            "website",
            "phone",
            "email",
            "address",
            "business_name",
            "category",
            "city",
            "state",
            "keyword",
            "status",
            "source",
            "missing_fields",
            "data_status",
            "valid_phone",
            "lead_score",
            "opportunity"
        ]

        for field in fields_to_check:

            old_value = lead.get(field)
            new_value = normalized.get(field)

            if old_value != new_value:

                changes[field] = {
                    "old": old_value,
                    "new": new_value
                }

        return changes

    # =========================================================
    # DUPLICATE DETECTION
    # =========================================================

    def find_duplicate_candidates(self, leads):
        """
        Find possible duplicate leads.

        This function ONLY reports candidates.
        It does not delete or merge anything.
        """

        candidates = []

        for i in range(len(leads)):

            lead_a = leads[i]

            for j in range(i + 1, len(leads)):

                lead_b = leads[j]

                name_a = (
                    self.normalize_text(
                        lead_a.get("business_name")
                    ).lower()
                )

                name_b = (
                    self.normalize_text(
                        lead_b.get("business_name")
                    ).lower()
                )

                city_a = (
                    self.normalize_text(
                        lead_a.get("city")
                    ).lower()
                )

                city_b = (
                    self.normalize_text(
                        lead_b.get("city")
                    ).lower()
                )

                phone_a = self.normalize_phone(
                    lead_a.get("phone")
                )

                phone_b = self.normalize_phone(
                    lead_b.get("phone")
                )

                address_a = (
                    self.normalize_text(
                        lead_a.get("address")
                    ).lower()
                )

                address_b = (
                    self.normalize_text(
                        lead_b.get("address")
                    ).lower()
                )

                maps_a = self.normalize_text(
                    lead_a.get("maps_url")
                )

                maps_b = self.normalize_text(
                    lead_b.get("maps_url")
                )

                reasons = []

                # Same business name + city
                if (
                    name_a
                    and name_b
                    and name_a == name_b
                    and city_a
                    and city_a == city_b
                ):
                    reasons.append(
                        "same business name + city"
                    )

                # Same business name + phone
                if (
                    name_a
                    and name_b
                    and name_a == name_b
                    and phone_a
                    and phone_b
                    and phone_a == phone_b
                ):
                    reasons.append(
                        "same business name + phone"
                    )

                # Same Maps URL
                if (
                    maps_a
                    and maps_b
                    and maps_a == maps_b
                ):
                    reasons.append(
                        "same maps URL"
                    )

                # Same business name + address
                if (
                    name_a
                    and name_b
                    and name_a == name_b
                    and address_a
                    and address_b
                    and address_a == address_b
                ):
                    reasons.append(
                        "same business name + address"
                    )

                if reasons:

                    candidates.append({
                        "lead_1": lead_a.get(
                            "business_name"
                        ),
                        "lead_2": lead_b.get(
                            "business_name"
                        ),
                        "city_1": lead_a.get("city"),
                        "city_2": lead_b.get("city"),
                        "phone_1": lead_a.get("phone"),
                        "phone_2": lead_b.get("phone"),
                        "address_1": lead_a.get(
                            "address"
                        ),
                        "address_2": lead_b.get(
                            "address"
                        ),
                        "maps_url_1": maps_a,
                        "maps_url_2": maps_b,
                        "reasons": reasons
                    })

        return candidates

    # =========================================================
    # DRY RUN
    # =========================================================

    def dry_run(self):

        leads = list(
            self.collection.find(
                {},
                {"_id": 0}
            )
        )

        print("=" * 80)
        print("TECHUWEB LEAD NORMALIZER - DRY RUN")
        print("=" * 80)

        print(
            f"\nTotal Leads: {len(leads)}"
        )

        # -----------------------------------------------------
        # NORMALIZATION REPORT
        # -----------------------------------------------------

        print("\n" + "=" * 80)
        print("DATA NORMALIZATION REPORT")
        print("=" * 80)

        normalization_count = 0
        score_change_count = 0

        for index, lead in enumerate(
            leads,
            start=1
        ):

            changes = self.analyze_lead(
                lead
            )

            if changes:

                normalization_count += 1

                print(
                    f"\nLead {index}: "
                    f"{lead.get('business_name')}"
                )

                for field, change in changes.items():

                    print(
                        f"  {field}: "
                        f"{change['old']!r} "
                        f"-> "
                        f"{change['new']!r}"
                    )

                if "lead_score" in changes:
                    score_change_count += 1

        print(
            f"\nLeads requiring normalization: "
            f"{normalization_count}"
        )

        print(
            f"Leads requiring score recalculation: "
            f"{score_change_count}"
        )

        # -----------------------------------------------------
        # DUPLICATE REPORT
        # -----------------------------------------------------

        print("\n" + "=" * 80)
        print("DUPLICATE CANDIDATE REPORT")
        print("=" * 80)

        duplicates = (
            self.find_duplicate_candidates(
                leads
            )
        )

        print(
            f"\nDuplicate candidates: "
            f"{len(duplicates)}"
        )

        for index, duplicate in enumerate(
            duplicates,
            start=1
        ):

            print(
                f"\nDuplicate Candidate {index}"
            )

            print(
                f"  Lead 1    : "
                f"{duplicate['lead_1']}"
            )

            print(
                f"  Lead 2    : "
                f"{duplicate['lead_2']}"
            )

            print(
                f"  City 1    : "
                f"{duplicate['city_1']}"
            )

            print(
                f"  City 2    : "
                f"{duplicate['city_2']}"
            )

            print(
                f"  Phone 1   : "
                f"{duplicate['phone_1']}"
            )

            print(
                f"  Phone 2   : "
                f"{duplicate['phone_2']}"
            )

            print(
                f"  Address 1 : "
                f"{duplicate['address_1']}"
            )

            print(
                f"  Address 2 : "
                f"{duplicate['address_2']}"
            )

            print(
                f"  Reason    : "
                f"{', '.join(duplicate['reasons'])}"
            )

        # -----------------------------------------------------
        # SAFETY
        # -----------------------------------------------------

        print("\n" + "=" * 80)
        print("DRY RUN COMPLETED")
        print("=" * 80)

        print(
            "\nNO DATABASE DATA WAS MODIFIED."
        )

        print(
            "NO RECORDS WERE DELETED."
        )

        print(
            "NO RECORDS WERE MERGED."
        )


def main():

    db = MongoDB()

    try:

        normalizer = LeadNormalizer(db)

        normalizer.dry_run()

    except Exception as e:

        print("\n❌ NORMALIZER ERROR")

        print(
            f"{type(e).__name__}: {e}"
        )

    finally:

        db.close()

        print(
            "\nMongoDB Connection Closed"
        )


if __name__ == "__main__":
    main()