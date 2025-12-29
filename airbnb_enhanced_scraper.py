"""
Enhanced Airbnb Scraper
Extracts comprehensive property details for owner site matching.

This scraper gets ALL the details we need:
- Property name/title
- Full address or detailed location
- Host name
- Property features (bedrooms, bathrooms, amenities)
- Multiple images
- Price from Airbnb for comparison
"""

import os
import re
import time
import requests
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class EnhancedAirbnbScraper:
    """
    Enhanced scraper that extracts comprehensive property details from Airbnb.

    Uses requests + BeautifulSoup (no Selenium needed) for faster scraping.
    Falls back to AI parsing if structure changes.
    """

    def __init__(self, openai_api_key: Optional[str] = None):
        """Initialize the enhanced scraper."""
        self.api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found")

        self.client = OpenAI(api_key=self.api_key)

        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        }

    def fetch_airbnb_page(self, url: str) -> Optional[str]:
        """
        Fetch Airbnb listing page HTML.

        Args:
            url: Airbnb listing URL

        Returns:
            HTML content or None
        """
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"Error fetching Airbnb page: {e}")
            return None

    def extract_from_url(self, url: str) -> Dict:
        """
        Extract basic info from the URL itself.

        Args:
            url: Airbnb URL

        Returns:
            Dict with dates, guests, listing ID
        """
        # Extract listing ID
        listing_id_match = re.search(r'/rooms/(\d+)', url)
        listing_id = listing_id_match.group(1) if listing_id_match else None

        # Extract dates
        check_in_match = re.search(r'check_in=(\d{4}-\d{2}-\d{2})', url)
        check_out_match = re.search(r'check_out=(\d{4}-\d{2}-\d{2})', url)
        check_in = check_in_match.group(1) if check_in_match else None
        check_out = check_out_match.group(1) if check_out_match else None

        # Extract guests
        adults_match = re.search(r'adults=(\d+)', url)
        children_match = re.search(r'children=(\d+)', url)
        adults = int(adults_match.group(1)) if adults_match else 0
        children = int(children_match.group(1)) if children_match else 0
        total_guests = adults + children

        return {
            'listing_id': listing_id,
            'check_in': check_in,
            'check_out': check_out,
            'total_guests': total_guests,
            'airbnb_url': url
        }

    def extract_json_data(self, html: str) -> Optional[Dict]:
        """
        Extract structured data from Airbnb's embedded JSON.

        Airbnb embeds property data in <script> tags as JSON.

        Args:
            html: Page HTML

        Returns:
            Parsed JSON data or None
        """
        soup = BeautifulSoup(html, 'html.parser')

        # Look for JSON-LD structured data
        scripts = soup.find_all('script', type='application/ld+json')

        for script in scripts:
            try:
                import json
                data = json.loads(script.string)

                # Check if it's the listing data
                if isinstance(data, dict) and data.get('@type') in ['Product', 'LodgingBusiness', 'House']:
                    return data
            except:
                continue

        return None

    def _extract_host_name(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Extract host/owner name using specific patterns.

        Args:
            soup: BeautifulSoup parsed HTML

        Returns:
            Host name or None
        """
        # Try multiple methods to find host name

        # Method 1: Search in raw HTML (before BeautifulSoup processing)
        html_str = str(soup)

        html_patterns = [
            r'Hosted by ([A-Za-z0-9\s&\'-]+)',
            r'Managed by ([A-Za-z0-9\s&\'-]+)',
            r'"hostName":"([^"]+)"',
            r'Property managed by ([A-Za-z0-9\s&\'-]+)',
        ]

        for pattern in html_patterns:
            matches = re.findall(pattern, html_str, re.IGNORECASE)
            if matches:
                # Get the most common match (sometimes appears multiple times)
                from collections import Counter
                most_common = Counter(matches).most_common(1)
                if most_common:
                    host_name = most_common[0][0].strip()
                    # Clean up
                    host_name = re.sub(r'\s*\(.*?\)\s*$', '', host_name)  # Remove (something)
                    host_name = re.sub(r'\s*·.*$', '', host_name)  # Remove · something
                    host_name = re.sub(r'\s*<.*$', '', host_name)  # Remove <tag

                    if 2 < len(host_name) < 100:  # Reasonable length
                        return host_name

        # Method 2: Look in visible text
        text_content = soup.get_text()

        text_patterns = [
            r'Hosted by ([^\n<]+)',
            r'Managed by ([^\n<]+)',
            r'Host: ([^\n<]+)',
        ]

        for pattern in text_patterns:
            match = re.search(pattern, text_content, re.IGNORECASE)
            if match:
                host_name = match.group(1).strip()
                # Clean up
                host_name = re.sub(r'\s*\(.*?\)\s*$', '', host_name)
                host_name = re.sub(r'\s*·.*$', '', host_name)

                if 2 < len(host_name) < 100:
                    return host_name

        # Method 3: Look for meta tags
        author_tag = soup.find('meta', property='author')
        if author_tag and author_tag.get('content'):
            return author_tag['content']

        return None

    def extract_with_ai(self, html: str) -> Dict:
        """
        Use AI to extract property details from HTML when structured parsing fails.

        Args:
            html: Page HTML

        Returns:
            Dict with extracted details
        """
        # Get visible text from HTML
        soup = BeautifulSoup(html, 'html.parser')

        # Try to find host name using specific patterns before general extraction
        host_name = self._extract_host_name(soup)

        # Remove scripts, styles
        for tag in soup(['script', 'style', 'nav', 'footer']):
            tag.decompose()

        text = soup.get_text()

        # Clean up and limit length
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        text = '\n'.join(lines)

        # Limit to avoid token limits
        max_chars = 8000
        if len(text) > max_chars:
            text = text[:max_chars]

        prompt = f"""Extract vacation rental property details from this Airbnb listing page.

Page Content:
{text}

IMPORTANT: Look carefully for the HOST/OWNER information. It may appear as:
- "Hosted by [Name]"
- "Managed by [Name]"
- "Property managed by [Company Name]"
- A name near profile/contact info
The host name is often a property management company (e.g., "Abode Park City", "Mountain West Vacation Rentals").

Extract and return JSON with:
{{
    "property_name": "name/title of the property",
    "address": "full address if available (street, city, state, zip)",
    "city": "city name",
    "state_region": "state or region",
    "country": "country",
    "host_name": "host's name or property management company name (VERY IMPORTANT - look for 'Hosted by' or 'Managed by')",
    "property_type": "house/condo/apartment/villa/cabin",
    "bedrooms": number,
    "bathrooms": number,
    "max_guests": number,
    "amenities": ["pool", "hot tub", "wifi", etc],
    "price_per_night": number or null,
    "description_summary": "brief description (1-2 sentences)"
}}

Be accurate. If you can't find something, use null.
Focus on unique identifying details."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert at extracting structured data from vacation rental listings."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                max_tokens=500
            )

            result_text = response.choices[0].message.content

            # Parse JSON
            import json
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                result = json.loads(result_text)

            # Use pre-extracted host name if AI didn't find it
            if host_name and not result.get('host_name'):
                result['host_name'] = host_name

            return result

        except Exception as e:
            print(f"AI extraction error: {e}")
            # Return at least the host name if we found it
            return {'host_name': host_name} if host_name else {}

    def extract_images(self, html: str) -> List[str]:
        """
        Extract all property images from the page.

        Args:
            html: Page HTML

        Returns:
            List of image URLs
        """
        soup = BeautifulSoup(html, 'html.parser')
        images = []

        # Method 1: Find og:image meta tag
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            images.append(og_image['content'])

        # Method 2: Find images in picture tags
        for img in soup.find_all('img'):
            src = img.get('src', '')
            if 'muscache.com/im/pictures' in src and src not in images:
                images.append(src)

        # Method 3: Look for images in data attributes
        for element in soup.find_all(attrs={'data-original-uri': True}):
            uri = element['data-original-uri']
            if uri and uri not in images:
                images.append(uri)

        return images[:10]  # Limit to first 10 images

    def scrape_listing(self, url: str) -> Dict:
        """
        Complete scrape of an Airbnb listing with all details.

        Args:
            url: Airbnb listing URL

        Returns:
            Dict with comprehensive property details
        """
        print(f"\nScraping Airbnb listing: {url[:60]}...")

        # Step 1: Extract from URL
        url_data = self.extract_from_url(url)

        # Step 2: Fetch page
        html = self.fetch_airbnb_page(url)
        if not html:
            return {
                'success': False,
                'error': 'Could not fetch page',
                **url_data
            }

        # Step 3: Try structured data extraction
        json_data = self.extract_json_data(html)

        # Step 4: Extract images
        images = self.extract_images(html)

        # Step 5: Use AI to extract details
        print("Using AI to extract property details...")
        ai_data = self.extract_with_ai(html)

        # Merge all data
        result = {
            'success': True,
            **url_data,
            **ai_data,
            'images': images,
            'main_image': images[0] if images else None,
        }

        # Add computed fields
        if result.get('check_in') and result.get('check_out'):
            from datetime import datetime
            check_in_date = datetime.strptime(result['check_in'], '%Y-%m-%d')
            check_out_date = datetime.strptime(result['check_out'], '%Y-%m-%d')
            result['nights'] = (check_out_date - check_in_date).days

        return result


