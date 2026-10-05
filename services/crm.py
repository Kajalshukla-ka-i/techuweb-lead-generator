from datetime import datetime


class CRMService:

    def __init__(self, db):

        self.db = db
        self.collection = db.collection

    # ==================================================
    # GET LEAD
    # ==================================================

    def get_lead(self, business_name):

        return self.collection.find_one(
            {
                "business_name": business_name
            },
            {
                "_id": 0
            }
        )

    # ==================================================
    # UPDATE LEAD STATUS
    # ==================================================

    def update_status(
        self,
        business_name,
        status
    ):

        allowed_statuses = [
            "NEW",
            "CONTACTED",
            "INTERESTED",
            "CONVERTED",
            "LOST"
        ]

        status = status.upper()

        if status not in allowed_statuses:

            print(
                f"Invalid status: {status}"
            )

            return False

        result = self.collection.update_one(

            {
                "business_name": business_name
            },

            {
                "$set": {
                    "status": status,
                    "updated_at": datetime.utcnow()
                }
            }
        )

        if result.modified_count > 0:

            print(
                f"Status updated: "
                f"{business_name} → {status}"
            )

            return True

        print(
            f"Lead not found: "
            f"{business_name}"
        )

        return False

    # ==================================================
    # UPDATE NOTES
    # ==================================================

    def update_notes(
        self,
        business_name,
        notes
    ):

        result = self.collection.update_one(

            {
                "business_name": business_name
            },

            {
                "$set": {
                    "notes": notes,
                    "updated_at": datetime.utcnow()
                }
            }
        )

        if result.modified_count > 0:

            print(
                f"Notes updated for: "
                f"{business_name}"
            )

            return True

        print(
            f"Lead not found: "
            f"{business_name}"
        )

        return False

    # ==================================================
    # ASSIGN LEAD
    # ==================================================

    def assign_lead(
        self,
        business_name,
        assigned_to
    ):

        result = self.collection.update_one(

            {
                "business_name": business_name
            },

            {
                "$set": {
                    "assigned_to": assigned_to,
                    "updated_at": datetime.utcnow()
                }
            }
        )

        if result.modified_count > 0:

            print(
                f"Lead assigned: "
                f"{business_name} → {assigned_to}"
            )

            return True

        print(
            f"Lead not found: "
            f"{business_name}"
        )

        return False

    # ==================================================
    # UPDATE EMAIL
    # ==================================================

    def update_email(
        self,
        business_name,
        email
    ):

        result = self.collection.update_one(

            {
                "business_name": business_name
            },

            {
                "$set": {
                    "email": email,
                    "updated_at": datetime.utcnow()
                }
            }
        )

        return result.modified_count > 0

    # ==================================================
    # UPDATE PHONE
    # ==================================================

    def update_phone(
        self,
        business_name,
        phone
    ):

        result = self.collection.update_one(

            {
                "business_name": business_name
            },

            {
                "$set": {
                    "phone": phone,
                    "updated_at": datetime.utcnow()
                }
            }
        )

        return result.modified_count > 0

    # ==================================================
    # UPDATE WEBSITE
    # ==================================================

    def update_website(
        self,
        business_name,
        website
    ):

        result = self.collection.update_one(

            {
                "business_name": business_name
            },

            {
                "$set": {
                    "website": website,
                    "updated_at": datetime.utcnow()
                }
            }
        )

        return result.modified_count > 0

    # ==================================================
    # DELETE LEAD
    # ==================================================

    def delete_lead(
        self,
        business_name
    ):

        result = self.collection.delete_one(

            {
                "business_name": business_name
            }
        )

        if result.deleted_count > 0:

            print(
                f"Lead deleted: "
                f"{business_name}"
            )

            return True

        print(
            f"Lead not found: "
            f"{business_name}"
        )

        return False