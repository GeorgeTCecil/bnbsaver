"""
Intelligent Property Finder System for Affiliate Conversions
Searches for EXACT matches first, then SIMILAR alternatives if exact isn't found.

This module maximizes affiliate conversions by:
1. First searching for the EXACT same property on Booking.com, VRBO, etc.
2. If not found, using AI to find SIMILAR properties that match key criteria
3. Presenting both as options to maximize bookings

Author: BnbSaver Team
License: MIT
"""

import os
import re
import time
import json
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlencode, urlparse, parse_qs
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, asdict
from enum import Enum

# LangChain imports for AI comparison
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# SerpAPI for search
from serpapi import GoogleSearch

# Internal imports
from web_searcher import ParallelWebSearcher
from ai_verifier import ContentScraper
from ai_extractor import PropertyDetailExtractor


class Platform(Enum):
    """Supported affiliate platforms."""
    BOOKING_COM = "booking.com"
    VRBO = "vrbo.com"
    HOMEAWAY = "homeaway.com"
    TRIPADVISOR = "tripadvisor.com"
    HOTELS_COM = "hotels.com"
    EXPEDIA = "expedia.com"
    VACASA = "vacasa.com"
    FLIPKEY = "flipkey.com"
    EVOLVE = "evolve.com"
    UNKNOWN = "unknown"

    @classmethod
    def from_url(cls, url: str) -> 'Platform':
        """Determine platform from URL."""
        url_lower = url.lower()
        for platform in cls:
            if platform.value in url_lower:
                return platform
        return cls.UNKNOWN


@dataclass
class PropertyMatch:
    """Represents a property match with similarity score."""
    url: str
    platform: Platform
    title: str
    is_exact_match: bool
    similarity_score: float  # 0-100
    matching_features: List[str]
    price_per_night: Optional[float] = None
    total_price: Optional[float] = None
    currency: str = "USD"
    price_difference: Optional[float] = None  # vs original property
    recommendation: str = ""
    amenities: List[str] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    property_type: str = ""
    location: str = ""
    affiliate_link: str = ""
    scraped_content: str = ""

    def __post_init__(self):
        """Initialize mutable defaults."""
        if self.amenities is None:
            self.amenities = []

    def to_dict(self) -> Dict:
        """Convert to dictionary, handling enum."""
        result = asdict(self)
        result['platform'] = self.platform.value
        return result


class AffiliateLinkWrapper:
    """Wraps URLs with affiliate tracking IDs."""

    def __init__(self):
        """Initialize with affiliate IDs from environment variables."""
        self.affiliate_ids = {
            Platform.BOOKING_COM: os.getenv("BOOKING_AFFILIATE_ID", ""),
            Platform.VRBO: os.getenv("VRBO_AFFILIATE_ID", ""),
            Platform.TRIPADVISOR: os.getenv("TRIPADVISOR_AFFILIATE_ID", ""),
            Platform.HOTELS_COM: os.getenv("HOTELS_AFFILIATE_ID", ""),
            Platform.EXPEDIA: os.getenv("EXPEDIA_AFFILIATE_ID", ""),
        }

    def add_affiliate_id(self, url: str, platform: Platform) -> str:
        """
        Add affiliate tracking ID to URL.

        Args:
            url: Original URL
            platform: Platform enum

        Returns:
            URL with affiliate tracking ID appended

        Note:
            If no affiliate ID is configured, returns original URL.
            Each platform has different URL parameter conventions.
        """
        affiliate_id = self.affiliate_ids.get(platform, "")
        if not affiliate_id:
            return url

        # Parse URL
        parsed = urlparse(url)
        params = parse_qs(parsed.query)

        # Add platform-specific affiliate parameters
        if platform == Platform.BOOKING_COM:
            params['aid'] = [affiliate_id]
        elif platform == Platform.VRBO:
            params['affiliateId'] = [affiliate_id]
        elif platform == Platform.TRIPADVISOR:
            params['partner'] = [affiliate_id]
        elif platform == Platform.HOTELS_COM:
            params['pos'] = [affiliate_id]
        elif platform == Platform.EXPEDIA:
            params['affcid'] = [affiliate_id]

        # Reconstruct URL with affiliate params
        new_query = urlencode(params, doseq=True)
        affiliate_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{new_query}"

        return affiliate_url


