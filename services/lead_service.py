from datetime import datetime


class LeadService:

    def __init__(self, db):
        self.db = db
        self.collection = db.collection

    # ==================================================
    # GET ALL LEADS
    # ==================================================

    def get_all_leads(self):
        return list(
            self.collection.find(
                {},
                {"_id": 0}
            )
        )

    # ==================================================
    # GET HIGH OPPORTUNITY LEADS
    # ==================================================

    def get_high_opportunity_leads(self):

        return list(
            self.collection.find(
                {
                    "opportunity": "HIGH"
                },
                {
                    "_id": 0
                }
            ).sort(
                "lead_score",
                -1
            )
        )

    # ==================================================
    # GET LEADS WITHOUT WEBSITE
    # ==================================================

    def get_leads_without_website(self):

        return list(
            self.collection.find(
                {
                    "$or": [
                        {
                            "website": ""
                        },
                        {
                            "website": None
                        },
                        {
                            "website": {
                                "$exists": False
                            }
                        }
                    ]
                },
                {
                    "_id": 0
                }
            )
        )

    # ==================================================
    # GET INCOMPLETE LEADS
    # ==================================================

    def get_incomplete_leads(self):

        return list(
            self.collection.find(
                {
                    "data_status": "INCOMPLETE"
                },
                {
                    "_id": 0
                }
            )
        )

    # ==================================================
    # GET LEADS BY CITY
    # ==================================================

    def get_by_city(self, city):

        return list(
            self.collection.find(
                {
                    "city": city
                },
                {
                    "_id": 0
                }
            )
        )

    # ==================================================
    # GET LEADS BY CATEGORY
    # ==================================================

    def get_by_category(self, category):

        return list(
            self.collection.find(
                {
                    "category": category
                },
                {
                    "_id": 0
                }
            )
        )

    # ==================================================
    # GET LEADS BY STATUS
    # ==================================================

    def get_by_status(self, status):

        return list(
            self.collection.find(
                {
                    "status": status
                },
                {
                    "_id": 0
                }
            )
        )

    # ==================================================
    # GET LEADS BY SCORE
    # ==================================================

    def get_by_score(self, minimum_score=70):

        return list(
            self.collection.find(
                {
                    "lead_score": {
                        "$gte": minimum_score
                    }
                },
                {
                    "_id": 0
                }
            ).sort(
                "lead_score",
                -1
            )
        )

    # ==================================================
    # UPDATE STATUS
    # ==================================================

    def update_status(
        self,
        business_name,
        status
    ):

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

        return result.modified_count > 0

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

        return result.modified_count > 0

    # ==================================================
    # GET STATISTICS
    # ==================================================

    def get_statistics(self):

        total = self.collection.count_documents({})

        high = self.collection.count_documents(
            {
                "opportunity": "HIGH"
            }
        )

        medium = self.collection.count_documents(
            {
                "opportunity": "MEDIUM"
            }
        )

        low = self.collection.count_documents(
            {
                "opportunity": "LOW"
            }
        )

        incomplete = self.collection.count_documents(
            {
                "data_status": "INCOMPLETE"
            }
        )

        without_website = self.collection.count_documents(
            {
                "$or": [
                    {"website": ""},
                    {"website": None},
                    {
                        "website": {
                            "$exists": False
                        }
                    }
                ]
            }
        )

        new = self.collection.count_documents(
            {
                "status": "NEW"
            }
        )

        contacted = self.collection.count_documents(
            {
                "status": "CONTACTED"
            }
        )

        interested = self.collection.count_documents(
            {
                "status": "INTERESTED"
            }
        )

        converted = self.collection.count_documents(
            {
                "status": "CONVERTED"
            }
        )

        return {
            "total": total,
            "high": high,
            "medium": medium,
            "low": low,
            "incomplete": incomplete,
            "without_website": without_website,
            "new": new,
            "contacted": contacted,
            "interested": interested,
            "converted": converted
        }