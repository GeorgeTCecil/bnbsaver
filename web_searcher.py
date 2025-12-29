"""
Parallel Web Search Module
Performs concurrent text-based searches across multiple queries and engines.
"""
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Set
from serpapi import GoogleSearch
import time


class ParallelWebSearcher:
    """Performs parallel web searches to find vacation rental listings."""

    def __init__(self, api_key=None, max_workers=5):
        """
        Initialize the web searcher.

        Args:
            api_key: SerpAPI key (defaults to SERPAPI_API_KEY env var)
            max_workers: Number of parallel search threads
        """
        self.api_key = api_key or os.getenv("SERPAPI_API_KEY")
        if not self.api_key:
            raise ValueError("SerpAPI API key required. Set SERPAPI_API_KEY environment variable.")

        self.max_workers = max_workers

    def search_single_query(self, query: str, num_results: int = 10) -> List[Dict]:
        """
        Execute a single Google search query via SerpAPI.

        Args:
            query: Search query string
            num_results: Number of results to retrieve

        Returns:
            List of result dictionaries with 'title', 'link', 'snippet'
        """
        params = {
            "engine": "google",
            "q": query,
            "api_key": self.api_key,
            "num": num_results,
            "hl": "en",
            "gl": "us",
        }

        try:
            search = GoogleSearch(params)
            results = search.get_dict()

            organic_results = results.get("organic_results", [])

            parsed_results = []
            for result in organic_results:
                parsed_results.append({
                    "title": result.get("title", ""),
                    "link": result.get("link", ""),
                    "snippet": result.get("snippet", ""),
                    "source": "google_text_search",
                    "query": query
                })

            return parsed_results

        except Exception as e:
            print(f"Error searching query '{query}': {e}")
            return []

    def search_multiple_queries(self, queries: List[str], num_results_per_query: int = 10) -> List[Dict]:
        """
        Execute multiple search queries in parallel.

        Args:
            queries: List of search query strings
            num_results_per_query: Number of results per query

        Returns:
            Combined list of all results from all queries
        """
        all_results = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all search tasks
            future_to_query = {
                executor.submit(self.search_single_query, query, num_results_per_query): query
                for query in queries
            }

            # Collect results as they complete
            for future in as_completed(future_to_query):
                query = future_to_query[future]
                try:
                    results = future.result()
                    all_results.extend(results)
                    print(f"✓ Completed search: '{query}' ({len(results)} results)")
                except Exception as e:
                    print(f"✗ Error in search '{query}': {e}")

        return all_results

    def deduplicate_results(self, results: List[Dict]) -> List[Dict]:
        """
        Remove duplicate URLs from results.

        Args:
            results: List of search result dictionaries

        Returns:
            Deduplicated list of results
        """
        seen_urls: Set[str] = set()
        unique_results = []

        for result in results:
            url = result.get("link", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)

        return unique_results

    def filter_by_domains(self, results: List[Dict], exclude_domains: List[str] = None,
                         include_domains: List[str] = None) -> List[Dict]:
        """
        Filter results by domain name.

        Args:
            results: List of search results
            exclude_domains: List of domains to exclude (e.g., ['airbnb.com', 'zillow.com'])
            include_domains: List of domains to include (if specified, only these are kept)

        Returns:
            Filtered list of results
        """
        exclude_domains = exclude_domains or []
        include_domains = include_domains or []

        filtered_results = []

        for result in results:
            url = result.get("link", "")

            # Check exclusions
            if any(domain in url.lower() for domain in exclude_domains):
                continue

            # Check inclusions (if specified)
            if include_domains:
                if not any(domain in url.lower() for domain in include_domains):
                    continue

            filtered_results.append(result)

        return filtered_results

    def filter_vacation_rental_sites(self, results: List[Dict]) -> List[Dict]:
        """
        Filter to keep only known vacation rental sites and exclude aggregators/irrelevant sites.

        Args:
            results: List of search results

        Returns:
            Filtered list focusing on rental sites
        """
        # Common vacation rental platforms
        rental_platforms = [
            'vrbo.com', 'homeaway.com', 'booking.com', 'vacasa.com',
            'flipkey.com', 'tripadvisor.com', 'expedia.com', 'hotels.com',
            'evolve.com', 'vacationrenter.com', 'tripping.com'
        ]

        # Sites to exclude
        exclude = [
            'airbnb.com', 'zillow.com', 'realtor.com', 'redfin.com',
            'facebook.com', 'pinterest.com', 'instagram.com', 'youtube.com',
            'reddit.com', 'twitter.com', 'linkedin.com'
        ]

        platform_results = []
        other_results = []

        for result in results:
            url = result.get("link", "").lower()

            # Skip excluded domains
            if any(domain in url for domain in exclude):
                continue

            # Prioritize known rental platforms
            if any(platform in url for platform in rental_platforms):
                platform_results.append(result)
            else:
                # Keep other results (could be personal rental sites)
                other_results.append(result)

        # Return platform results first, then others
        return platform_results + other_results


class TextSearchOrchestrator:
    """High-level orchestrator for text-based property searches."""

    def __init__(self, api_key=None):
        self.searcher = ParallelWebSearcher(api_key=api_key)

    def find_property_listings(self, search_queries: List[str],
                               results_per_query: int = 10,
                               filter_rentals: bool = True) -> List[Dict]:
        """
        Execute full text search pipeline for property listings.

        Args:
            search_queries: List of search query strings
            results_per_query: Number of results per query
            filter_rentals: Whether to filter to rental sites only

        Returns:
            Deduplicated, filtered list of potential property listings
        """
        print(f"\n=== Text Search Phase ===")
        print(f"Executing {len(search_queries)} search queries in parallel...")

        # Execute parallel searches
        all_results = self.searcher.search_multiple_queries(
            search_queries,
            num_results_per_query=results_per_query
        )
        print(f"Total results collected: {len(all_results)}")

        # Deduplicate
        unique_results = self.searcher.deduplicate_results(all_results)
        print(f"After deduplication: {len(unique_results)} unique URLs")

        # Filter to vacation rental sites
        if filter_rentals:
            filtered_results = self.searcher.filter_vacation_rental_sites(unique_results)
            print(f"After filtering to rental sites: {len(filtered_results)} results")
            return filtered_results
        else:
            return unique_results


# Quick usage example
if __name__ == "__main__":
    # Test the searcher
    searcher = TextSearchOrchestrator()

    test_queries = [
        "Miami beach ocean view 3 bedroom vacation rental -airbnb",
        "South Beach Miami short term rental VRBO",
        "Miami luxury beachfront rental booking.com"
    ]

    results = searcher.find_property_listings(test_queries, results_per_query=5)

    print(f"\n=== Found {len(results)} potential listings ===")
    for i, result in enumerate(results[:10], 1):
        print(f"{i}. {result['title'][:60]}...")
        print(f"   {result['link']}")