class PropertyComparisonAI:
    """Uses AI to compare properties and determine similarity."""

    def __init__(self, model_provider="openai", model_name="gpt-4o-mini", api_key=None):
        """
        Initialize the AI comparison engine.

        Args:
            model_provider: "openai" or "anthropic"
            model_name: Model to use (default: "gpt-4o-mini" for cost-effectiveness)
            api_key: API key (defaults to env variables)

        Note:
            GPT-4o-mini provides excellent cost/quality balance:
            - $0.003 per comparison
            - Fast response times (1-2 seconds)
            - High accuracy for property matching
        """
        self.model_provider = model_provider

        if model_provider == "openai":
            self.llm = ChatOpenAI(
                model=model_name,
                api_key=api_key or os.getenv("OPENAI_API_KEY"),
                temperature=0  # Deterministic for consistency
            )
        elif model_provider == "anthropic":
            self.llm = ChatAnthropic(
                model=model_name,
                api_key=api_key or os.getenv("ANTHROPIC_API_KEY"),
                temperature=0
            )
        else:
            raise ValueError(f"Unsupported model provider: {model_provider}")

    def compare_properties(self,
                          original_property: Dict,
                          candidate_url: str,
                          candidate_content: str) -> Dict:
        """
        Compare original property with a candidate to determine similarity.

        Args:
            original_property: Enhanced property details from ai_extractor
            candidate_url: URL of candidate property
            candidate_content: Scraped content from candidate URL

        Returns:
            Dictionary with comparison results:
            {
                "is_exact_match": bool,
                "similarity_score": 0-100,
                "matching_features": list,
                "price_difference": float or null,
                "recommendation": string,
                "extracted_details": dict with bedrooms, bathrooms, amenities, etc.
            }
        """
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at comparing vacation rental properties to determine if they are the same listing or similar alternatives.

Your task is to analyze the original Airbnb property and a candidate property found on another website, then determine:

1. **is_exact_match**: Is this the EXACT SAME property? Look for:
   - Same address/building/street name
   - Same host/owner name
   - Identical unique features (e.g., "rooftop terrace with city views")
   - Same property photos/descriptions
   - Answer: true or false

2. **similarity_score**: How similar are they? (0-100)
   - 90-100: Exact same property
   - 70-89: Very similar (same area, size, amenities)
   - 50-69: Moderately similar (same city, similar size)
   - 30-49: Somewhat similar (same city)
   - 0-29: Different properties

3. **matching_features**: List of features that match (location, bedrooms, amenities, etc.)

4. **price_difference**: If both prices available, calculate difference (candidate - original)

5. **recommendation**: Brief recommendation for the user

6. **extracted_details**: Extract from candidate content:
   - property_type: apartment, house, villa, etc.
   - bedrooms: number (integer or null)
   - bathrooms: number (float or null)
   - max_guests: number (integer or null)
   - amenities: list of amenities found
   - location: specific location details
   - price_per_night: nightly rate if found (float or null)
   - total_price: total price if found (float or null)
   - currency: USD, EUR, etc.

Return ONLY valid JSON, no additional text. Use null for unknown values."""),
            ("user", """Compare these properties:

ORIGINAL PROPERTY (Airbnb):
Title: {original_title}
Location: {original_location}
Property Type: {original_type}
Bedrooms: {original_bedrooms}
Bathrooms: {original_bathrooms}
Amenities: {original_amenities}
Check-in: {check_in}
Check-out: {check_out}

