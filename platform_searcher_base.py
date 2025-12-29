"""
Base Platform Searcher
Shared logic for searching vacation rental platforms (Booking.com, VRBO, Hotels.com, etc.)

Each platform searcher:
1. Searches platform by location + property details
2. Returns list of properties with prices
3. AI can verify if specific property matches
"""

import os
from typing import Dict, List, Optional
from abc import ABC, abstractmethod
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class PlatformSearcherBase(ABC):
    """
    Base class for platform-specific searchers.

    Subclasses implement platform-specific search logic while inheriting
    common functionality like AI verification and result formatting.
    """

    def __init__(self, openai_api_key: Optional[str] = None):
        """Initialize the platform searcher."""
        self.api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found")

        self.client = OpenAI(api_key=self.api_key)

    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Return the platform name (e.g., 'Booking.com', 'VRBO')."""
        pass

    @abstractmethod
    def search_properties(
        self,
        property_details: Dict,
        check_in: str,
        check_out: str,
        max_results: int = 20
    ) -> List[Dict]:
        """
        Search platform for properties matching the criteria.

        Args:
            property_details: Original property details from Airbnb
            check_in: Check-in date (YYYY-MM-DD)
            check_out: Check-out date (YYYY-MM-DD)
            max_results: Maximum number of results to return

        Returns:
            List of property dicts:
            [
                {
                    'name': 'Property Name',
                    'location': 'City, State',
                    'type': 'condo',
                    'bedrooms': 2,
                    'bathrooms': 2,
                    'amenities': ['Pool', 'WiFi'],
                    'price': 380,  # per night
                    'url': 'https://...',
                    'platform': 'Booking.com'
                }
            ]
        """
        pass

    def generate_search_url(
        self,
        property_details: Dict,
        check_in: str,
        check_out: str
    ) -> str:
        """
        Generate platform-specific search URL.

        Args:
            property_details: Property details
            check_in: Check-in date
            check_out: Check-out date

        Returns:
            Search URL for the platform
        """
        # Override in subclass for platform-specific URL construction
        raise NotImplementedError("Subclass must implement generate_search_url")

    def extract_property_data(self, html: str) -> List[Dict]:
        """
        Extract property listings from search results HTML.

        Args:
            html: HTML content from search results page

        Returns:
            List of property dicts
        """
        # Override in subclass for platform-specific HTML parsing
        raise NotImplementedError("Subclass must implement extract_property_data")

    def verify_property_match(
        self,
        original_property: Dict,
        candidate_property: Dict
    ) -> Dict:
        """
        Use AI to verify if candidate property matches the original.

        Args:
            original_property: Original Airbnb property details
            candidate_property: Candidate property from platform search

        Returns:
            {
                'match': True/False,
                'confidence': 0-100,
                'reasoning': 'explanation'
            }
        """
        prompt = f"""Determine if these two vacation rental properties are the same property.

Original Property (from Airbnb):
- Name: {original_property.get('property_name')}
- Location: {original_property.get('city')}, {original_property.get('state_region')}
- Address: {original_property.get('address', 'N/A')}
- Type: {original_property.get('property_type')}
- Bedrooms: {original_property.get('bedrooms')}
- Bathrooms: {original_property.get('bathrooms')}

Candidate Property (from {self.platform_name}):
- Name: {candidate_property.get('name')}
- Location: {candidate_property.get('location')}
- Type: {candidate_property.get('type')}
- Bedrooms: {candidate_property.get('bedrooms')}
- Bathrooms: {candidate_property.get('bathrooms')}

Are these the EXACT SAME property? Consider:
- Same address or building/complex
- Exact same unit (not just same building)
- Same property specs (bedrooms, bathrooms)

Respond with JSON:
{{
    "match": true/false,
    "confidence": 0-100,
    "reasoning": "brief explanation"
}}

Be strict: only match if you're confident it's the EXACT same unit."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert at comparing vacation rental property listings."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                max_tokens=200
            )

            result_text = response.choices[0].message.content

            # Parse JSON
            import json
            import re
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                return {
                    'match': result.get('match', False),
                    'confidence': result.get('confidence', 0),
                    'reasoning': result.get('reasoning', '')
                }
            else:
                return {'match': False, 'confidence': 0, 'reasoning': 'Failed to parse AI response'}

        except Exception as e:
            print(f"Error verifying property match: {e}")
            return {'match': False, 'confidence': 0, 'reasoning': f'Error: {e}'}

    def add_affiliate_link(self, property_url: str) -> str:
        """
        Add affiliate tracking to property URL.

        Args:
            property_url: Original property URL

        Returns:
            URL with affiliate tracking parameters
        """
        # Override in subclass for platform-specific affiliate parameters
        # For now, return original URL (we'll add affiliate codes after approval)
        return property_url

    def format_result(self, property_dict: Dict) -> Dict:
        """
        Format search result with standardized fields.

        Args:
            property_dict: Raw property data from platform

        Returns:
            Standardized property dict for results aggregator
        """
        return {
            'name': property_dict.get('name', 'Unknown'),
            'location': property_dict.get('location', 'Unknown'),
            'type': property_dict.get('type', 'vacation rental'),
            'bedrooms': property_dict.get('bedrooms', 0),
            'bathrooms': property_dict.get('bathrooms', 0),
            'amenities': property_dict.get('amenities', []),
            'price': property_dict.get('price', 0),
            'url': property_dict.get('url', ''),
            'affiliate_link': self.add_affiliate_link(property_dict.get('url', '')),
            'platform': self.platform_name,
            'source': self.platform_name
        }
