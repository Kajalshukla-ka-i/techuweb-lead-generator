from scraper.scraper import scrape_google_maps
from services.parser import clean_data
from services.validator import validate_all
from services.excel import save_excel
from services.logger import logger
from database.mongodb import MongoDB


# ==================================================
# MAIN APPLICATION
# ==================================================

def main():

    db = None

    try:

        # ==================================================
        # USER INPUT
        # ==================================================

        keyword = input(
            "Enter keyword (Example: Dental Clinic Faridabad): "
        ).strip()

        if not keyword:

            print(
                "❌ Keyword cannot be empty."
            )

            logger.warning(
                "Lead generation stopped: Empty keyword"
            )

            return

        logger.info(
            f"Lead generation started | Keyword: {keyword}"
        )

        # ==================================================
        # CATEGORY + CITY
        # ==================================================

        words = keyword.split()

        if len(words) < 2:

            print(
                "❌ Please enter category and city."
            )

            logger.warning(
                f"Invalid keyword: {keyword}"
            )

            return

        city = words[-1]

        category = " ".join(
            words[:-1]
        )

        logger.info(
            f"Category: {category} | City: {city}"
        )

        # ==================================================
        # MONGODB CONNECTION
        # ==================================================

        db = MongoDB()

        logger.info(
            "MongoDB connection established"
        )

        print(
            "\n🔎 Starting Google Maps scraping..."
        )

        # ==================================================
        # SCRAPE GOOGLE MAPS
        # ==================================================

        raw_leads = scrape_google_maps(
            keyword
        )

        if not raw_leads:

            print(
                "❌ No leads found."
            )

            logger.warning(
                f"No leads found | Keyword: {keyword}"
            )

            return

        logger.info(
            f"Raw leads scraped: {len(raw_leads)}"
        )

        # ==================================================
        # PARSE / CLEAN DATA
        # ==================================================

        parsed_leads = clean_data(
            raw_leads
        )

        logger.info(
            f"Leads parsed: {len(parsed_leads)}"
        )

        # ==================================================
        # ADD METADATA
        # ==================================================

        for lead in parsed_leads:

            lead["keyword"] = keyword

            lead["category"] = category

            lead["city"] = city

            lead["source"] = "Google Maps"

        # ==================================================
        # VALIDATE LEADS
        # ==================================================

        validated_leads = validate_all(
            parsed_leads
        )

        print(
            f"\nValidated {len(validated_leads)} leads"
        )

        logger.info(
            f"Leads validated: {len(validated_leads)}"
        )

        # ==================================================
        # SAVE TO MONGODB
        # ==================================================

        db.save_leads(
            validated_leads
        )

        print(
            "✅ Saved to MongoDB"
        )

        logger.info(
            "MongoDB save operation completed"
        )

        # ==================================================
        # EXPORT TO EXCEL
        # ==================================================

        save_excel(
            validated_leads,
            keyword
        )

        print(
            "✅ Excel Exported Successfully"
        )

        logger.info(
            "Excel export completed successfully"
        )

        # ==================================================
        # SUCCESS
        # ==================================================

        print(
            "\n🎉 Lead Generation Completed Successfully!"
        )

        logger.info(
            f"Lead generation completed successfully | "
            f"Keyword: {keyword}"
        )

    # ==================================================
    # ERROR HANDLING
    # ==================================================

    except Exception as e:

        print(
            f"\n❌ Error: {e}"
        )

        logger.exception(
            "Lead generation failed"
        )

    # ==================================================
    # CLOSE DATABASE
    # ==================================================

    finally:

        if db:

            db.close()

            logger.info(
                "MongoDB connection closed"
            )


# ==================================================
# RUN APPLICATION
# ==================================================

if __name__ == "__main__":

    main()