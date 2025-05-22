from flask import request, render_template, redirect, url_for
from app import application # Assuming 'application' is your Flask app instance defined in app/__init__.py
from test_image_searchers import SmartAirbnbScraper, SerpApiGoogleImageSearch # Correct imports

@application.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        airbnb_url = request.form.get("airbnb_url")
        if airbnb_url:
            # Instead of redirecting, you might want to trigger the Celery task here
            # and redirect to a page that polls for results.
            # For now, let's keep the redirect for simplicity of fixing the immediate error.
            return redirect(url_for("results_page", url=airbnb_url)) # Changed route name slightly for clarity
        else:
            return render_template("home.html", error="Please enter a valid Airbnb URL.")
    return render_template("home.html")

# This route will display the results.
# The actual scraping should ideally be in a background task.
@application.route("/results_page", methods=["GET"]) # Renamed for clarity
def results_page():
    airbnb_url_from_user = request.args.get("url")
    if not airbnb_url_from_user:
        return render_template("results.html", data=[], image_url=None, error="No URL provided.")

    # --- Use your NEW classes and methods ---
    airbnb_smart_scraper = SmartAirbnbScraper()
    # The get_listing_details method returns a dictionary
    listing_details = airbnb_smart_scraper.get_listing_details(airbnb_url_from_user)

    main_image_to_search = None
    if listing_details and listing_details.get("main_image_url"):
        main_image_to_search = listing_details["main_image_url"]
    else:
        error_message = "Could not retrieve primary image or details from the Airbnb URL."
        if listing_details and listing_details.get("error"): # If your scraper class sets an error
             error_message = listing_details["error"]
        return render_template("results.html", data=[], image_url=None, error=error_message)

    # Now use the SerpApiGoogleImageSearch
    # Ensure SERPAPI_API_KEY is set as an environment variable
    # (The SerpApiGoogleImageSearch class constructor will try to load it)
    try:
        serp_api_searcher = SerpApiGoogleImageSearch() # API key should be handled by the class
        target_ota_domains = ['vrbo.com', 'booking.com'] # Define your target sites
        
        alternative_urls = serp_api_searcher.search_by_image(
            main_image_to_search,
            target_domains=target_ota_domains
        )
        # 'alternative_urls' is now a list of strings.
        # You might want to structure it better for the template, e.g., list of dicts
        # For now, just pass it as 'data'
        return render_template("results.html", data=alternative_urls, image_url=main_image_to_search, airbnb_details=listing_details)

    except ValueError as ve: # Handles API key not found error from SerpApiGoogleImageSearch
        return render_template("results.html", data=[], image_url=main_image_to_search, error=str(ve))
    except Exception as e:
        # Catch other potential errors during the API call
        error_msg = f"An error occurred during the search: {e}"
        print(error_msg) # Log it for debugging
        return render_template("results.html", data=[], image_url=main_image_to_search, error=error_msg)