import re


class LeadSearchService:

    def __init__(self, db):
        self.db = db
        self.collection = db.collection

    # ==================================================
    # SEARCH LEADS
    # ==================================================

    def search(self, query):
        """
        Search leads by:
        - Business name
        - Phone
        - Email
        - Category
        - City
        """

        if not query:
            return []

        pattern = re.escape(query.strip())

        return list(
            self.collection.find(
                {
                    "$or": [
                        {
                            "business_name": {
                                "$regex": pattern,
                                "$options": "i"
                            }
                        },
                        {
                            "phone": {
                                "$regex": pattern,
                                "$options": "i"
                            }
                        },
                        {
                            "email": {
                                "$regex": pattern,
                                "$options": "i"
                            }
                        },
                        {
                            "category": {
                                "$regex": pattern,
                                "$options": "i"
                            }
                        },
                        {
                            "city": {
                                "$regex": pattern,
                                "$options": "i"
                            }
                        }
                    ]
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
    # FILTER LEADS
    # ==================================================

    def filter_leads(
        self,
        city=None,
        category=None,
        status=None,
        opportunity=None,
        min_score=None,
        has_website=None,
        data_status=None
    ):

        filters = {}

        # ----------------------------------------------
        # CITY
        # ----------------------------------------------

        if city:
            filters["city"] = {
                "$regex": f"^{re.escape(city.strip())}$",
                "$options": "i"
            }

        # ----------------------------------------------
        # CATEGORY
        # ----------------------------------------------

        if category:
            filters["category"] = {
                "$regex": f"^{re.escape(category.strip())}$",
                "$options": "i"
            }

        # ----------------------------------------------
        # STATUS
        # ----------------------------------------------

        if status:
            filters["status"] = status.upper()

        # ----------------------------------------------
        # OPPORTUNITY
        # ----------------------------------------------

        if opportunity:
            filters["opportunity"] = opportunity.upper()

        # ----------------------------------------------
        # MINIMUM SCORE
        # ----------------------------------------------

        if min_score is not None:
            filters["lead_score"] = {
                "$gte": min_score
            }

        # ----------------------------------------------
        # WEBSITE
        # ----------------------------------------------

        if has_website is True:

            filters["website"] = {
                "$exists": True,
                "$nin": ["", None]
            }

        elif has_website is False:

            filters["$or"] = [
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

        # ----------------------------------------------
        # DATA STATUS
        # ----------------------------------------------

        if data_status:
            filters["data_status"] = data_status.upper()

        # ----------------------------------------------
        # GET RESULTS
        # ----------------------------------------------

        return list(
            self.collection.find(
                filters,
                {
                    "_id": 0
                }
            ).sort(
                "lead_score",
                -1
            )
        )

    # ==================================================
    # SEARCH + FILTER
    # ==================================================

    def search_and_filter(
        self,
        query=None,
        city=None,
        category=None,
        status=None,
        opportunity=None,
        min_score=None,
        has_website=None,
        data_status=None
    ):

        filters = []

        # ----------------------------------------------
        # SEARCH QUERY
        # ----------------------------------------------

        if query:
            pattern = re.escape(query.strip())

            filters.append(
                {
                    "$or": [
                        {
                            "business_name": {
                                "$regex": pattern,
                                "$options": "i"
                            }
                        },
                        {
                            "phone": {
                                "$regex": pattern,
                                "$options": "i"
                            }
                        },
                        {
                            "email": {
                                "$regex": pattern,
                                "$options": "i"
                            }
                        },
                        {
                            "category": {
                                "$regex": pattern,
                                "$options": "i"
                            }
                        },
                        {
                            "city": {
                                "$regex": pattern,
                                "$options": "i"
                            }
                        }
                    ]
                }
            )

        # ----------------------------------------------
        # CITY
        # ----------------------------------------------

        if city:
            filters.append(
                {
                    "city": {
                        "$regex": f"^{re.escape(city.strip())}$",
                        "$options": "i"
                    }
                }
            )

        # ----------------------------------------------
        # CATEGORY
        # ----------------------------------------------

        if category:
            filters.append(
                {
                    "category": {
                        "$regex": f"^{re.escape(category.strip())}$",
                        "$options": "i"
                    }
                }
            )

        # ----------------------------------------------
        # STATUS
        # ----------------------------------------------

        if status:
            filters.append(
                {
                    "status": status.upper()
                }
            )

        # ----------------------------------------------
        # OPPORTUNITY
        # ----------------------------------------------

        if opportunity:
            filters.append(
                {
                    "opportunity": opportunity.upper()
                }
            )

        # ----------------------------------------------
        # MINIMUM SCORE
        # ----------------------------------------------

        if min_score is not None:
            filters.append(
                {
                    "lead_score": {
                        "$gte": min_score
                    }
                }
            )

        # ----------------------------------------------
        # WEBSITE
        # ----------------------------------------------

        if has_website is True:

            filters.append(
                {
                    "website": {
                        "$exists": True,
                        "$nin": ["", None]
                    }
                }
            )

        elif has_website is False:

            filters.append(
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
                }
            )

        # ----------------------------------------------
        # DATA STATUS
        # ----------------------------------------------

        if data_status:
            filters.append(
                {
                    "data_status": data_status.upper()
                }
            )

        # ----------------------------------------------
        # FINAL QUERY
        # ----------------------------------------------

        if not filters:

            mongo_query = {}

        elif len(filters) == 1:

            mongo_query = filters[0]

        else:

            mongo_query = {
                "$and": filters
            }

        # ----------------------------------------------
        # RETURN RESULTS
        # ----------------------------------------------

        return list(
            self.collection.find(
                mongo_query,
                {
                    "_id": 0
                }
            ).sort(
                "lead_score",
                -1
            )
        )