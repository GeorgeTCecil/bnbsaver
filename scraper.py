# Refactored GoogleImageSearch using SerpApi
import os
from serpapi import GoogleSearch
# from dotenv import load_dotenv # For loading API key from .env file

# load_dotenv() # Load environment variables from .env file

class SerpApiGoogleImageSearch:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("SERPAPI_API_KEY")
        if not self.api_key:
            raise ValueError("SerpApi API key not found. Set SERPAPI_API_KEY environment variable.")

    def search_by_image(self, image_url, target_domains=None):
        """
        Performs a reverse image search using SerpApi.
        :param image_url: URL of the image to search for.
        :param target_domains: Optional list of domains to filter results (e.g., ['vrbo.com', 'booking.com'])
        :return: List of relevant URLs.
        """
        params = {
            "engine": "google_reverse_image",
            "image_url": image_url,
            "api_key": self.api_key,
            "hl": "en", # Language
            "gl": "us", # Country
        }

        try:
            search = GoogleSearch(params)
            results = search.get_dict()

            found_links = []

            # SerpApi returns results in 'image_results' or 'inline_images' or similar
            # You'll need to inspect the SerpApi JSON output to find the exact structure
            # for "pages with matching images" or similar sections.
            # This is an example, structure might vary slightly.
            if "image_results" in results:
                for result in results["image_results"]:
                    if "link" in result and "source" in result:
                        # Example: filter by source domain if target_domains provided
                        if target_domains:
                            if any(domain in result["source"].lower() for domain in target_domains):
                                found_links.append(result["link"])
                        else: # If no target_domains, take all (you might want stricter filtering)
                            found_links.append(result["link"])
                            
            # You might also want to look into 'Visual matches' if 'Exact matches' isn't a direct key
            # Google Lens results can be complex. Check the 'inline_images' or 'visual_matches' sections.
            # For instance, from "Pages that include matching images" section
            if 'image_sources' in results: # This key often contains sites where the image appears
                for item in results['image_sources']:
                    if 'link' in item:
                         if target_domains:
                             if any(domain in item.get("source", "").lower() for domain in target_domains):
                                 found_links.append(item["link"])
                         else:
                             found_links.append(item["link"])


            # Deduplicate links
            unique_links = list(set(found_links))

            # Further filter out Airbnb self-links if image_url itself is an Airbnb image
            # (though ideally, you'd filter by a list of *target* OTAs)
            cleaned_links = [link for link in unique_links if "airbnb.com" not in link.lower()]

            return cleaned_links

        except Exception as e:
            print(f"Error during SerpApi Google Image search: {e}")
            print(f"Search params: {params}")
            if 'results' in locals() and results.get('error'):
                print(f"SerpApi error message: {results['error']}")
            return []

# Example Usage (SerpApi):
# if __name__ == '__main__':
#     image_searcher = SerpApiGoogleImageSearch()
#     # Replace with a real image URL from an Airbnb listing for testing
#     test_image_url = "https://a0.muscache.com/im/pictures/prohost-api/Hosting-SOMEID/original/SOMEID.jpeg"
#     links = image_searcher.search_by_image(test_image_url, target_domains=['vrbo.com', 'booking.com'])
#     print("Found links:", links)