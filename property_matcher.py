"""
Property Matcher
Searches candidate owner websites to find the specific property listing.

Takes property details from Airbnb and searches owner sites to find if that
exact property is listed there.
"""

import re
import requests
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()


class PropertyMatcher:
    """
    Searches owner websites for specific properties using intelligent matching.

    Strategy:
    1. Search the owner site for property details (address, name, features)
    2. Extract potential property page URLs
    3. Visit those pages and verify it's the same property
    4. Return the exact property URL or None if not found
    """

    def __init__(self, openai_api_key: Optional[str] = None):
        """Initialize property matcher."""
        self.api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found")

        self.client = OpenAI(api_key=self.api_key)

        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

    def fetch_page(self, url: str) -> Optional[str]:
        """Fetch webpage HTML."""
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"  Error fetching {url[:50]}: {e}")
            return None

    def search_site_for_property(
        self,
        site_url: str,
        property_details: Dict
    ) -> Optional[str]:
        """
        Search an owner website for a specific property.

        Args:
            site_url: Base URL of owner website
            property_details: Dict with Airbnb property details

        Returns:
            Specific property URL if found, None otherwise
        """
        print(f"\n  Searching {urlparse(site_url).netloc} for property...")

        # Fetch the main page
        html = self.fetch_page(site_url)
        if not html:
            return None

        soup = BeautifulSoup(html, 'html.parser')

        # Extract all property/rental links from the page
        property_links = self._extract_property_links(soup, site_url)

        if not property_links:
            print(f"    No property links found on page")
            return None

        print(f"    Found {len(property_links)} property links")

        # Use AI to find the best matching link
        best_match = self._find_best_matching_link(
            property_links,
            property_details
        )

        return best_match

    def _extract_property_links(
        self,
        soup: BeautifulSoup,
        base_url: str
    ) -> List[Dict]:
        """
        Extract all potential property listing links from a page.

        Args:
            soup: BeautifulSoup object
            base_url: Base URL for resolving relative links

        Returns:
            List of dicts with link info
        """
        links = []
        seen_urls = set()

        # Look for links that might be property listings
        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(base_url, href)

            # Skip if already seen
            if full_url in seen_urls:
                continue

            # Skip external links (different domain)
            if urlparse(full_url).netloc != urlparse(base_url).netloc:
                continue

            # Skip common non-property pages
            skip_patterns = [
                '/search', '/about', '/contact', '/blog', '/faq',
                '/terms', '/privacy', '/login', '/cart', '/checkout'
            ]

            if any(pattern in full_url.lower() for pattern in skip_patterns):
                continue

            # Look for indicators it's a property page
            text = link.get_text().strip().lower()
            href_lower = href.lower()

            property_indicators = [
                'bedroom', 'bath', 'view', 'rental', 'condo', 'house',
                'cabin', 'villa', 'apartment', 'property', 'unit'
            ]

            if any(indicator in text or indicator in href_lower for indicator in property_indicators):
                seen_urls.add(full_url)
                links.append({
                    'url': full_url,
                    'text': link.get_text().strip()[:100],
                    'href': href
                })

        return links[:20]  # Limit to first 20 to avoid too many checks

    def _find_best_matching_link(
        self,
        property_links: List[Dict],
        property_details: Dict
    ) -> Optional[str]:
        """
        Use AI to find which link best matches the property details.

        Args:
            property_links: List of potential property links
            property_details: Airbnb property details

        Returns:
            Best matching URL or None
        """
        # Create a summary of links for AI
        links_summary = "\n".join([
            f"{i+1}. {link['text']} ({link['url']})"
            for i, link in enumerate(property_links[:15])  # Limit to 15
        ])

        # Extract key details
        address = property_details.get('address', 'Unknown')
        property_name = property_details.get('property_name', 'Unknown')
        city = property_details.get('city', 'Unknown')
        bedrooms = property_details.get('bedrooms', 'Unknown')
        property_type = property_details.get('property_type', 'vacation rental')

        prompt = f"""Find which link matches this vacation rental property:

Property Details:
- Name: {property_name}
- Address: {address}
- City: {city}
- Type: {property_type}
- Bedrooms: {bedrooms}

Available Links:
{links_summary}

Which link number (1-{len(property_links[:15])}) is most likely THIS specific property?
Consider:
- Address matches
- Property name matches
- Bedroom count matches
- Location matches

Respond with JSON:
{{
    "best_match_number": number or null,
    "confidence": 0-100,
    "reasoning": "why this is or isn't a match"
}}

If none match well, set best_match_number to null."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert at matching vacation rental properties across different websites."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                max_tokens=200
            )

            result_text = response.choices[0].message.content

            # Parse JSON
            import json
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                result = json.loads(result_text)

            best_number = result.get('best_match_number')
            confidence = result.get('confidence', 0)

            if best_number and confidence >= 60:
                matched_link = property_links[best_number - 1]
                print(f"    ✓ Found match: {matched_link['text']}")
                print(f"      Confidence: {confidence}%")
                return matched_link['url']
            else:
                print(f"    ✗ No confident match found")
                return None

        except Exception as e:
            print(f"    Error in AI matching: {e}")
            return None

    def verify_property_match(
        self,
        property_url: str,
        property_details: Dict
    ) -> Dict:
        """
        Verify that a property page actually matches our Airbnb listing.

        Args:
            property_url: URL of potential matching property
            property_details: Airbnb property details

        Returns:
            Dict with match result and confidence
        """
        print(f"\n  Verifying property match...")

        html = self.fetch_page(property_url)
        if not html:
            return {
                'match': False,
                'confidence': 0,
                'reason': 'Could not fetch property page'
            }

        soup = BeautifulSoup(html, 'html.parser')

        # Extract visible text
        for tag in soup(['script', 'style', 'nav', 'footer']):
            tag.decompose()

        text = soup.get_text()
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        text = '\n'.join(lines)[:6000]  # Limit length

        # Use AI to verify match
        address = property_details.get('address', '')
        property_name = property_details.get('property_name', '')
        city = property_details.get('city', '')
        bedrooms = property_details.get('bedrooms', '')
        bathrooms = property_details.get('bathrooms', '')
        property_type = property_details.get('property_type', '')

        prompt = f"""Verify if this property page matches our target property.

