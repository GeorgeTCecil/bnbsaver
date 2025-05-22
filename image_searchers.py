# image_searchers.py
import os
import re # For SmartAirbnbScraper
import requests # For SmartAirbnbScraper
from bs4 import BeautifulSoup # For SmartAirbnbScraper
from serpapi import GoogleSearch
from urllib.parse import urlparse # For parsing domain from link if needed

# --- SmartAirbnbScraper Class Definition ---
class SmartAirbnbScraper:
    def __init__(self, use_scraping_api_key=None):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        })

    @staticmethod
    def trim_airbnb_url(airbnb_url):
        match = re.search(r"(https://www.airbnb.com/rooms/\d+)", airbnb_url)
        if match:
            return match.group(1)
        return re.sub(r"(\?|&)source_impression_id=.*", "", airbnb_url)

    @staticmethod
    def extract_dates_and_guests(airbnb_url):
        dates_match = re.search(r"check_in=(\d{4}-\d{2}-\d{2}).*?check_out=(\d{4}-\d{2}-\d{2})", airbnb_url)
        adults_match = re.search(r"adults=(\d+)", airbnb_url)
        check_in = dates_match.group(1) if dates_match else None
        check_out = dates_match.group(2) if dates_match else None
        adults = int(adults_match.group(1)) if adults_match else 0
        children_match = re.search(r"children=(\d+)", airbnb_url)
        children = int(children_match.group(1)) if children_match else 0
        total_guests = adults + children
        return check_in, check_out, total_guests if total_guests > 0 else None

    def get_listing_details(self, airbnb_url):
        trimmed_url = self.trim_airbnb_url(airbnb_url)
        check_in, check_out, total_guests = self.extract_dates_and_guests(airbnb_url)
        details = {
            "original_url": airbnb_url, "trimmed_url": trimmed_url, "main_image_url": None,
            "title": None, "description_snippet": None, "location_text": None, "host_name": None,
            "check_in": check_in, "check_out": check_out, "total_guests": total_guests, "error": None
        }
        try:
            response = self.session.get(trimmed_url, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            og_image_meta = soup.find("meta", property="og:image")
            if og_image_meta and og_image_meta.get("content"): details["main_image_url"] = og_image_meta["content"]
            og_title_meta = soup.find("meta", property="og:title")
            if og_title_meta and og_title_meta.get("content"): details["title"] = og_title_meta["content"]
            else:
                title_h1 = soup.find("h1")
                if title_h1: details["title"] = title_h1.get_text(strip=True)
            og_description_meta = soup.find("meta", property="og:description")
            if og_description_meta and og_description_meta.get("content"): details["description_snippet"] = og_description_meta["content"]
            else:
                description_meta = soup.find("meta", attrs={"name": "description"})
                if description_meta and description_meta.get("content"): details["description_snippet"] = description_meta["content"]
            json_ld_script = soup.find("script", type="application/ld+json")
            if json_ld_script:
                import json
                try:
                    data = json.loads(json_ld_script.string)
                    if not details["main_image_url"] and data.get("image"):
                        img_data = data["image"]
                        if isinstance(img_data, list):
                            img_url_candidate = img_data[0] if img_data else None
                            if isinstance(img_url_candidate, dict): details["main_image_url"] = img_url_candidate.get('url')
                            elif isinstance(img_url_candidate, str): details["main_image_url"] = img_url_candidate
                        elif isinstance(img_data, str): details["main_image_url"] = img_data
                    if not details["title"] and data.get("name"): details["title"] = data["name"]
                    if not details["description_snippet"] and data.get("description"): details["description_snippet"] = data["description"]
                    addr = data.get("address", data.get("location", {}).get("address"))
                    if isinstance(addr, dict) and addr.get("addressLocality"): details["location_text"] = addr["addressLocality"]
                except json.JSONDecodeError: print("Could not parse JSON-LD data.")
                except Exception as e: print(f"Error parsing JSON-LD: {e}")
            if not details["main_image_url"]:
                image_elements = soup.find_all("img", src=re.compile(r"a0\.muscache\.com/im/pictures"))
                if image_elements: details["main_image_url"] = image_elements[0].get('src')
            if not details["main_image_url"]:
                details["error"] = "Warning: Could not find a primary image URL using requests."
                print(details["error"])
            return details
        except requests.exceptions.RequestException as e:
            error_msg = f"Error fetching Airbnb URL {trimmed_url} with requests: {e}"; print(error_msg); details["error"] = error_msg; return details
        except Exception as e:
            error_msg = f"An unexpected error occurred in SmartAirbnbScraper: {e}"; print(error_msg); details["error"] = error_msg; return details

# --- SerpApiGoogleImageSearch Class Definition ---
# image_searchers.py
# ... (SmartAirbnbScraper remains the same) ...
# ... (imports like os, re, requests, BeautifulSoup, GoogleSearch, urlparse remain) ...

class SerpApiGoogleImageSearch:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("SERPAPI_API_KEY")
        if not self.api_key:
            raise ValueError("SerpApi API key not found. Set SERPAPI_API_KEY environment variable or pass as argument.")

    def search_by_image(self, image_url): # Removed target_domains from parameters
        print(f"DEBUG: SerpApiGoogleImageSearch.search_by_image called.")
        print(f"DEBUG:   image_url: {image_url}")
        # target_domains parameter is removed, so no filtering based on it here.

        params = {
            "engine": "google_reverse_image", "image_url": image_url, "api_key": self.api_key,
            "hl": "en", "gl": "us",
        }
        found_links = []
        try:
            search = GoogleSearch(params)
            results_dict = search.get_dict()
            
            # --- For deep debugging if necessary ---
            # import json
            # print(f"DEBUG: Full SerpApi results_dict:\n{json.dumps(results_dict, indent=2)}")
            # ---

            # Check if SerpApi itself reported that Google found no direct reverse image matches
            if results_dict.get("error") and "Google Reverse Image hasn't returned any results" in results_dict["error"]:
                print(f"DEBUG: SerpApi reported no direct reverse image results (Google fallback likely): {results_dict['error']}")
                # Even if there's an error, Google might still populate 'image_results' based on its interpretation
                # so we will still try to process 'image_results' below if 'image_sources' is empty.

            # Key for "Pages that include matching images" / "Exact Matches" is usually 'image_sources'
            if "image_sources" in results_dict and results_dict["image_sources"]:
                print("DEBUG: Processing 'image_sources' (primary target for exact matches)")
                for item_idx, item in enumerate(results_dict["image_sources"]):
                    if "link" in item:
                        link = item["link"]
                        print(f"  DEBUG: Found in 'image_sources': {link}")
                        found_links.append(link)
            
            # If 'image_sources' was empty or missing, or if you want to be exhaustive
            # and also include results from 'image_results' (which might be broader
            # or contain results when Google's reverse image search falls back to text interpretation).
            # You need to decide if 'image_results' counts towards your definition of "exact matches".
            # For now, let's include them if 'image_sources' was empty.
            if not found_links and "image_results" in results_dict and results_dict["image_results"]:
                print("DEBUG: 'image_sources' was empty or missing. Processing 'image_results'.")
                for result_idx, result in enumerate(results_dict["image_results"]):
                    if "link" in result:
                        link = result["link"]
                        print(f"  DEBUG: Found in 'image_results': {link}")
                        found_links.append(link)
            
            # If STILL no links, but there's a 'google_lens_resolver_results' or similar,
            # that could be another place Google UI might show matches. This is more advanced.
            # For now, focusing on image_sources and image_results.

            unique_links = sorted(list(set(found_links)))
            print(f"DEBUG: Total unique links found from SerpApi: {unique_links}")
            
            # No domain-based filtering applied here as per your request.
            # All found links are returned.
            print(f"SerpApiGoogleImageSearch.search_by_image returning: {unique_links}")
            return unique_links

        except Exception as e:
            print(f"Error during SerpApi Google Image search: {e}")
            # Check if results_dict exists before trying to access 'error' key from it
            if 'results_dict' in locals() and results_dict is not None and results_dict.get('error'):
                print(f"SerpApi error message: {results_dict.get('error')}")
            return []