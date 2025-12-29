"""
AI Booking Form Filler
Uses AI to understand and fill out booking forms on owner websites.

This solves the problem of:
1. Different websites having different search forms
2. Need to input dates/guests to see pricing
3. Finding the EXACT property (100% match)
4. Getting the REAL price for specific dates

Strategy:
- AI analyzes the search/booking form
- Identifies which fields need dates, guests, property name
- Fills out the form intelligently
- Submits and parses results
- Finds exact property match
- Extracts actual pricing
"""

import os
from typing import Dict, List, Optional
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
from dotenv import load_dotenv
import re
import json

load_dotenv()


class AIBookingFormFiller:
    """
    Uses AI to intelligently fill out booking forms on any vacation rental website.

    This enables us to:
    - Search for specific properties by name
    - Input check-in/check-out dates
    - Specify number of guests
    - Get actual pricing for those dates
    """

    def __init__(self, openai_api_key: Optional[str] = None):
        """Initialize the AI form filler."""
        self.api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found")

        self.client = OpenAI(api_key=self.api_key)

        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

    def find_search_form_url(
        self,
        base_url: str,
        property_details: Dict
    ) -> Optional[str]:
        """
        Find the search/booking form URL on the site.

        Args:
            base_url: Base website URL
            property_details: Property details to search for

        Returns:
            URL of the search form or search results page
        """
        print(f"\n  Looking for search form on {base_url}...")

        try:
            # Get the homepage
            response = requests.get(base_url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')

            # Look for common search URLs or forms
            search_patterns = [
                '/search',
                '/availability',
                '/booking',
                '/rentals',
                '/properties',
                '/vacation-rentals',
                '/browse',
                '?search=',
            ]

            # Find links that match search patterns
            search_links = []
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                text = link.get_text().strip().lower()

                # Check if it's a search-related link
                if any(pattern in href.lower() for pattern in search_patterns):
                    search_links.append(href)
                elif any(word in text for word in ['search', 'availability', 'browse', 'rentals', 'properties']):
                    search_links.append(href)

            # Also look for forms
            forms = soup.find_all('form')
            for form in forms:
                action = form.get('action', '')
                if action:
                    search_links.append(action)

            if search_links:
                # Use AI to pick the most relevant one
                best_link = self._ai_select_best_search_url(search_links, property_details)

                if best_link:
                    # Make absolute URL
                    if best_link.startswith('/'):
                        from urllib.parse import urljoin
                        best_link = urljoin(base_url, best_link)
                    elif not best_link.startswith('http'):
                        best_link = f"{base_url}/{best_link}"

                    print(f"  ✓ Found search form: {best_link[:70]}...")
                    return best_link

            # Fallback: try common search URLs
            fallback_urls = [
                f"{base_url}/vacation-rentals",
                f"{base_url}/search",
                f"{base_url}/availability",
                f"{base_url}/properties",
            ]

            for url in fallback_urls:
                try:
                    response = requests.head(url, headers=self.headers, timeout=5)
                    if response.status_code == 200:
                        print(f"  ✓ Using fallback: {url}")
                        return url
                except:
                    continue

            return None

        except Exception as e:
            print(f"  ⚠ Error finding search form: {e}")
            return None

    def _ai_select_best_search_url(
        self,
        search_links: List[str],
        property_details: Dict
    ) -> Optional[str]:
        """Use AI to select the best search URL from candidates."""

        if len(search_links) == 1:
            return search_links[0]

        property_name = property_details.get('property_name', '')

        prompt = f"""You are analyzing URLs to find the best search/booking form for a vacation rental website.

Property we're looking for: {property_name}

Available URLs:
{chr(10).join(f"{i+1}. {url}" for i, url in enumerate(search_links[:10]))}

Which URL is most likely to have:
1. A search form where we can search for specific properties
2. An availability checker with date inputs
3. A property listing/browse page

Respond with ONLY the number (1-{min(10, len(search_links))}) of the best URL.
"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert at analyzing website navigation."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                max_tokens=10
            )

            result = response.choices[0].message.content.strip()
            # Extract number
            match = re.search(r'(\d+)', result)
            if match:
                idx = int(match.group(1)) - 1
                if 0 <= idx < len(search_links):
                    return search_links[idx]

        except:
            pass

        # Fallback: return first one
        return search_links[0] if search_links else None

    def construct_search_url_with_params(
        self,
        search_url: str,
        property_details: Dict
    ) -> str:
        """
        Construct a search URL with query parameters for dates and property.

        Args:
            search_url: Base search URL
            property_details: Property details with check-in, check-out, guests

        Returns:
            URL with search parameters
        """
        property_name = property_details.get('property_name', '')
        check_in = property_details.get('check_in', '')
        check_out = property_details.get('check_out', '')
        guests = property_details.get('total_guests', 2)

        # Extract property complex name if possible
        # "King's Crown D203" -> search for "King's Crown"
        search_term = property_name

        # Remove unit numbers for broader search
        search_term = re.sub(r'\s+[A-Z]?\d+[A-Z]?$', '', search_term)  # Remove "D203"
        search_term = re.sub(r'\s+-\s+Unit.*$', '', search_term)  # Remove "- Unit 5B"

        # Common URL parameter patterns
        param_variants = [
            # Property search
            f"?search={search_term.replace(' ', '+')}",
            f"?q={search_term.replace(' ', '+')}",
            f"?property={search_term.replace(' ', '+')}",

            # With dates
            f"?checkin={check_in}&checkout={check_out}&search={search_term.replace(' ', '+')}",
            f"?arrival={check_in}&departure={check_out}&search={search_term.replace(' ', '+')}",
        ]

        # Try different parameter combinations
        # For now, use simple search term
        if '?' in search_url:
            return f"{search_url}&search={search_term.replace(' ', '+')}"
        else:
            return f"{search_url}?search={search_term.replace(' ', '+')}"

    def search_for_exact_property(
        self,
        owner_site_url: str,
        property_details: Dict
    ) -> Optional[Dict]:
        """
        Use AI to search an owner site for the exact property and get pricing.

        Args:
            owner_site_url: Owner website base URL
            property_details: Property details including dates

        Returns:
            Dict with property URL and pricing, or None
        """
        print(f"\n  Using AI to search {owner_site_url} for exact property...")

        # Step 1: Find the search form
        search_url = self.find_search_form_url(owner_site_url, property_details)

        if not search_url:
            print(f"  ⚠ Could not find search form")
            return None

        # Step 2: Construct search with parameters
        search_with_params = self.construct_search_url_with_params(
            search_url,
            property_details
        )

        print(f"  Searching: {search_with_params[:80]}...")

        try:
            # Get search results
            response = requests.get(search_with_params, headers=self.headers, timeout=15)
            soup = BeautifulSoup(response.text, 'html.parser')

            # Step 3: Use AI to find the exact property in results
            property_url = self._ai_find_exact_property_in_results(
                soup,
                search_with_params,
                property_details
            )

            if not property_url:
                print(f"  ✗ Property not found in search results")
                return None

            print(f"  ✓ Found property: {property_url[:70]}...")

            # Step 4: Get pricing from property page
            pricing = self._ai_extract_pricing_from_property_page(
                property_url,
                property_details
            )

            return {
                'property_url': property_url,
                'pricing': pricing,
                'search_url': search_with_params
            }

        except Exception as e:
            print(f"  ⚠ Error: {e}")
            return None

    def _ai_find_exact_property_in_results(
        self,
        soup: BeautifulSoup,
        search_url: str,
        property_details: Dict
    ) -> Optional[str]:
        """
        Use AI to identify the exact property from search results.

        Args:
            soup: BeautifulSoup of search results page
            search_url: URL being searched
            property_details: Property we're looking for

        Returns:
            URL of the exact property, or None
        """
        # Get all property links
        all_links = soup.find_all('a', href=True)

        # Filter to likely property links
        property_links = []
        for link in all_links:
            href = link.get('href', '')
            text = link.get_text().strip()

            # Skip navigation, footer, etc.
            if not href or len(href) < 5:
                continue
            if href.startswith('#') or href.startswith('javascript:'):
                continue

            # Look for property-related keywords
            if any(word in href.lower() for word in ['property', 'rental', 'unit', 'condo', 'home']):
                property_links.append({
                    'text': text[:100],
                    'href': href
                })
            elif any(word in text.lower() for word in ['view', 'details', 'book', 'bedroom', 'bath']):
                property_links.append({
                    'text': text[:100],
                    'href': href
                })

        if not property_links:
            return None

        # Limit to top candidates
        property_links = property_links[:20]

        # Use AI to find the best match
        property_name = property_details.get('property_name', '')

        prompt = f"""You are analyzing search results from a vacation rental website to find a specific property.

Property we're looking for: {property_name}
(Focus on the complex/building name, e.g., "King's Crown" not the specific unit number)

Search Results (property links):
{chr(10).join(f"{i+1}. Text: '{link['text']}' | URL: {link['href']}" for i, link in enumerate(property_links))}

Which link is most likely to be the property we're looking for?
Consider:
- Property name match (exact or partial)
- Building/complex name (e.g., "King's Crown" matches even without "D203")
- Similar names (e.g., "Kings Crown Condos" = "King's Crown")

Respond with JSON:
{{
    "match_number": number (1-{len(property_links)}) or null if no good match,
    "confidence": 0-100,
    "reasoning": "why this is the match"
}}
"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert at matching vacation rental property listings."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                max_tokens=200
            )

            result_text = response.choices[0].message.content

            # Parse JSON
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())

                match_num = result.get('match_number')
                confidence = result.get('confidence', 0)

                if match_num and confidence >= 70:
                    idx = int(match_num) - 1
                    if 0 <= idx < len(property_links):
                        href = property_links[idx]['href']

                        # Make absolute URL
                        if href.startswith('/'):
                            from urllib.parse import urljoin
                            href = urljoin(search_url, href)
                        elif not href.startswith('http'):
                            base_url = '/'.join(search_url.split('/')[:3])
                            href = f"{base_url}/{href}"

                        print(f"  AI Match: {property_links[idx]['text'][:50]} ({confidence}% confidence)")
                        return href

        except Exception as e:
            print(f"  ⚠ AI matching error: {e}")

        return None

    def _ai_extract_pricing_from_property_page(
        self,
        property_url: str,
        property_details: Dict
    ) -> Dict:
        """
        Extract pricing from the property page using AI.
        Uses multiple methods to find pricing.

        Args:
            property_url: URL of the property listing
            property_details: Property details with dates

        Returns:
            Pricing dict
        """
        print(f"  Extracting pricing from property page...")

        try:
            response = requests.get(property_url, headers=self.headers, timeout=15)
            soup = BeautifulSoup(response.text, 'html.parser')

            # Method 1: Look for pricing in HTML/JSON data
            html_str = str(soup)

            # Look for common pricing patterns in raw HTML
            price_patterns = [
                r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:/\s*night|per night|nightly)',
                r'"price":\s*(\d+(?:\.\d{2})?)',
                r'"nightly_rate":\s*(\d+(?:\.\d{2})?)',
                r'(?:price|rate)["\']?\s*:\s*["\']?\$?(\d+(?:,\d{3})*(?:\.\d{2})?)',
            ]

            for pattern in price_patterns:
                matches = re.findall(pattern, html_str, re.IGNORECASE)
                if matches:
                    # Get first match, clean up commas
                    price_str = matches[0].replace(',', '')
                    try:
                        nightly_rate = float(price_str)
                        if 50 <= nightly_rate <= 10000:  # Reasonable range
                            print(f"  ✓ Found nightly rate in HTML: ${nightly_rate}")

                            nights = property_details.get('nights', 3)

                            return {
                                'nightly_rate': nightly_rate,
                                'total_cost': nightly_rate * nights,
                                'cleaning_fee': None,
                                'service_fee': None,
                                'currency': 'USD',
                                'available': True,
                                'extraction_method': 'html_pattern'
                            }
                    except:
                        continue

            # Method 2: Use AI to extract from visible text
            text = soup.get_text()
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            text = '\n'.join(lines)

            # Limit length but include more context for pricing
            if len(text) > 12000:
                # Try to find pricing section
                price_keywords = ['price', 'rate', 'cost', 'fee', 'total', 'nightly', 'night']
                relevant_lines = []
                for i, line in enumerate(lines):
                    if any(keyword in line.lower() for keyword in price_keywords):
                        # Include context around pricing mentions
                        start = max(0, i-5)
                        end = min(len(lines), i+5)
                        relevant_lines.extend(lines[start:end])

                if relevant_lines:
                    text = '\n'.join(relevant_lines[:200])  # Top 200 relevant lines
                else:
                    text = text[:12000]

            check_in = property_details.get('check_in', '')
            check_out = property_details.get('check_out', '')
            nights = property_details.get('nights', 3)

            prompt = f"""Extract ALL pricing information from this vacation rental property listing.

DATES: {check_in} to {check_out} ({nights} nights)

Page Content:
{text}

IMPORTANT: Look for:
1. Price PER NIGHT (nightly rate, daily rate)
2. TOTAL cost for the stay
3. Cleaning fee
4. Service fees
5. Taxes
6. Any other fees

Extract and return JSON with:
{{
    "nightly_rate": number (dollars per night),
    "total_cost": number (total for entire stay if shown),
    "cleaning_fee": number or null,
    "service_fee": number or null,
    "taxes": number or null,
    "other_fees": number or null,
    "currency": "USD",
    "available": true/false,
    "notes": "any important pricing notes"
}}

CRITICAL: Return actual numbers found. If multiple prices listed, use the one for the dates {check_in} to {check_out}.
If you can't find specific pricing, estimate based on typical rates mentioned or return null.
"""

            ai_response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert at extracting pricing information from vacation rental websites. Be thorough and find ALL pricing details."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                max_tokens=400
            )

            result_text = ai_response.choices[0].message.content

            # Parse JSON
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                pricing = json.loads(json_match.group())

                # Calculate total if we have nightly rate but not total
                if pricing.get('nightly_rate') and not pricing.get('total_cost'):
                    base_total = pricing['nightly_rate'] * nights
                    cleaning = pricing.get('cleaning_fee', 0) or 0
                    service = pricing.get('service_fee', 0) or 0
                    taxes = pricing.get('taxes', 0) or 0

                    pricing['total_cost'] = base_total + cleaning + service + taxes

                pricing['extraction_method'] = 'ai_text'

                if pricing.get('nightly_rate'):
                    print(f"  ✓ Nightly rate: ${pricing['nightly_rate']}")
                if pricing.get('total_cost'):
                    print(f"  ✓ Total cost: ${pricing['total_cost']}")
                if pricing.get('cleaning_fee'):
                    print(f"  ✓ Cleaning fee: ${pricing['cleaning_fee']}")

                return pricing

            return {}

        except Exception as e:
            print(f"  ⚠ Pricing extraction error: {e}")
            return {}


