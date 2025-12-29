"""
Owner Website Finder
Searches Google for property owner's direct booking websites to bypass platform fees.

This is the killer feature - finding owner sites can save users $200-800 per booking
by avoiding Airbnb/VRBO's 10-25% platform fees.
"""

import os
from typing import List, Dict, Optional
from serpapi import GoogleSearch
from dotenv import load_dotenv

load_dotenv()


class OwnerWebsiteFinder:
    """
    Finds owner direct booking websites using smart Google search strategies.

    Strategy:
    1. Generate multiple search queries based on property details
    2. Use SerpAPI to search Google
    3. Filter out platforms and irrelevant results
    4. Return candidate owner websites for image verification
    """

    # Platforms to exclude from results (we want direct owner sites only)
    PLATFORM_DOMAINS = [
        'airbnb.com',
        'vrbo.com',
        'booking.com',
        'hotels.com',
        'expedia.com',
        'tripadvisor.com',
        'trip.com',
        'agoda.com',
        'homeaway.com',
        'flipkey.com',
        'vacasa.com',
        'vacationrenter.com',
        'rentalo.com',
        'tripping.com',
    ]

    # Sites that aren't owner sites (review sites, aggregators, forums)
    EXCLUDE_DOMAINS = [
        'yelp.com',
        'facebook.com',
        'instagram.com',
        'twitter.com',
        'reddit.com',
        'pinterest.com',
        'youtube.com',
        'google.com',
        'wikipedia.org',
    ]

    def __init__(self, serpapi_key: Optional[str] = None):
        """
        Initialize the owner website finder.

        Args:
            serpapi_key: SerpAPI key (defaults to env var SERPAPI_API_KEY)
        """
        self.serpapi_key = serpapi_key or os.getenv('SERPAPI_API_KEY')
        if not self.serpapi_key:
            raise ValueError("SERPAPI_API_KEY not found in environment variables")

    def generate_search_queries(self, property_details: Dict) -> List[str]:
        """
        Generate smart Google search queries to find owner websites.

        PRIORITY ORDER:
        1. Host name (often the property management company!)
        2. Property name + location
        3. Address
        4. General location search

        Args:
            property_details: Dict with keys:
                - address: Property address or location
                - property_name: Name of the property (if available)
                - host_name: Host/owner name (if available)
                - city: City name
                - region: State/region

        Returns:
            List of search query strings (ordered by priority)
        """
        queries = []

        address = property_details.get('address', '')
        property_name = property_details.get('property_name', '')
        host_name = property_details.get('host_name', '')
        city = property_details.get('city', '')
        region = property_details.get('state_region') or property_details.get('region', '')

        # ===================================================================
        # PRIORITY 1: HOST NAME (Most likely to find owner direct site!)
        # ===================================================================
        # Often the host name IS the property management company
        # Examples: "Abode Park City", "Mountain West Vacation Rentals"

        if host_name:
            # Just the host name (if it's a known company, this is best)
            queries.append(f'"{host_name}" vacation rentals')

            # Host name + direct booking
            queries.append(f'"{host_name}" direct booking')

            # Host name + region (broader than city)
            if region:
                queries.append(f'"{host_name}" {region} vacation rentals')

            # Host name + city (more specific)
            if city:
                queries.append(f'"{host_name}" {city} property rentals')

        # ===================================================================
        # PRIORITY 2: PROPERTY NAME + LOCATION
        # ===================================================================
        # Good for finding specific properties or complexes

        if property_name and city:
            queries.append(f'"{property_name}" {city} direct booking')
            queries.append(f'"{property_name}" {city} vacation rental -airbnb -vrbo')

        # ===================================================================
        # PRIORITY 3: ADDRESS
        # ===================================================================
        # Specific but less likely to have a dedicated website

        if address:
            queries.append(f'"{address}" vacation rental direct booking')
            queries.append(f'"{address}" rental website')

        # ===================================================================
        # PRIORITY 4: GENERAL LOCATION (Cast wider net)
        # ===================================================================
        # Finds local property managers in the area

        if city and region:
            property_type = property_details.get('property_type', 'vacation rental')
            queries.append(f'{city} {region} {property_type} direct booking -airbnb -vrbo -booking.com')

        # Query with all platforms excluded (finds smaller local companies)
        location = address or f"{city}, {region}" if city and region else city
        if location:
            exclude_str = ' -' + ' -'.join(self.PLATFORM_DOMAINS)
            queries.append(f'"{location}" vacation rental{exclude_str}')

        return queries

    def search_google(self, query: str, num_results: int = 10) -> List[Dict]:
        """
        Search Google using SerpAPI.

        Args:
            query: Search query string
            num_results: Number of results to return

        Returns:
            List of search result dicts with 'title', 'link', 'snippet'
        """
        try:
            search = GoogleSearch({
                "q": query,
                "api_key": self.serpapi_key,
                "num": num_results,
                "gl": "us",  # Search from US
                "hl": "en"   # English results
            })

            results = search.get_dict()
            organic_results = results.get("organic_results", [])

            return [
                {
                    'title': result.get('title', ''),
                    'link': result.get('link', ''),
                    'snippet': result.get('snippet', ''),
                    'query': query
                }
                for result in organic_results
            ]

        except Exception as e:
            print(f"Error searching Google for '{query}': {e}")
            return []

    def is_likely_owner_site(self, url: str, title: str, snippet: str) -> bool:
        """
        Determine if a URL is likely an owner direct booking site.

        Filters out:
        - Major booking platforms
        - Review sites
        - Social media
        - Forums/aggregators

        Args:
            url: Website URL
            title: Page title
            snippet: Search result snippet

        Returns:
            True if likely an owner site
        """
        url_lower = url.lower()

        # Exclude major platforms
        for domain in self.PLATFORM_DOMAINS:
            if domain in url_lower:
                return False

        # Exclude review sites and social media
        for domain in self.EXCLUDE_DOMAINS:
            if domain in url_lower:
                return False

        # Good signals in title/snippet
        good_signals = [
            'vacation rental',
            'direct booking',
            'book direct',
            'property rental',
            'rental property',
            'beach house',
            'beach rental',
            'mountain cabin',
            'villa rental',
            'cottage rental',
            'condo rental',
        ]

        content = f"{title} {snippet}".lower()
        has_good_signal = any(signal in content for signal in good_signals)

        return has_good_signal

    def find_owner_websites(
        self,
        property_details: Dict,
        max_queries: int = 5,
        max_results_per_query: int = 10
    ) -> List[Dict]:
        """
        Find potential owner direct booking websites.

        Args:
            property_details: Property information dict
            max_queries: Maximum number of search queries to try
            max_results_per_query: Max results to fetch per query

        Returns:
            List of candidate websites with metadata:
            [
                {
                    'url': 'https://example.com',
                    'title': 'Beachfront Villa - Direct Booking',
                    'snippet': 'Book directly and save...',
                    'query': 'search query used',
                    'confidence': 0.8  # how likely this is the right site
                }
            ]
        """
        queries = self.generate_search_queries(property_details)
        queries = queries[:max_queries]  # Limit number of queries

        all_candidates = []
        seen_urls = set()

        for query in queries:
            print(f"Searching: {query}")
            results = self.search_google(query, num_results=max_results_per_query)

            for result in results:
                url = result['link']
                title = result['title']
                snippet = result['snippet']

                # Skip duplicates
                if url in seen_urls:
                    continue

                # Filter out non-owner sites
                if not self.is_likely_owner_site(url, title, snippet):
                    continue

                seen_urls.add(url)
                all_candidates.append({
                    'url': url,
                    'title': title,
                    'snippet': snippet,
                    'query': query,
                    'confidence': self._calculate_confidence(result, property_details)
                })

        # Sort by confidence score
        all_candidates.sort(key=lambda x: x['confidence'], reverse=True)

        return all_candidates

    def _calculate_confidence(self, result: Dict, property_details: Dict) -> float:
        """
        Calculate confidence score (0-1) that this is the correct owner site.

        Factors (in priority order):
        - Host name match (HIGHEST - often the property management company)
        - Property name match
        - Address match
        - Booking-related keywords
        - Domain quality

        Args:
            result: Search result dict
            property_details: Original property details

        Returns:
            Confidence score 0.0-1.0
        """
        score = 0.4  # Base score (increased from 0.5 to make room for higher bonuses)

        url = result.get('link', '').lower()
        title = result.get('title', '').lower()
        snippet = result.get('snippet', '').lower()
        content = f"{title} {snippet}"

        # ===================================================================
        # HOST NAME MATCH - HIGHEST PRIORITY (up to +0.50)
        # ===================================================================
        # The host name is often the property management company name
        # Examples: "Abode Park City", "Mountain West Vacation Rentals"
        host_name = property_details.get('host_name') or ''
        if host_name:
            host_name_lower = host_name.lower()

            # Check if host name is in the domain itself (VERY strong signal)
            # Example: host="Abode Park City" and url="abodeparkcity.com"
            host_name_clean = ''.join(c for c in host_name_lower if c.isalnum())
            if host_name_clean and host_name_clean in url.replace('-', '').replace('.', ''):
                score += 0.50  # Very high confidence!

            # Check if host name is in title or snippet
            elif host_name_lower in content:
                score += 0.35  # High confidence

            # Partial match (e.g., "Abode" in "Abode Vacation Rentals")
            elif any(word.lower() in content for word in host_name.split() if len(word) > 3):
                score += 0.20

        # ===================================================================
        # PROPERTY NAME MATCH (up to +0.25)
        # ===================================================================
        property_name = property_details.get('property_name') or ''
        if property_name and property_name.lower() in content:
            score += 0.25

        # ===================================================================
        # ADDRESS MATCH (up to +0.15)
        # ===================================================================
        address = property_details.get('address') or ''
        if address and address.lower() in content:
            score += 0.15

        # ===================================================================
        # BOOKING KEYWORDS (+0.10)
        # ===================================================================
        booking_keywords = ['direct booking', 'book direct', 'reserve now', 'book now', 'availability']
        if any(keyword in content for keyword in booking_keywords):
            score += 0.10

        # ===================================================================
        # PROFESSIONAL DOMAIN (+0.05)
        # ===================================================================
        # Custom domain is better than free hosting
        free_hosting = ['blogspot', 'wordpress.com', 'wix.com', 'weebly', 'squarespace']
        if not any(host in url for host in free_hosting):
            score += 0.05

        # Cap at 1.0
        return min(score, 1.0)


def test_owner_finder():
    """Test the owner website finder with a sample property."""
    finder = OwnerWebsiteFinder()

    # Test property details
    property_details = {
        'address': '123 Ocean View Dr, Malibu, CA',
        'property_name': 'Sunset Beach Villa',
        'host_name': 'John Smith',
        'city': 'Malibu',
        'region': 'California',
        'property_type': 'beach house'
    }

    print("=" * 60)
    print("Testing Owner Website Finder")
    print("=" * 60)
    print(f"\nProperty: {property_details['property_name']}")
    print(f"Location: {property_details['city']}, {property_details['region']}")
    print(f"Host: {property_details['host_name']}")

    candidates = finder.find_owner_websites(property_details, max_queries=3)

    print(f"\n\nFound {len(candidates)} potential owner websites:")
    print("-" * 60)

    for i, candidate in enumerate(candidates[:5], 1):  # Show top 5
        print(f"\n{i}. {candidate['title']}")
        print(f"   URL: {candidate['url']}")
        print(f"   Confidence: {candidate['confidence']:.2f}")
        print(f"   Snippet: {candidate['snippet'][:100]}...")

    return candidates


if __name__ == "__main__":
    test_owner_finder()