CANDIDATE PROPERTY:
URL: {candidate_url}
Content: {candidate_content}

Analyze and return the comparison results as JSON.""")
        ])

        # Extract original property details
        ai_data = original_property.get("ai_extracted", {}) or {}

        chain = prompt_template | self.llm | StrOutputParser()

        response = chain.invoke({
            "original_title": original_property.get("title", "Not available"),
            "original_location": original_property.get("location_text", "Not available"),
            "original_type": ai_data.get("property_type", "Not specified"),
            "original_bedrooms": ai_data.get("bedrooms", "Not specified"),
            "original_bathrooms": ai_data.get("bathrooms", "Not specified"),
            "original_amenities": ", ".join(ai_data.get("key_amenities", [])) if ai_data.get("key_amenities") else "Not specified",
            "check_in": original_property.get("check_in", "Not specified"),
            "check_out": original_property.get("check_out", "Not specified"),
            "candidate_url": candidate_url,
            "candidate_content": candidate_content[:4000]  # Limit content to avoid token limits
        })

        try:
            comparison_result = json.loads(response)
            return comparison_result
        except json.JSONDecodeError as e:
            print(f"Error parsing AI comparison response: {e}")
            print(f"Raw response: {response[:500]}")
            return {
                "is_exact_match": False,
                "similarity_score": 0,
                "matching_features": [],
                "price_difference": None,
                "recommendation": "Error analyzing property",
                "extracted_details": {},
                "error": str(e)
            }

    def batch_compare(self,
                     original_property: Dict,
                     candidates: List[Tuple[str, str]],
                     max_workers: int = 3) -> List[Dict]:
        """
        Compare multiple candidates in parallel.

        Args:
            original_property: Enhanced property details
            candidates: List of (url, content) tuples
            max_workers: Number of parallel comparison threads

        Returns:
            List of comparison results
        """
        results = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_candidate = {
                executor.submit(
                    self.compare_properties,
                    original_property,
                    url,
                    content
                ): (url, content)
                for url, content in candidates
            }

            for future in as_completed(future_to_candidate):
                url, content = future_to_candidate[future]
                try:
                    result = future.result()
                    result['url'] = url
                    results.append(result)
                    print(f"✓ Compared: {url[:60]}... (similarity: {result.get('similarity_score', 0)})")
                except Exception as e:
                    print(f"✗ Error comparing {url}: {e}")
                    results.append({
                        "url": url,
                        "is_exact_match": False,
                        "similarity_score": 0,
                        "matching_features": [],
                        "price_difference": None,
                        "recommendation": f"Error: {str(e)}",
                        "extracted_details": {},
                        "error": str(e)
                    })

        return results


class ExactPropertyFinder:
    """Searches for the EXACT same property on other platforms."""

    def __init__(self, api_key=None):
        """
        Initialize exact property finder.

        Args:
            api_key: SerpAPI key for searches
        """
        self.api_key = api_key or os.getenv("SERPAPI_API_KEY")
        self.searcher = ParallelWebSearcher(api_key=self.api_key)

    def generate_exact_match_queries(self, property_details: Dict) -> List[str]:
        """
        Generate search queries designed to find the EXACT same property.

        Args:
            property_details: Enhanced property details with AI extraction

        Returns:
            List of highly specific search queries
        """
        queries = []
        ai_data = property_details.get("ai_extracted", {}) or {}

        # Extract key identifiers
        title = property_details.get("title", "")
        location = property_details.get("location_text", "")

        # Extract building/property name from title if exists
        # Common patterns: "Luxury Condo at The Grand Tower", "Beachfront Villa - Ocean View Estate"
        building_match = re.search(r'(?:at|in|@)\s+([A-Z][A-Za-z\s&]+(?:Tower|Building|Estate|Residences|House|Villa|Condo|Apartment))', title)
        building_name = building_match.group(1).strip() if building_match else None

        # Query 1: Building name + location (highest specificity)
        if building_name and location:
            queries.append(f'"{building_name}" {location} vacation rental -airbnb')

        # Query 2: Full title on specific platforms
        if title:
            queries.append(f'"{title}" site:booking.com OR site:vrbo.com OR site:tripadvisor.com')

        # Query 3: Unique features + location
        unique_features = ai_data.get("unique_features", [])
        if unique_features and location:
            feature_str = " ".join(unique_features[:2])  # Top 2 unique features
            queries.append(f'{location} "{feature_str}" vacation rental -airbnb')

        # Query 4: Address-based search (if location is specific)
        if location and any(word in location.lower() for word in ['street', 'avenue', 'road', 'drive', 'boulevard']):
            queries.append(f'"{location}" short term rental booking.com vrbo')

        # Query 5: Property type + specific amenities + location
        prop_type = ai_data.get("property_type", "")
        amenities = ai_data.get("key_amenities", [])
        if prop_type and amenities and location:
            amenity_str = " ".join(amenities[:2])
            queries.append(f'{location} {prop_type} "{amenity_str}" -airbnb')

        # Remove empty queries
        queries = [q for q in queries if q]

        return queries[:5]  # Limit to top 5 most specific queries

    def search_exact_matches(self,
                            property_details: Dict,
                            results_per_query: int = 5) -> List[Dict]:
        """
        Search for exact matches of the property.

        Args:
            property_details: Enhanced property details
            results_per_query: Number of results per query

        Returns:
            List of search results that might be exact matches
        """
        queries = self.generate_exact_match_queries(property_details)

        if not queries:
            print("WARNING: No exact match queries generated")
            return []

        print(f"\n=== Exact Match Search ===")
        print(f"Generated {len(queries)} high-specificity queries:")
        for i, query in enumerate(queries, 1):
            print(f"  {i}. {query}")

        # Execute searches in parallel
        results = self.searcher.search_multiple_queries(queries, results_per_query)

        # Deduplicate
        results = self.searcher.deduplicate_results(results)

        # Filter to major rental platforms
        platform_domains = [
            'booking.com', 'vrbo.com', 'homeaway.com', 'tripadvisor.com',
            'hotels.com', 'expedia.com', 'vacasa.com', 'flipkey.com', 'evolve.com'
        ]

        filtered_results = [
            r for r in results
            if any(domain in r.get('link', '').lower() for domain in platform_domains)
        ]

        print(f"✓ Found {len(filtered_results)} potential exact matches on rental platforms")

        return filtered_results


class SimilarPropertyFinder:
    """Finds similar properties when exact match isn't available."""

    def __init__(self, api_key=None):
        """
        Initialize similar property finder.

        Args:
            api_key: SerpAPI key for searches
        """
        self.api_key = api_key or os.getenv("SERPAPI_API_KEY")
        self.searcher = ParallelWebSearcher(api_key=self.api_key)

    def generate_similar_property_queries(self, property_details: Dict) -> List[str]:
        """
        Generate search queries for finding similar properties.

        Args:
            property_details: Enhanced property details with AI extraction

        Returns:
            List of search queries focused on key matching criteria
        """
        queries = []
        ai_data = property_details.get("ai_extracted", {}) or {}

        location = property_details.get("location_text", "")
        prop_type = ai_data.get("property_type", "vacation rental")
        bedrooms = ai_data.get("bedrooms")
        bathrooms = ai_data.get("bathrooms")
        amenities = ai_data.get("key_amenities", [])

        # Query 1: Location + property type + bedrooms
        if location and bedrooms:
            queries.append(f'{location} {bedrooms} bedroom {prop_type} booking.com vrbo')

        # Query 2: Location + bedrooms + bathrooms
        if location and bedrooms and bathrooms:
            queries.append(f'{location} {bedrooms}BR {bathrooms}BA vacation rental -airbnb')

        # Query 3: Location + key amenities
        if location and amenities:
            top_amenities = " ".join(amenities[:2])
            queries.append(f'{location} {top_amenities} {prop_type} -airbnb')

        # Query 4: Generic location + property type
        if location:
            queries.append(f'{location} {prop_type} short term rental booking vrbo')

        # Query 5: Location + "luxury" or "budget" based on amenities
        if location:
            luxury_amenities = ['pool', 'hot tub', 'ocean view', 'concierge', 'gym', 'spa']
            is_luxury = any(amenity.lower() in str(amenities).lower() for amenity in luxury_amenities)
            category = "luxury" if is_luxury else "affordable"
            queries.append(f'{location} {category} {prop_type} rental')

        # Remove empty queries
        queries = [q for q in queries if q]

        return queries[:6]

    def search_similar_properties(self,
                                 property_details: Dict,
                                 results_per_query: int = 10) -> List[Dict]:
        """
        Search for similar properties.

        Args:
            property_details: Enhanced property details
            results_per_query: Number of results per query

        Returns:
            List of search results for similar properties
        """
        queries = self.generate_similar_property_queries(property_details)

        if not queries:
            print("WARNING: No similar property queries generated")
            return []

        print(f"\n=== Similar Property Search ===")
        print(f"Generated {len(queries)} similarity-based queries:")
        for i, query in enumerate(queries, 1):
            print(f"  {i}. {query}")

        # Execute searches
        results = self.searcher.search_multiple_queries(queries, results_per_query)

        # Deduplicate
        results = self.searcher.deduplicate_results(results)

        # Filter to rental platforms
        results = self.searcher.filter_vacation_rental_sites(results)

        print(f"✓ Found {len(results)} similar property candidates")

        return results


