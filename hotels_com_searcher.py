"""
Hotels.com Platform Searcher
Searches Hotels.com for vacation rentals and hotels matching property criteria.

Strategy:
1. Search Hotels.com by location + dates
2. Filter results by property type, bedrooms, etc.
3. Extract pricing for specific dates
4. Return standardized results for aggregator
"""

import os
from typing import Dict, List, Optional
from serpapi import GoogleSearch
from dotenv import load_dotenv
import re
from platform_searcher_base import PlatformSearcherBase

load_dotenv()


class HotelsComSearcher(PlatformSearcherBase):
    """
    Searches Hotels.com for vacation rental properties and hotels.

    Uses SerpAPI to search Hotels.com and extract property listings.
    """

    def __init__(self, serpapi_key: Optional[str] = None, openai_api_key: Optional[str] = None):
        """Initialize the Hotels.com searcher."""
        super().__init__(openai_api_key)
        self.serpapi_key = serpapi_key or os.getenv('SERPAPI_API_KEY')
        if not self.serpapi_key:
            raise ValueError("SERPAPI_API_KEY not found")

    @property
    def platform_name(self) -> str:
        """Return platform name."""
        return "Hotels.com"

    def generate_search_query(
        self,
        property_details: Dict,
        check_in: str,
        check_out: str
    ) -> str:
        """
        Generate Google search query for Hotels.com properties.

        Args:
            property_details: Property details
            check_in: Check-in date
            check_out: Check-out date

        Returns:
            Search query string
        """
        city = property_details.get('city', '')
        state = property_details.get('state_region', '')
        bedrooms = property_details.get('bedrooms', 0)
        property_type = property_details.get('property_type', 'vacation rental')

        # Build search query
        location = f"{city}, {state}" if city and state else city or state

        query_parts = [
            f"site:hotels.com",
            location,
        ]

        # Hotels.com has both hotels and vacation rentals
        if property_type in ['condo', 'apartment', 'house', 'villa']:
            query_parts.append('vacation rental')

        if bedrooms:
            query_parts.append(f"{bedrooms} bedroom")

        return " ".join(query_parts)

    def search_properties(
        self,
        property_details: Dict,
        check_in: str,
        check_out: str,
        max_results: int = 20
    ) -> List[Dict]:
        """
        Search Hotels.com for properties matching criteria.

        Args:
            property_details: Original property details
            check_in: Check-in date (YYYY-MM-DD)
            check_out: Check-out date (YYYY-MM-DD)
            max_results: Maximum results to return

        Returns:
            List of property dicts
        """
        print(f"\nSearching {self.platform_name} for similar properties...")

        query = self.generate_search_query(property_details, check_in, check_out)
        print(f"  Query: {query}")

        try:
            search = GoogleSearch({
                "q": query,
                "api_key": self.serpapi_key,
                "num": max_results,
                "gl": "us",
                "hl": "en"
            })

            results = search.get_dict()
            organic_results = results.get("organic_results", [])

            print(f"  Found {len(organic_results)} Hotels.com listings")

            properties = []
            for result in organic_results[:max_results]:
                # Extract property details from search result
                property_dict = self._parse_search_result(
                    result,
                    property_details,
                    check_in,
                    check_out
                )

                if property_dict:
                    properties.append(self.format_result(property_dict))

            return properties

        except Exception as e:
            print(f"  Error searching {self.platform_name}: {e}")
            return []

    def _parse_search_result(
        self,
        result: Dict,
        property_details: Dict,
        check_in: str,
        check_out: str
    ) -> Optional[Dict]:
        """
        Parse a single search result into property dict.

        Args:
            result: Search result from SerpAPI
            property_details: Original property details (for context)
            check_in: Check-in date
            check_out: Check-out date

        Returns:
            Property dict or None if parsing fails
        """
        try:
            title = result.get('title', '')
            url = result.get('link', '')
            snippet = result.get('snippet', '')

            # Skip if not actually a property listing
            if not self._is_property_listing(title, url, snippet):
                return None

            # Extract basic details using AI
            extracted = self._extract_details_with_ai(title, snippet, property_details)

            if not extracted:
                return None

            return {
                'name': extracted.get('name', title),
                'location': extracted.get('location', f"{property_details.get('city')}, {property_details.get('state_region')}"),
                'type': extracted.get('type', 'hotel'),
                'bedrooms': extracted.get('bedrooms', 0),
                'bathrooms': extracted.get('bathrooms', 0),
                'amenities': extracted.get('amenities', []),
                'price': extracted.get('price', 0),
                'url': url
            }

        except Exception as e:
            print(f"    Error parsing result: {e}")
            return None

    def _is_property_listing(self, title: str, url: str, snippet: str) -> bool:
        """
        Check if search result is an actual property listing.

        Args:
            title: Page title
            url: Page URL
            snippet: Search snippet

        Returns:
            True if this is a property listing
        """
        # Must be hotels.com domain
        if 'hotels.com' not in url.lower():
            return False

        # Skip non-property pages
        skip_patterns = [
            '/help',
            '/customer-service',
            '/about',
            '/contact',
            'hotels.com/lp/',
            '/deals',
            '/rewards',
        ]

        url_lower = url.lower()
        if any(pattern in url_lower for pattern in skip_patterns):
            return False

        # Look for property indicators
        property_indicators = [
            'hotel',
            'resort',
            'apartment',
            'vacation rental',
            'condo',
            'suite',
            'lodge',
            'inn',
            'bedroom',
        ]

        content = f"{title} {snippet}".lower()
        return any(indicator in content for indicator in property_indicators)

    def _extract_details_with_ai(
        self,
        title: str,
        snippet: str,
        property_details: Dict
    ) -> Optional[Dict]:
        """
        Use AI to extract property details from search result.

        Args:
            title: Search result title
            snippet: Search result snippet
            property_details: Original property (for context)

        Returns:
            Extracted property details or None
        """
        prompt = f"""Extract hotel/vacation rental property details from this Hotels.com search result.

Search Result:
Title: {title}
Description: {snippet}

Extract and return JSON with:
{{
    "name": "property name",
    "location": "city, state",
    "type": "hotel/resort/apartment/condo/suite/etc",
    "bedrooms": number (extract if specified, estimate if not, hotels often don't specify),
    "bathrooms": number (extract if specified, estimate if not),
    "amenities": ["pool", "wifi", "gym", etc] (extract any mentioned),
    "price": number (nightly rate if mentioned, otherwise 0)
}}

If this doesn't look like a valid property listing, return null."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert at extracting hotel and vacation rental property information."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                max_tokens=300
            )

            result_text = response.choices[0].message.content

            # Parse JSON
            import json
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                extracted = json.loads(json_match.group())
                return extracted if extracted else None
            else:
                return None

        except Exception as e:
            print(f"    AI extraction error: {e}")
            return None

    def add_affiliate_link(self, property_url: str) -> str:
        """
        Add Hotels.com affiliate tracking parameters.

        Args:
            property_url: Original property URL

        Returns:
            URL with affiliate tracking (once we have affiliate ID)
        """
        # TODO: Add affiliate tracking parameters
        # Hotels.com uses Expedia Partner Solutions (EPS), same as VRBO
        return property_url


def test_hotels_com_searcher():
    """Test the Hotels.com searcher."""
    searcher = HotelsComSearcher()

    # Test property details
    property_details = {
        'property_name': "King's Crown D203",
        'city': 'Park City',
        'state_region': 'Utah',
        'property_type': 'condo',
        'bedrooms': 2,
        'bathrooms': 2,
        'amenities': ['Pool', 'Hot Tub', 'Ski In/Ski Out']
    }

    print("=" * 80)
    print(f"TESTING: {searcher.platform_name} Searcher")
    print("=" * 80)
    print(f"\nOriginal Property: {property_details['property_name']}")
    print(f"Location: {property_details['city']}, {property_details['state_region']}")

    # Search for similar properties
    results = searcher.search_properties(
        property_details,
        check_in="2026-02-05",
        check_out="2026-02-08",
        max_results=10
    )

    print(f"\n{'=' * 80}")
    print("RESULTS")
    print("=" * 80)

    if results:
        print(f"\nFound {len(results)} properties:\n")
        for i, prop in enumerate(results, 1):
            print(f"{i}. {prop['name']}")
            print(f"   Location: {prop['location']}")
            print(f"   Type: {prop['type']}")
            if prop.get('bedrooms'):
                print(f"   Bedrooms: {prop['bedrooms']}, Bathrooms: {prop['bathrooms']}")
            if prop.get('amenities'):
                print(f"   Amenities: {', '.join(prop['amenities'][:3])}")
            if prop.get('price'):
                print(f"   Price: ${prop['price']}/night")
            print(f"   URL: {prop['url'][:70]}...")
            print()
    else:
        print("\nNo properties found")

    print("=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    test_hotels_com_searcher()
