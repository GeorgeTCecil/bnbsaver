"""
Multi-Modal Property Search Orchestrator
Main entry point that coordinates AI extraction, text search, image search, verification, and pricing.
"""
import os
import time
from typing import Dict, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import our custom modules
from image_searchers import SmartAirbnbScraper, SerpApiGoogleImageSearch
from scraper import GoogleImageSearch  # Selenium-based image search
from ai_extractor import PropertyDetailExtractor, SearchQueryGenerator
from web_searcher import TextSearchOrchestrator
from ai_verifier import ContentScraper, PropertyVerifier, PriceExtractor


class MultiModalPropertySearcher:
    """
    Orchestrates the complete multi-modal search pipeline:
    1. Scrape Airbnb listing
    2. Extract property details with AI
    3. Generate smart search queries with AI
    4. Parallel text searches
    5. Reverse image search (thorough)
    6. Scrape candidate URLs
    7. AI verification of matches
    8. AI price extraction
    """

    def __init__(self,
                 model_provider="openai",
                 model_name="gpt-4o-mini",
                 openai_api_key=None,
                 anthropic_api_key=None,
                 serpapi_key=None,
                 use_selenium_image_search=True):
        """
        Initialize the multi-modal searcher.

        Args:
            model_provider: "openai" or "anthropic"
            model_name: Model to use for AI tasks (default: "gpt-4o-mini" - optimal cost/quality balance)
            openai_api_key: OpenAI API key
            anthropic_api_key: Anthropic API key
            serpapi_key: SerpAPI key
            use_selenium_image_search: Whether to use Selenium (thorough) or SerpAPI (fast) for image search

        Note:
            GPT-4o-mini is the default model due to its excellent cost-effectiveness:
            - $0.003 per search (99.4% profit margin at $0.49/search)
            - Better quality than GPT-3.5-turbo
            - Fast response times (1-2 seconds)
        """
        self.model_provider = model_provider
        self.model_name = model_name
        self.use_selenium_image_search = use_selenium_image_search

        # Set API keys
        if openai_api_key:
            os.environ["OPENAI_API_KEY"] = openai_api_key
        if anthropic_api_key:
            os.environ["ANTHROPIC_API_KEY"] = anthropic_api_key
        if serpapi_key:
            os.environ["SERPAPI_API_KEY"] = serpapi_key

        # Initialize components
        self.airbnb_scraper = SmartAirbnbScraper()
        self.detail_extractor = PropertyDetailExtractor(model_provider, model_name)
        self.query_generator = SearchQueryGenerator(model_provider, model_name)
        self.text_searcher = TextSearchOrchestrator()
        self.content_scraper = ContentScraper()
        self.verifier = PropertyVerifier(model_provider, model_name)
        self.price_extractor = PriceExtractor(model_provider, model_name)

        # Initialize image searcher based on config
        if use_selenium_image_search:
            self.image_searcher = GoogleImageSearch()
        else:
            self.image_searcher = SerpApiGoogleImageSearch()

    def search_property(self,
                       airbnb_url: str,
                       num_text_queries: int = 8,
                       results_per_query: int = 10,
                       run_image_search: bool = True,
                       run_text_search: bool = True,
                       verify_matches: bool = True,
                       extract_prices: bool = True) -> Dict:
        """
        Execute complete multi-modal property search.

        Args:
            airbnb_url: Airbnb listing URL
            num_text_queries: Number of search query variations to generate
            results_per_query: Results per text search query
            run_image_search: Whether to run reverse image search
            run_text_search: Whether to run text-based searches
            verify_matches: Whether to verify matches with AI
            extract_prices: Whether to extract prices with AI

        Returns:
            Complete results dictionary with all findings
        """
        print("=" * 80)
        print("MULTI-MODAL PROPERTY SEARCH")
        print("=" * 80)

        start_time = time.time()
        results = {
            "airbnb_url": airbnb_url,
            "original_property": None,
            "text_search_results": [],
            "image_search_results": [],
            "all_candidates": [],
            "scraped_content": [],
            "verified_matches": [],
            "prices": [],
            "errors": [],
            "timing": {}
        }

        # Stage 1: Scrape Airbnb and extract details
        print("\n" + "=" * 80)
        print("STAGE 1: Scraping Airbnb & Extracting Property Details")
        print("=" * 80)

        stage1_start = time.time()
        try:
            listing_details = self.airbnb_scraper.get_listing_details(airbnb_url)
            if listing_details.get("error"):
                results["errors"].append(f"Airbnb scraping error: {listing_details['error']}")
                print(f"ERROR: {listing_details['error']}")
                return results

            enhanced_details = self.detail_extractor.extract_property_details(listing_details)
            results["original_property"] = enhanced_details

            print(f"\n✓ Property Details Extracted:")
            print(f"  Title: {enhanced_details.get('title', 'N/A')}")
            print(f"  Location: {enhanced_details.get('location_text', 'N/A')}")

            ai_data = enhanced_details.get("ai_extracted", {})
            if ai_data:
                print(f"  Property Type: {ai_data.get('property_type', 'N/A')}")
                print(f"  Bedrooms: {ai_data.get('bedrooms', 'N/A')}")
                print(f"  Amenities: {', '.join(ai_data.get('key_amenities', [])[:3]) if ai_data.get('key_amenities') else 'N/A'}")

        except Exception as e:
            error_msg = f"Stage 1 error: {str(e)}"
            results["errors"].append(error_msg)
            print(f"ERROR: {error_msg}")
            return results

        results["timing"]["stage1_scraping"] = time.time() - stage1_start

        # Stage 2: Generate search queries
        print("\n" + "=" * 80)
        print("STAGE 2: Generating AI-Powered Search Queries")
        print("=" * 80)

        stage2_start = time.time()
        try:
            search_queries = self.query_generator.generate_search_queries(
                enhanced_details,
                num_queries=num_text_queries
            )
            print(f"\n✓ Generated {len(search_queries)} search queries:")
            for i, query in enumerate(search_queries, 1):
                print(f"  {i}. {query}")

        except Exception as e:
            error_msg = f"Stage 2 error: {str(e)}"
            results["errors"].append(error_msg)
            print(f"ERROR: {error_msg}")
            search_queries = []

        results["timing"]["stage2_query_generation"] = time.time() - stage2_start

        # Stage 3 & 4: Parallel text and image searches
        print("\n" + "=" * 80)
        print("STAGE 3 & 4: Parallel Text + Image Searches")
        print("=" * 80)

        stage3_start = time.time()
        text_results = []
        image_results = []

        # Run text and image searches in parallel
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = {}

            # Submit text search
            if run_text_search and search_queries:
                futures["text"] = executor.submit(
                    self.text_searcher.find_property_listings,
                    search_queries,
                    results_per_query
                )

            # Submit image search
            if run_image_search and enhanced_details.get("main_image_url"):
                image_url = enhanced_details["main_image_url"]
                futures["image"] = executor.submit(
                    self.image_searcher.search_by_image,
                    image_url
                )

            # Collect results
            for search_type, future in futures.items():
                try:
                    if search_type == "text":
                        text_results = future.result()
                        results["text_search_results"] = text_results
                        print(f"\n✓ Text search completed: {len(text_results)} results")
                    elif search_type == "image":
                        raw_image_results = future.result()
                        # Convert to dictionary format
                        image_results = [
                            {"title": "", "link": url, "snippet": "", "source": "reverse_image_search"}
                            for url in raw_image_results
                        ]
                        results["image_search_results"] = image_results
                        print(f"\n✓ Image search completed: {len(image_results)} results")
                except Exception as e:
                    error_msg = f"{search_type.capitalize()} search error: {str(e)}"
                    results["errors"].append(error_msg)
                    print(f"ERROR: {error_msg}")

        results["timing"]["stage3_parallel_search"] = time.time() - stage3_start

        # Combine and deduplicate results
        all_candidates = text_results + image_results
        seen_urls = set()
        unique_candidates = []
        for candidate in all_candidates:
            url = candidate.get("link", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_candidates.append(candidate)

        results["all_candidates"] = unique_candidates
        print(f"\n✓ Combined results: {len(unique_candidates)} unique candidate URLs")

        if not unique_candidates:
            print("\nWARNING: No candidates found. Search complete.")
            results["timing"]["total"] = time.time() - start_time
            return results

        # Stage 5: Scrape candidate URLs
        print("\n" + "=" * 80)
        print("STAGE 5: Scraping Candidate URLs")
        print("=" * 80)

        stage5_start = time.time()
        candidate_urls = [c["link"] for c in unique_candidates]
        scraped_contents = self.content_scraper.scrape_multiple(candidate_urls)
        results["scraped_content"] = scraped_contents
        results["timing"]["stage5_content_scraping"] = time.time() - stage5_start

        # Stage 6: AI Verification
        if verify_matches:
            print("\n" + "=" * 80)
            print("STAGE 6: AI Verification of Matches")
            print("=" * 80)

            stage6_start = time.time()
            verification_results = self.verifier.verify_multiple(
                enhanced_details,
                scraped_contents
            )
            results["verified_matches"] = [v for v in verification_results if v.get("is_match")]
            results["timing"]["stage6_verification"] = time.time() - stage6_start

            print(f"\n✓ Verified {len(results['verified_matches'])} matches")
        else:
            # If not verifying, assume all are potential matches
            results["verified_matches"] = [{"url": c["url"], "is_match": True} for c in scraped_contents]

        # Stage 7: Price Extraction
        if extract_prices and results["verified_matches"]:
            print("\n" + "=" * 80)
            print("STAGE 7: AI Price Extraction")
            print("=" * 80)

            stage7_start = time.time()

            # Get scraped content for verified matches
            verified_urls = {m["url"] for m in results["verified_matches"]}
            verified_contents = [c for c in scraped_contents if c["url"] in verified_urls]

            # Extract prices
            check_in = enhanced_details.get("check_in")
            check_out = enhanced_details.get("check_out")

            price_results = self.price_extractor.extract_multiple_prices(
                verified_contents,
                check_in,
                check_out
            )

            results["prices"] = price_results
            results["timing"]["stage7_price_extraction"] = time.time() - stage7_start

            # Sort by price
            prices_with_values = [p for p in price_results if p.get("price_found")]
            if prices_with_values:
                print(f"\n✓ Found prices for {len(prices_with_values)} listings")

        # Final Summary
        results["timing"]["total"] = time.time() - start_time
        self._print_summary(results)

        return results

    def _print_summary(self, results: Dict):
        """Print final summary of results."""
        print("\n" + "=" * 80)
        print("SEARCH COMPLETE - SUMMARY")
        print("=" * 80)

        print(f"\nTotal Time: {results['timing']['total']:.2f}s")
        print(f"  - Airbnb scraping & AI extraction: {results['timing'].get('stage1_scraping', 0):.2f}s")
        print(f"  - Query generation: {results['timing'].get('stage2_query_generation', 0):.2f}s")
        print(f"  - Parallel searches: {results['timing'].get('stage3_parallel_search', 0):.2f}s")
        print(f"  - Content scraping: {results['timing'].get('stage5_content_scraping', 0):.2f}s")
        print(f"  - AI verification: {results['timing'].get('stage6_verification', 0):.2f}s")
        print(f"  - Price extraction: {results['timing'].get('stage7_price_extraction', 0):.2f}s")

        print(f"\nResults:")
        print(f"  - Text search results: {len(results['text_search_results'])}")
        print(f"  - Image search results: {len(results['image_search_results'])}")
        print(f"  - Total unique candidates: {len(results['all_candidates'])}")
        print(f"  - Verified matches: {len(results['verified_matches'])}")
        print(f"  - Prices found: {len([p for p in results.get('prices', []) if p.get('price_found')])}")

        if results.get("errors"):
            print(f"\nErrors: {len(results['errors'])}")
            for error in results["errors"]:
                print(f"  - {error}")

        # Print best prices
        prices_with_values = [p for p in results.get("prices", []) if p.get("price_found")]
        if prices_with_values:
            print("\n" + "=" * 80)
            print("PRICE COMPARISON")
            print("=" * 80)

            # Sort by nightly rate or total price
            sorted_prices = sorted(
                prices_with_values,
                key=lambda x: x.get("nightly_rate") or x.get("total_price") or float('inf')
            )

            for i, price in enumerate(sorted_prices[:5], 1):
                nightly = price.get("nightly_rate")
                total = price.get("total_price")
                currency = price.get("currency", "USD")

                price_str = f"{currency} {nightly}/night" if nightly else f"{currency} {total} total"
                print(f"\n{i}. {price_str}")
                print(f"   {price['url']}")
                if price.get("price_notes"):
                    print(f"   Note: {price['price_notes']}")

        print("\n" + "=" * 80)


# Convenience function
def find_best_price(airbnb_url: str,
                   model_provider="openai",
                   model_name="gpt-4o-mini",
                   use_selenium=True):
    """
    Quick function to find the best price for an Airbnb listing.

    Args:
        airbnb_url: Airbnb listing URL
        model_provider: "openai" or "anthropic"
        model_name: Model to use (default: "gpt-4o-mini" for optimal cost/quality)
        use_selenium: Use Selenium for thorough image search

    Returns:
        Results dictionary

    Note:
        GPT-4o-mini is the default model due to its excellent cost-effectiveness:
        - $0.003 per search (99.4% profit margin at $0.49/search)
        - Better quality than GPT-3.5-turbo
        - Fast response times (1-2 seconds)
    """
    searcher = MultiModalPropertySearcher(
        model_provider=model_provider,
        model_name=model_name,
        use_selenium_image_search=use_selenium
    )

    results = searcher.search_property(airbnb_url)
    return results


if __name__ == "__main__":
    # Example usage
    import sys

    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        # Test URL
        url = "https://www.airbnb.com/rooms/12345"

    print("Testing Multi-Modal Property Search")
    print(f"URL: {url}\n")

    # Using GPT-4o-mini for optimal cost/quality balance
    results = find_best_price(url, model_name="gpt-4o-mini")
