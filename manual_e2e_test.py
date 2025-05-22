# manual_e2e_test.py
import os
from dotenv import load_dotenv
import sys # Make sure sys is imported

# Make sure image_searchers.py is in the same directory or Python path is set up
from image_searchers import SmartAirbnbScraper, SerpApiGoogleImageSearch

def run_end_to_end_test(airbnb_url_to_test):
    """
    Performs an end-to-end test:
    1. Scrapes Airbnb for listing details (especially the main image).
    2. Uses SerpApi to perform a reverse image search.
    3. Prints the results.
    """
    print(f"--- Starting End-to-End Test for URL: {airbnb_url_to_test} ---\n")

    # Step 1: Scrape Airbnb for details
    print("Step 1: Scraping Airbnb for listing details...")
    airbnb_scraper = SmartAirbnbScraper()
    listing_details = airbnb_scraper.get_listing_details(airbnb_url_to_test)

    if not listing_details:
        print("Error: Failed to get any details from Airbnb.")
        return

    if listing_details.get("error"):
        print(f"Warning/Error from Airbnb scraper: {listing_details['error']}")

    main_image_url = listing_details.get("main_image_url")
    title = listing_details.get("title", "N/A")

    try:
        print(f"  Airbnb Title: {title}")
    except UnicodeEncodeError:
        output_encoding = sys.stdout.encoding if sys.stdout.encoding else 'utf-8'
        safe_title = title.encode(output_encoding, errors='replace').decode(output_encoding)
        print(f"  Airbnb Title (fallback encoding): {safe_title}")

    print(f"  Main Image URL found: {main_image_url}\n")

    if not main_image_url:
        print("Error: Could not find a main image URL from Airbnb. Cannot proceed with image search.")
        return

    # Step 2: Perform reverse image search using SerpApi
    print("Step 2: Performing reverse image search with SerpApi (aiming for 'exact matches')...")
    try:
        serp_api_searcher = SerpApiGoogleImageSearch()
    except ValueError as ve:
        print(f"Error initializing SerpApiGoogleImageSearch: {ve}")
        print("Please ensure SERPAPI_API_KEY is set in your environment or a .env file.")
        return

    # MODIFICATION: Call search_by_image without target_domains
    all_found_urls = serp_api_searcher.search_by_image(main_image_url)
    # No need for the target_ota_domains variable here anymore for this call.
    # The print statement below can also be simplified or removed if target_domains is always None for this call.
    print(f"  Searching for image (SerpApiGoogleImageSearch will extract from primary sections).")


    print("\n--- Test Results (All Links Found by SerpApi from relevant sections) ---")
    if all_found_urls:
        print(f"Found {len(all_found_urls)} potential URL(s) from SerpApi image search sections:")
        for i, url in enumerate(all_found_urls):
            try:
                print(f"  {i+1}. {url}")
            except UnicodeEncodeError:
                output_encoding = sys.stdout.encoding if sys.stdout.encoding else 'utf-8'
                safe_url = url.encode(output_encoding, errors='replace').decode(output_encoding)
                print(f"  {i+1}. {safe_url} (encoded)")
    else:
        print("No URLs found by SerpApi in 'image_sources' or 'image_results' sections.")

    print("\n--- End of End-to-End Test ---")

if __name__ == "__main__":
    load_dotenv()

    test_airbnb_url = "https://www.airbnb.com/rooms/23257738?search_mode=regular_search&adults=1&check_in=2025-05-25&check_out=2025-05-30&children=0&infants=0&pets=0&source_impression_id=p3_1747863615_P3tnkxsf-PgDh0oW&previous_page_section_name=1000&federated_search_id=389f8c9c-b667-49d2-9042-f64d5bb86b5b"

    if "airbnb.com/rooms/" not in test_airbnb_url or test_airbnb_url.endswith("SOME_ID") or test_airbnb_url.endswith("your_actual_airbnb_url_here"):
        print("Please replace the placeholder 'test_airbnb_url' with a specific, real Airbnb URL in manual_e2e_test.py")
    else:
        run_end_to_end_test(test_airbnb_url)
