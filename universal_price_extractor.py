"""
Universal Price Extractor
Works on ANY vacation rental website to extract real pricing for specific dates.

Works with:
- Owner direct sites
- Booking.com
- VRBO
- Hotels.com
- Any other platform

Strategy:
1. Visit the property URL
2. Look for pricing directly on page
3. If booking widget exists, extract pricing from it
4. Use AI to understand and extract ALL pricing components
"""

import os
from typing import Dict, Optional
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
from dotenv import load_dotenv
import re
import json

load_dotenv()


class UniversalPriceExtractor:
    """
    Extracts pricing from ANY vacation rental website.
    """

    def __init__(self, openai_api_key: Optional[str] = None):
        """Initialize the price extractor."""
        self.api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found")

        self.client = OpenAI(api_key=self.api_key)

        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

    def extract_price_from_url(
        self,
        url: str,
        check_in: str,
        check_out: str,
        nights: int = 3
    ) -> Dict:
        """
        Extract pricing from any vacation rental URL.

        Args:
            url: Property listing URL
            check_in: Check-in date (YYYY-MM-DD)
            check_out: Check-out date (YYYY-MM-DD)
            nights: Number of nights

        Returns:
            Pricing dict with:
            {
                'nightly_rate': float,
                'total_cost': float,
                'cleaning_fee': float,
                'service_fee': float,
                'platform': str,
                'currency': str
            }
        """
        print(f"\n  Extracting price from: {url[:60]}...")

        try:
            # Add date parameters to URL if not already there
            url_with_dates = self._add_date_params_to_url(url, check_in, check_out)

            # Fetch the page
            response = requests.get(url_with_dates, headers=self.headers, timeout=15)
            soup = BeautifulSoup(response.text, 'html.parser')
            html_str = str(soup)

            # Detect platform
            platform = self._detect_platform(url)

            # Method 1: Pattern matching in HTML
            price_html = self._extract_price_from_html(html_str, platform)
            if price_html:
                print(f"  ✓ Found price in HTML: ${price_html['nightly_rate']}/night")
                return {**price_html, 'platform': platform}

            # Method 2: AI extraction from visible text
            price_ai = self._extract_price_with_ai(soup, check_in, check_out, nights, platform)
            if price_ai:
                print(f"  ✓ AI extracted price: ${price_ai.get('nightly_rate', 0)}/night")
                return {**price_ai, 'platform': platform}

            print(f"  ⚠ Could not extract pricing")
            return {}

        except Exception as e:
            print(f"  ✗ Error: {e}")
            return {}

    def _add_date_params_to_url(self, url: str, check_in: str, check_out: str) -> str:
        """Add date parameters to URL if they're missing."""

        # If dates already in URL, return as-is
        if check_in in url or 'checkin' in url.lower():
            return url

        # Determine platform and add appropriate parameters
        if 'booking.com' in url:
            separator = '&' if '?' in url else '?'
            return f"{url}{separator}checkin={check_in}&checkout={check_out}"
        elif 'vrbo.com' in url:
            separator = '&' if '?' in url else '?'
            return f"{url}{separator}arrival={check_in}&departure={check_out}"
        elif 'hotels.com' in url:
            separator = '&' if '?' in url else '?'
            return f"{url}{separator}checkIn={check_in}&checkOut={check_out}"
        else:
            # Generic approach
            separator = '&' if '?' in url else '?'
            return f"{url}{separator}checkin={check_in}&checkout={check_out}"

    def _detect_platform(self, url: str) -> str:
        """Detect which platform the URL is from."""
        url_lower = url.lower()

        if 'booking.com' in url_lower:
            return 'Booking.com'
        elif 'vrbo.com' in url_lower:
            return 'VRBO'
        elif 'hotels.com' in url_lower:
            return 'Hotels.com'
        elif 'airbnb.com' in url_lower:
            return 'Airbnb'
        elif 'expedia.com' in url_lower:
            return 'Expedia'
        else:
            return 'Owner Direct'

    def _extract_price_from_html(self, html_str: str, platform: str) -> Optional[Dict]:
        """Extract pricing using pattern matching in HTML."""

        # Platform-specific patterns
        if platform == 'Booking.com':
            patterns = [
                r'b_price_no_default[^>]*>[\s\$]*(\d+(?:,\d{3})*(?:\.\d{2})?)',
                r'"price":\s*"?(\d+(?:\.\d{2})?)"?',
                r'data-price["\']?\s*=\s*["\']?(\d+(?:,\d{3})*(?:\.\d{2})?)',
            ]
        elif platform == 'VRBO':
            patterns = [
                r'"listPrice":\s*(\d+(?:\.\d{2})?)',
                r'price-value[^>]*>[\s\$]*(\d+(?:,\d{3})*(?:\.\d{2})?)',
                r'"rateNightly":\s*(\d+(?:\.\d{2})?)',
            ]
        else:
            # Generic patterns
            patterns = [
                r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:/\s*night|per night|nightly)',
                r'"price":\s*(\d+(?:\.\d{2})?)',
                r'"nightly_rate":\s*(\d+(?:\.\d{2})?)',
                r'(?:price|rate)["\']?\s*[:=]\s*["\']?\$?(\d+(?:,\d{3})*(?:\.\d{2})?)',
            ]

        for pattern in patterns:
            matches = re.findall(pattern, html_str, re.IGNORECASE)
            if matches:
                for match in matches:
                    try:
                        price_str = match.replace(',', '')
                        price = float(price_str)

                        if 20 <= price <= 20000:  # Reasonable range
                            return {
                                'nightly_rate': price,
                                'total_cost': None,  # Will calculate
                                'cleaning_fee': None,
                                'service_fee': None,
                                'currency': 'USD',
                                'extraction_method': 'html_pattern'
                            }
                    except:
                        continue

        return None

    def _extract_price_with_ai(
        self,
        soup: BeautifulSoup,
        check_in: str,
        check_out: str,
        nights: int,
        platform: str
    ) -> Optional[Dict]:
        """Extract pricing using AI."""

        # Get text content
        text = soup.get_text()
        lines = [line.strip() for line in text.splitlines() if line.strip()]

        # Focus on pricing-related content
        price_keywords = ['price', 'rate', 'cost', 'fee', 'total', 'nightly', 'night', '$', 'usd']
        relevant_lines = []

        for i, line in enumerate(lines):
            if any(keyword in line.lower() for keyword in price_keywords):
                start = max(0, i-3)
                end = min(len(lines), i+3)
                relevant_lines.extend(lines[start:end])

        if not relevant_lines:
            relevant_lines = lines[:300]

        text = '\n'.join(relevant_lines[:400])  # Limit context

        prompt = f"""Extract pricing from this {platform} vacation rental listing.

Dates: {check_in} to {check_out} ({nights} nights)

Content:
{text}

Extract and return JSON:
{{
    "nightly_rate": number (price per night in USD),
    "total_cost": number (total for {nights} nights, if shown),
    "cleaning_fee": number or null,
    "service_fee": number or null,
    "taxes": number or null,
    "currency": "USD",
    "available": true/false
}}

CRITICAL: Find the ACTUAL pricing numbers. Look for $ amounts, rates, totals.
If total is not shown, leave as null (we'll calculate it).
Return only numbers found on the page.
"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": f"You are an expert at extracting pricing from {platform} listings. Be precise and thorough."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                max_tokens=300
            )

            result_text = response.choices[0].message.content

            # Parse JSON
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                pricing = json.loads(json_match.group())

                # Calculate total if not provided
                if pricing.get('nightly_rate') and not pricing.get('total_cost'):
                    base = pricing['nightly_rate'] * nights
                    cleaning = pricing.get('cleaning_fee', 0) or 0
                    service = pricing.get('service_fee', 0) or 0
                    taxes = pricing.get('taxes', 0) or 0

                    pricing['total_cost'] = base + cleaning + service + taxes

                pricing['extraction_method'] = 'ai'

                return pricing

        except Exception as e:
            print(f"  ⚠ AI extraction error: {e}")

        return None


def test_universal_extractor():
    """Test the universal price extractor."""
    extractor = UniversalPriceExtractor()

    print("=" * 80)
    print("TESTING: Universal Price Extractor")
    print("=" * 80)

    # Test URLs
    test_cases = [
        {
            'name': 'All Seasons - King\'s Crown',
            'url': 'https://www.allseasonsresortlodging.com/park-city/rentals/kings-crown-condos/',
            'check_in': '2026-02-05',
            'check_out': '2026-02-08',
            'nights': 3
        },
        # Could add Booking.com, VRBO URLs here
    ]

    for test in test_cases:
        print(f"\n{test['name']}")
        print("-" * 80)

        pricing = extractor.extract_price_from_url(
            test['url'],
            test['check_in'],
            test['check_out'],
            test['nights']
        )

        if pricing and pricing.get('nightly_rate'):
            print(f"\n✓ SUCCESS!")
            print(f"  Nightly Rate: ${pricing['nightly_rate']}")
            if pricing.get('total_cost'):
                print(f"  Total Cost: ${pricing['total_cost']:.2f}")
            if pricing.get('cleaning_fee'):
                print(f"  Cleaning Fee: ${pricing['cleaning_fee']}")
            print(f"  Platform: {pricing.get('platform')}")
        else:
            print(f"\n✗ Could not extract pricing")


if __name__ == "__main__":
    test_universal_extractor()