class AffiliateFinder:
    """
    Main orchestrator for finding exact and similar properties with affiliate links.

    This class coordinates the entire property finding pipeline:
    1. Search for exact matches first
    2. Search for similar properties if needed
    3. Scrape candidate URLs
    4. Use AI to verify matches and extract details
    5. Rank by similarity and price
    6. Add affiliate tracking links
    """

    def __init__(self,
                 model_provider="openai",
                 model_name="gpt-4o-mini",
                 openai_api_key=None,
                 anthropic_api_key=None,
                 serpapi_key=None):
        """
        Initialize the affiliate finder system.

        Args:
            model_provider: "openai" or "anthropic"
            model_name: Model to use (default: "gpt-4o-mini")
            openai_api_key: OpenAI API key
            anthropic_api_key: Anthropic API key
            serpapi_key: SerpAPI key

        Note:
            GPT-4o-mini is recommended for optimal cost/quality balance.
        """
        # Set API keys if provided
        if openai_api_key:
            os.environ["OPENAI_API_KEY"] = openai_api_key
        if anthropic_api_key:
            os.environ["ANTHROPIC_API_KEY"] = anthropic_api_key
        if serpapi_key:
            os.environ["SERPAPI_API_KEY"] = serpapi_key

        # Initialize components
        self.exact_finder = ExactPropertyFinder(api_key=serpapi_key)
        self.similar_finder = SimilarPropertyFinder(api_key=serpapi_key)
        self.content_scraper = ContentScraper()
        self.comparator = PropertyComparisonAI(model_provider, model_name)
        self.affiliate_wrapper = AffiliateLinkWrapper()

        self.model_provider = model_provider
        self.model_name = model_name

    def find_alternatives(self,
                         property_details: Dict,
                         max_results: int = 10,
                         exact_match_threshold: int = 90,
                         min_similarity_threshold: int = 50) -> Dict:
        """
        Find exact matches and similar alternatives for a property.

        Args:
            property_details: Enhanced property details from PropertyDetailExtractor
            max_results: Maximum number of results to return
            exact_match_threshold: Similarity score threshold for exact matches (90-100)
            min_similarity_threshold: Minimum similarity score to include (0-100)

        Returns:
            Dictionary with:
            {
                "exact_matches": [...],  # Same property on other sites
                "similar_properties": [...],  # Similar alternatives
                "total_found": int,
                "best_deal": {...},  # Cheapest option overall
                "original_property": {...},
                "search_summary": {...}
            }
        """
        print("=" * 80)
        print("AFFILIATE PROPERTY FINDER")
        print("=" * 80)

        start_time = time.time()

        results = {
            "exact_matches": [],
            "similar_properties": [],
            "total_found": 0,
            "best_deal": None,
            "original_property": property_details,
            "search_summary": {
                "exact_queries_run": 0,
                "similar_queries_run": 0,
                "candidates_scraped": 0,
                "total_time": 0
            }
        }

        # Step 1: Search for exact matches
        print("\n" + "=" * 80)
        print("STEP 1: Searching for EXACT property matches")
        print("=" * 80)

        exact_search_results = self.exact_finder.search_exact_matches(
            property_details,
            results_per_query=5
        )
        results["search_summary"]["exact_queries_run"] = len(
            self.exact_finder.generate_exact_match_queries(property_details)
        )

        # Step 2: Search for similar properties
        print("\n" + "=" * 80)
        print("STEP 2: Searching for SIMILAR properties")
        print("=" * 80)

        similar_search_results = self.similar_finder.search_similar_properties(
            property_details,
            results_per_query=10
        )
        results["search_summary"]["similar_queries_run"] = len(
            self.similar_finder.generate_similar_property_queries(property_details)
        )

        # Combine results, prioritizing exact matches
        all_candidates = exact_search_results + similar_search_results

        # Deduplicate URLs
        seen_urls = set()
        unique_candidates = []
        for candidate in all_candidates:
            url = candidate.get("link", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_candidates.append(candidate)

        # Limit to max_results
        unique_candidates = unique_candidates[:max_results * 2]  # Scrape more than needed

        if not unique_candidates:
            print("\nNo candidates found. Returning empty results.")
            results["search_summary"]["total_time"] = time.time() - start_time
            return results

        # Step 3: Scrape candidate URLs
        print("\n" + "=" * 80)
        print(f"STEP 3: Scraping {len(unique_candidates)} candidate URLs")
        print("=" * 80)

        candidate_urls = [c["link"] for c in unique_candidates]
        scraped_contents = self.content_scraper.scrape_multiple(candidate_urls, max_workers=5)
        results["search_summary"]["candidates_scraped"] = len(scraped_contents)

        # Filter out failed scrapes
        valid_contents = [c for c in scraped_contents if c.get("content") and not c.get("error")]

        if not valid_contents:
            print("\nFailed to scrape any candidate URLs. Returning empty results.")
            results["search_summary"]["total_time"] = time.time() - start_time
            return results

        # Step 4: AI comparison and verification
        print("\n" + "=" * 80)
        print(f"STEP 4: AI comparison of {len(valid_contents)} properties")
        print("=" * 80)

        # Prepare candidates for comparison
        candidates_for_comparison = [
            (c["url"], c["content"]) for c in valid_contents
        ]

        comparison_results = self.comparator.batch_compare(
            property_details,
            candidates_for_comparison,
            max_workers=3
        )

        # Step 5: Process results and categorize
        print("\n" + "=" * 80)
        print("STEP 5: Processing and ranking results")
        print("=" * 80)

        processed_matches = []

        for comparison in comparison_results:
            similarity_score = comparison.get("similarity_score", 0)

            # Skip low similarity matches
            if similarity_score < min_similarity_threshold:
                continue

            # Extract details
            extracted = comparison.get("extracted_details", {})
            url = comparison.get("url", "")
            platform = Platform.from_url(url)

            # Create PropertyMatch object
            match = PropertyMatch(
                url=url,
                platform=platform,
                title=extracted.get("property_type", "Property"),
                is_exact_match=comparison.get("is_exact_match", False) or similarity_score >= exact_match_threshold,
                similarity_score=similarity_score,
                matching_features=comparison.get("matching_features", []),
                price_per_night=extracted.get("price_per_night"),
                total_price=extracted.get("total_price"),
                currency=extracted.get("currency", "USD"),
                price_difference=comparison.get("price_difference"),
                recommendation=comparison.get("recommendation", ""),
                amenities=extracted.get("amenities", []),
                bedrooms=extracted.get("bedrooms"),
                bathrooms=extracted.get("bathrooms"),
                property_type=extracted.get("property_type", ""),
                location=extracted.get("location", ""),
                affiliate_link="",  # Will be populated next
                scraped_content=comparison.get("url", "")
            )

            # Add affiliate link
            match.affiliate_link = self.affiliate_wrapper.add_affiliate_id(url, platform)

            processed_matches.append(match)

        # Sort by similarity score (highest first)
        processed_matches.sort(key=lambda x: x.similarity_score, reverse=True)

        # Categorize into exact vs similar
        exact_matches = [m for m in processed_matches if m.is_exact_match]
        similar_properties = [m for m in processed_matches if not m.is_exact_match]

        # Limit results
        results["exact_matches"] = [m.to_dict() for m in exact_matches[:max_results]]
        results["similar_properties"] = [m.to_dict() for m in similar_properties[:max_results]]
        results["total_found"] = len(results["exact_matches"]) + len(results["similar_properties"])

        # Find best deal (cheapest with known price)
        all_with_prices = [
            m for m in processed_matches
            if m.price_per_night is not None or m.total_price is not None
        ]

        if all_with_prices:
            # Sort by nightly rate or total price
            best_deal_match = min(
                all_with_prices,
                key=lambda x: x.price_per_night or x.total_price or float('inf')
            )
            results["best_deal"] = best_deal_match.to_dict()

        # Final summary
        results["search_summary"]["total_time"] = time.time() - start_time

        self._print_summary(results)

        return results

    def _print_summary(self, results: Dict):
        """Print summary of findings."""
        print("\n" + "=" * 80)
        print("SEARCH COMPLETE - SUMMARY")
        print("=" * 80)

        summary = results["search_summary"]
        print(f"\nSearch Statistics:")
        print(f"  - Exact match queries: {summary['exact_queries_run']}")
        print(f"  - Similar property queries: {summary['similar_queries_run']}")
        print(f"  - Candidates scraped: {summary['candidates_scraped']}")
        print(f"  - Total time: {summary['total_time']:.2f}s")

        print(f"\nResults Found:")
        print(f"  - Exact matches: {len(results['exact_matches'])}")
        print(f"  - Similar properties: {len(results['similar_properties'])}")
        print(f"  - Total alternatives: {results['total_found']}")

        if results["exact_matches"]:
            print("\n" + "-" * 80)
            print("EXACT MATCHES (Same Property on Other Sites)")
            print("-" * 80)
            for i, match in enumerate(results["exact_matches"], 1):
                price_info = ""
                if match.get("price_per_night"):
                    price_info = f" - ${match['price_per_night']}/night"
                elif match.get("total_price"):
                    price_info = f" - ${match['total_price']} total"

                print(f"\n{i}. {match['platform'].upper()} (Similarity: {match['similarity_score']}%){price_info}")
                print(f"   URL: {match['url']}")
                print(f"   Affiliate: {match['affiliate_link']}")
                if match.get("recommendation"):
                    print(f"   {match['recommendation']}")

        if results["similar_properties"]:
            print("\n" + "-" * 80)
            print("SIMILAR ALTERNATIVES (Different Properties, Similar Criteria)")
            print("-" * 80)
            for i, match in enumerate(results["similar_properties"][:5], 1):
                price_info = ""
                if match.get("price_per_night"):
                    price_info = f" - ${match['price_per_night']}/night"
                elif match.get("total_price"):
                    price_info = f" - ${match['total_price']} total"

                print(f"\n{i}. {match['platform'].upper()} (Similarity: {match['similarity_score']}%){price_info}")
                print(f"   {match.get('bedrooms', '?')} bed, {match.get('bathrooms', '?')} bath - {match.get('property_type', 'Property')}")
                print(f"   URL: {match['url'][:80]}...")
                if match.get("price_difference"):
                    diff = match['price_difference']
                    if diff < 0:
                        print(f"   💰 CHEAPER by ${abs(diff):.2f}!")
                    else:
                        print(f"   More expensive by ${diff:.2f}")

        if results.get("best_deal"):
            best = results["best_deal"]
            print("\n" + "=" * 80)
            print("🏆 BEST DEAL FOUND")
            print("=" * 80)
            price = best.get("price_per_night") or best.get("total_price")
            price_type = "per night" if best.get("price_per_night") else "total"
            print(f"Platform: {best['platform'].upper()}")
            print(f"Price: ${price} {price_type}")
            print(f"Similarity: {best['similarity_score']}%")
            print(f"Affiliate Link: {best['affiliate_link']}")

        print("\n" + "=" * 80)


# Convenience function for quick usage
def find_property_alternatives(airbnb_url: str,
                               model_provider: str = "openai",
                               model_name: str = "gpt-4o-mini",
                               max_results: int = 10) -> Dict:
    """
    Quick function to find alternatives for an Airbnb listing.

    Args:
        airbnb_url: Airbnb listing URL
        model_provider: "openai" or "anthropic"
        model_name: Model to use (default: "gpt-4o-mini")
        max_results: Maximum number of results

    Returns:
        Results dictionary with exact matches and similar properties

    Example:
        >>> from affiliate_finder import find_property_alternatives
        >>> results = find_property_alternatives("https://airbnb.com/rooms/12345")
        >>> print(f"Found {len(results['exact_matches'])} exact matches")
        >>> print(f"Best deal: {results['best_deal']['platform']} - ${results['best_deal']['price_per_night']}/night")
    """
    # Import here to avoid circular dependency
    from image_searchers import SmartAirbnbScraper

    # Step 1: Scrape Airbnb listing
    print("Scraping Airbnb listing...")
    scraper = SmartAirbnbScraper()
    listing_details = scraper.get_listing_details(airbnb_url)

    if listing_details.get("error"):
        return {
            "error": listing_details["error"],
            "exact_matches": [],
            "similar_properties": [],
            "total_found": 0,
            "best_deal": None
        }

    # Step 2: Extract property details with AI
    print("Extracting property details with AI...")
    extractor = PropertyDetailExtractor(model_provider, model_name)
    enhanced_details = extractor.extract_property_details(listing_details)

    # Step 3: Find alternatives
    finder = AffiliateFinder(model_provider, model_name)
    results = finder.find_alternatives(enhanced_details, max_results=max_results)

    return results


if __name__ == "__main__":
    """Test the affiliate finder system."""
    import sys

    if len(sys.argv) > 1:
        test_url = sys.argv[1]
    else:
        print("Usage: python affiliate_finder.py <airbnb_url>")
        print("\nExample:")
        print("  python affiliate_finder.py 'https://www.airbnb.com/rooms/12345'")
        sys.exit(1)

    print(f"\nTesting Affiliate Finder with URL:")
    print(f"{test_url}\n")

    results = find_property_alternatives(test_url)

    # Print final stats
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)
    print(f"Exact matches found: {len(results.get('exact_matches', []))}")
    print(f"Similar properties found: {len(results.get('similar_properties', []))}")
    print(f"Total alternatives: {results.get('total_found', 0)}")

    if results.get('best_deal'):
        print(f"\nBest deal: {results['best_deal']['platform']} at ${results['best_deal'].get('price_per_night') or results['best_deal'].get('total_price')}")