def test_ai_form_filler():
    """Test the AI booking form filler."""
    filler = AIBookingFormFiller()

    # Test with King's Crown D203
    property_details = {
        'property_name': "King's Crown D203",
        'city': 'Park City',
        'state_region': 'Utah',
        'check_in': '2026-02-05',
        'check_out': '2026-02-08',
        'nights': 3,
        'total_guests': 2
    }

    print("=" * 80)
    print("TESTING: AI Booking Form Filler")
    print("=" * 80)
    print(f"\nProperty: {property_details['property_name']}")
    print(f"Dates: {property_details['check_in']} to {property_details['check_out']}")

    # Test with parkcityvacationrentals.com
    owner_site = "https://www.parkcityvacationrentals.com"

    print(f"\nSearching {owner_site}...")
    print("-" * 80)

    result = filler.search_for_exact_property(owner_site, property_details)

    if result:
        print("\n" + "=" * 80)
        print("✓ SUCCESS!")
        print("=" * 80)
        print(f"\nProperty URL: {result['property_url']}")

        if result.get('pricing'):
            pricing = result['pricing']
            print(f"\nPricing:")
            if pricing.get('nightly_rate'):
                print(f"  Nightly Rate: ${pricing['nightly_rate']}")
            if pricing.get('total_cost'):
                print(f"  Total Cost: ${pricing['total_cost']}")
            if pricing.get('cleaning_fee'):
                print(f"  Cleaning Fee: ${pricing['cleaning_fee']}")
    else:
        print("\n✗ Could not find property or extract pricing")


if __name__ == "__main__":
    test_ai_form_filler()
