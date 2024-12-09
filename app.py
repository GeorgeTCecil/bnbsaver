from flask import Flask, request, render_template, redirect, url_for
from scraper import AirbnbImageScraper, GoogleImageSearch  # Import the class from scraper.py

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        airbnb_url = request.form["airbnb_url"]
        return redirect(url_for("results", url=airbnb_url))
    return render_template("home.html")

@app.route('/results', methods=['GET', 'POST'])
def results():
    if request.method == "POST":
        airbnb_url = request.form['airbnb_url']  # URL input from the form
    elif request.method == "GET":
        airbnb_url = request.args.get('url')  # URL passed as query parameter

    airbnb_scraper = AirbnbImageScraper()  # Create an instance of the scraper
    first_image_url = airbnb_scraper.fetch_first_image_link(airbnb_url)  # Call the method
    
    if first_image_url:
        # Perform a Google Image Search for the extracted URL
        google_search = GoogleImageSearch()
        search_results = google_search.search_by_image(first_image_url)
        print("Image searching by...", first_image_url)
        # Pass `first_image_url` to the template
        return render_template('results.html', data=search_results, image_url=first_image_url)
    else:
        print("No image URL found.")
    
    return render_template('results.html', data=[], image_url=None)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

