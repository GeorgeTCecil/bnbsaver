"""
Owner Site Scraper
Extracts pricing and booking information from property owner websites.

Challenge: Every owner site is different (WordPress, Wix, Squarespace, custom).
Solution: Use AI to intelligently parse pricing from any format.
"""

import os
import requests
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()


class OwnerSiteScraper:
    """
    Scrapes pricing and contact information from vacation rental owner websites.

    Uses AI to intelligently extract:
    - Nightly rates
    - Weekly/monthly rates
    - Cleaning fees
    - Availability
    - Contact information
    - Booking links
    """

    def __init__(self, openai_api_key: Optional[str] = None):
        """Initialize the scraper."""
        self.api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")

        self.client = OpenAI(api_key=self.api_key)

    def fetch_website_content(self, url: str) -> Optional[str]:
        """
        Fetch website HTML content.

        Args:
            url: Website URL

        Returns:
            HTML content string or None if fetch fails
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            return response.text

        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None

    def extract_visible_text(self, html: str) -> str:
        """
        Extract visible text from HTML, removing scripts/styles.

        Args:
            html: HTML content

        Returns:
            Cleaned text content
        """
        soup = BeautifulSoup(html, 'html.parser')

        # Remove script and style elements
        for script in soup(["script", "style", "header", "footer", "nav"]):
            script.decompose()

        # Get text
        text = soup.get_text()

        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)

        return text

    def extract_pricing_with_ai(
        self,
        website_text: str,
        check_in_date: Optional[str] = None,
        check_out_date: Optional[str] = None
    ) -> Dict:
        """
        Use AI to extract pricing information from website text.

        Args:
            website_text: Cleaned text from website
            check_in_date: Check-in date (YYYY-MM-DD format)
            check_out_date: Check-out date (YYYY-MM-DD format)

        Returns:
            Dict with pricing information
        """
        # Limit text length to avoid token limits
        max_chars = 4000
        if len(website_text) > max_chars:
            website_text = website_text[:max_chars]

        prompt = f"""Extract vacation rental pricing information from this website text.

Website Content:
{website_text}

Find and extract:
1. Nightly rate ($/night)
2. Weekly rate (if available)
3. Monthly rate (if available)
4. Cleaning fee
5. Security deposit
6. Minimum stay requirements
7. Availability/calendar information
8. Contact information (email, phone)
9. Booking URL or booking form location

{"Check-in date: " + check_in_date if check_in_date else ""}
{"Check-out date: " + check_out_date if check_out_date else ""}

Respond in JSON format:
{{
    "nightly_rate": number or null,
    "weekly_rate": number or null,
    "monthly_rate": number or null,
    "cleaning_fee": number or null,
    "security_deposit": number or null,
    "minimum_stay_nights": number or null,
    "currency": "USD",
    "pricing_notes": "any special notes about pricing",
    "available": true/false/null,
    "contact_email": "email" or null,
    "contact_phone": "phone" or null,
    "booking_url": "url" or null,
    "confidence": 0-100
}}

If information isn't found, use null. Be accurate - only extract info you're confident about."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Cheaper model for text extraction
                messages=[
                    {"role": "system", "content": "You are an expert at extracting structured pricing data from vacation rental websites."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                max_tokens=500
            )

            result_text = response.choices[0].message.content

            # Parse JSON from response
            import json
            import re

            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                pricing_data = json.loads(json_match.group())
            else:
                pricing_data = json.loads(result_text)

            return pricing_data

        except Exception as e:
            print(f"Error extracting pricing with AI: {e}")
            return {
                'error': str(e),
                'confidence': 0
            }

    def scrape_owner_site(
        self,
        url: str,
        check_in_date: Optional[str] = None,
        check_out_date: Optional[str] = None
    ) -> Dict:
        """
        Scrape complete pricing info from an owner website.

        Args:
            url: Owner website URL
            check_in_date: Check-in date (YYYY-MM-DD)
            check_out_date: Check-out date (YYYY-MM-DD)

        Returns:
            Dict with all extracted information
        """
        print(f"\nScraping owner site: {url}")

        # Fetch website
        html = self.fetch_website_content(url)
        if not html:
            return {
                'url': url,
                'success': False,
                'error': 'Failed to fetch website'
            }

        # Extract visible text
        text = self.extract_visible_text(html)

        # Use AI to extract pricing
        pricing = self.extract_pricing_with_ai(text, check_in_date, check_out_date)

        # Add metadata
        result = {
            'url': url,
            'success': True,
            'scraped_at': datetime.now().isoformat(),
            **pricing
        }

        return result

    def calculate_total_cost(
        self,
        pricing: Dict,
        nights: int
    ) -> Optional[Dict]:
        """
        Calculate total cost for a stay.

        Args:
            pricing: Pricing dict from scrape_owner_site()
            nights: Number of nights

        Returns:
            Dict with cost breakdown
        """
        if not pricing.get('nightly_rate'):
            return None

        nightly_rate = pricing['nightly_rate']
        cleaning_fee = pricing.get('cleaning_fee', 0) or 0

        # Use weekly/monthly rates if applicable and cheaper
        if nights >= 28 and pricing.get('monthly_rate'):
            base_cost = pricing['monthly_rate']
            rate_type = 'monthly'
        elif nights >= 7 and pricing.get('weekly_rate'):
            weeks = nights // 7
            extra_nights = nights % 7
            base_cost = (weeks * pricing['weekly_rate']) + (extra_nights * nightly_rate)
            rate_type = 'weekly+nightly'
        else:
            base_cost = nights * nightly_rate
            rate_type = 'nightly'

        total = base_cost + cleaning_fee

        return {
            'base_cost': base_cost,
            'cleaning_fee': cleaning_fee,
            'total': total,
            'nights': nights,
            'rate_type': rate_type,
            'per_night_effective': total / nights if nights > 0 else 0,
            'currency': pricing.get('currency', 'USD')
        }


def test_owner_scraper():
    """Test the owner site scraper."""
    scraper = OwnerSiteScraper()

    print("=" * 60)
    print("Testing Owner Site Scraper")
    print("=" * 60)

    # Example usage (needs real owner website URL)
    """
    url = "https://example-rental-site.com/my-beach-house"
    check_in = "2025-03-15"
    check_out = "2025-03-22"

    result = scraper.scrape_owner_site(url, check_in, check_out)

    print(f"\nWebsite: {url}")
    print(f"\nPricing extracted:")
    print(f"  Nightly: ${result.get('nightly_rate', 'N/A')}")
    print(f"  Cleaning Fee: ${result.get('cleaning_fee', 'N/A')}")
    print(f"  Confidence: {result.get('confidence', 0)}%")

    if result.get('nightly_rate'):
        nights = 7
        cost = scraper.calculate_total_cost(result, nights)
        print(f"\nTotal for {nights} nights: ${cost['total']:.2f}")
        print(f"  Effective rate: ${cost['per_night_effective']:.2f}/night")
    """

    print("\nOwner site scraper initialized successfully!")
    print("Ready to extract pricing from vacation rental websites.")
    print("\nCost estimate: ~$0.002 per website scrape (GPT-4o-mini)")


if __name__ == "__main__":
    test_owner_scraper()