Target Property (from Airbnb):
- Name: {property_name}
- Address: {address}
- City: {city}
- Type: {property_type}
- Bedrooms: {bedrooms}
- Bathrooms: {bathrooms}

Property Page Content:
{text}

Is this the SAME property? Respond with JSON:
{{
    "is_match": true/false,
    "confidence": 0-100,
    "reasoning": "explanation",
    "matching_details": ["detail1", "detail2"],
    "conflicting_details": ["conflict1", "conflict2"]
}}"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert at verifying property matches."},
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
                result = json.loads(json_match.group())
            else:
                result = json.loads(result_text)

            is_match = result.get('is_match', False)
            confidence = result.get('confidence', 0)

            if is_match and confidence >= 70:
                print(f"    ✓ VERIFIED MATCH! Confidence: {confidence}%")
                return {
                    'match': True,
                    'confidence': confidence,
                    'property_url': property_url,
                    **result
                }
            else:
                print(f"    ✗ Not a match (confidence: {confidence}%)")
                return {
                    'match': False,
                    'confidence': confidence,
                    **result
                }

        except Exception as e:
            print(f"    Error verifying: {e}")
            return {
                'match': False,
                'confidence': 0,
                'reason': f'Error: {str(e)}'
            }


def test_property_matcher():
    """Test the property matcher."""
    matcher = PropertyMatcher()

    print("=" * 80)
    print("TESTING: Property Matcher")
    print("=" * 80)

    # Example property details (from Airbnb scraper)
    property_details = {
        'property_name': 'Luxurious 3BR Condo - Ski In/Ski Out',
        'address': '1234 Resort Drive, Park City, UT 84060',
        'city': 'Park City',
        'state_region': 'Utah',
        'property_type': 'condo',
        'bedrooms': 3,
        'bathrooms': 2
    }

    # Example owner website
    test_url = "https://luxehausvacations.com/search-results/luxe-haus-collection/park-city-vacation-rentals/park-city-condo-rentals/"

    result = matcher.search_site_for_property(test_url, property_details)

    if result:
        print(f"\n✓ Found property at: {result}")

        # Verify the match
        verification = matcher.verify_property_match(result, property_details)

        if verification['match']:
            print(f"\n🎉 CONFIRMED: This is the same property!")
            print(f"Confidence: {verification['confidence']}%")
        else:
            print(f"\n✗ Not verified as same property")
    else:
        print(f"\n✗ Property not found on this site")


if __name__ == "__main__":
    test_property_matcher()