def test_enhanced_scraper():
    """Test the enhanced scraper."""
    scraper = EnhancedAirbnbScraper()

    test_url = input("\nEnter Airbnb URL to test: ").strip()

    if not test_url or 'airbnb.com' not in test_url:
        print("Invalid Airbnb URL")
        return

    print("=" * 80)
    print("TESTING: Enhanced Airbnb Scraper")
    print("=" * 80)

    result = scraper.scrape_listing(test_url)

    print("\n" + "=" * 80)
    print("EXTRACTED PROPERTY DETAILS")
    print("=" * 80)

    if result.get('success'):
        print(f"\n✓ Successfully scraped listing!\n")

        print(f"Property Name: {result.get('property_name', 'N/A')}")
        print(f"Address: {result.get('address', 'N/A')}")
        print(f"City: {result.get('city', 'N/A')}")
        print(f"State/Region: {result.get('state_region', 'N/A')}")
        print(f"Host: {result.get('host_name', 'N/A')}")
        print(f"\nProperty Type: {result.get('property_type', 'N/A')}")
        print(f"Bedrooms: {result.get('bedrooms', 'N/A')}")
        print(f"Bathrooms: {result.get('bathrooms', 'N/A')}")
        print(f"Max Guests: {result.get('max_guests', 'N/A')}")

        if result.get('amenities'):
            print(f"Amenities: {', '.join(result['amenities'][:5])}...")

        print(f"\nCheck-in: {result.get('check_in', 'N/A')}")
        print(f"Check-out: {result.get('check_out', 'N/A')}")
        print(f"Nights: {result.get('nights', 'N/A')}")
        print(f"Guests: {result.get('total_guests', 'N/A')}")

        if result.get('price_per_night'):
            print(f"\nAirbnb Price: ${result['price_per_night']}/night")

        print(f"\nImages Found: {len(result.get('images', []))}")
        if result.get('main_image'):
            print(f"Main Image: {result['main_image'][:60]}...")

        if result.get('description_summary'):
            print(f"\nDescription: {result['description_summary']}")
    else:
        print(f"\n✗ Scraping failed: {result.get('error')}")

    return result


if __name__ == "__main__":
    test_enhanced_scraper()
