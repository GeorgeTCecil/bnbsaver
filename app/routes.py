from flask import request, render_template, redirect, url_for
from app import application
from scraper import AirbnbImageScraper, GoogleImageSearch

@application.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        airbnb_url = request.form.get("airbnb_url")
        if airbnb_url:
            return redirect(url_for("results", url=airbnb_url))
        else:
            return render_template("home.html", error="Please enter a valid Airbnb URL.")
    return render_template("home.html")

@application.route("/results", methods=["GET"])
def results():
    airbnb_url = request.args.get("url")
    if not airbnb_url:
        return render_template("results.html", data=[], image_url=None, error="No URL provided.")

    airbnb_scraper = AirbnbImageScraper()
    first_image_url = airbnb_scraper.fetch_first_image_link(airbnb_url)

    if first_image_url:
        google_search = GoogleImageSearch()
        search_results = google_search.search_by_image(first_image_url)
        return render_template("results.html", data=search_results, image_url=first_image_url)
    else:
        return render_template("results.html", data=[], image_url=None, error="No image found for the given URL.")
