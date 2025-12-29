"""
Similar Property Finder
Finds comparable vacation rentals across platforms to maximize affiliate opportunities.

CRITICAL BUSINESS FEATURE:
- Even when exact match not found, show similar options
- Provides affiliate revenue opportunities (60-70% conversion)
- Better UX - users always get options
- Example: Show other King's Crown units, nearby condos with affiliate links
"""

import os
from typing import Dict, List, Optional
from openai import OpenAI
from dotenv import load_dotenv
import re

load_dotenv()


class SimilarPropertyFinder:
    """
    Finds similar properties across booking platforms using AI-powered matching.

    Use Cases:
    1. Exact match not found → show nearby alternatives
    2. Owner site found → show platform alternatives for comparison
    3. Same complex/building → show other available units
    4. All results include affiliate links where possible
    """

    def __init__(self, openai_api_key: Optional[str] = None):
        """Initialize the similar property finder."""
        self.api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found")

        self.client = OpenAI(api_key=self.api_key)

    def generate_search_criteria(self, property_details: Dict) -> Dict:
        """
        Generate search criteria for finding similar properties.

        Args:
            property_details: Original property details from Airbnb

        Returns:
            Dict with search criteria and weights
        """
        city = property_details.get('city', '')
        state = property_details.get('state_region', '')
        property_type = property_details.get('property_type', 'vacation rental')
        bedrooms = property_details.get('bedrooms') or 0
        bathrooms = property_details.get('bathrooms') or 0
        max_guests = property_details.get('max_guests') or 0
        amenities = property_details.get('amenities', [])

        # Extract property complex/building if available
        property_name = property_details.get('property_name', '')
        complex_name = self._extract_complex_name(property_name)

        criteria = {
            'location': {
                'city': city,
                'state': state,
                'radius_miles': 0.5 if complex_name else 2.0,  # Smaller radius if same complex
                'weight': 0.35
            },
            'complex': {
                'name': complex_name,
                'same_building': bool(complex_name),
                'weight': 0.25 if complex_name else 0.0
            },
            'property_specs': {
                'type': property_type,
                'bedrooms': bedrooms,
                'bedroom_range': (max(0, bedrooms - 1), bedrooms + 1),  # ±1 bedroom
                'bathrooms': bathrooms,
                'max_guests': max_guests,
                'weight': 0.15
            },
            'amenities': {
                'must_have': amenities[:5] if amenities else [],  # Top 5 amenities
                'weight': 0.15
            },
            'price': {
                'reference': property_details.get('price_per_night', 0),
                'range_percent': 30,  # ±30%
                'weight': 0.10
            }
        }

        return criteria

    def _extract_complex_name(self, property_name: str) -> Optional[str]:
        """
        Extract complex/building name from property name.

        Examples:
            "King's Crown D203" → "King's Crown"
            "Deer Valley Resort - Unit 5B" → "Deer Valley Resort"
            "Sunset Beach Villa" → None (standalone)

        Args:
            property_name: Full property name

        Returns:
            Complex name or None
        """
        if not property_name:
            return None

        # Look for patterns: "Complex Name Unit/Room/Apt #"
        patterns = [
            r'^(.+?)\s+[A-Z]?\d+[A-Z]?$',  # "King's Crown D203"
            r'^(.+?)\s+-\s+Unit',  # "Name - Unit 5B"
            r'^(.+?)\s+-\s+Room',
            r'^(.+?)\s+-\s+Apt',
            r'^(.+?)\s+#\d+',  # "Name #123"
        ]

        for pattern in patterns:
            match = re.search(pattern, property_name, re.IGNORECASE)
            if match:
                complex_name = match.group(1).strip()
                # Only return if it's substantial (not just a letter/number)
                if len(complex_name) > 3:
                    return complex_name

        return None

    def calculate_similarity_score(
        self,
        original_property: Dict,
        candidate_property: Dict,
        criteria: Dict
    ) -> float:
        """
        Calculate similarity score (0-100) using AI.

        Args:
            original_property: Original Airbnb property
            candidate_property: Candidate similar property
            criteria: Search criteria with weights

        Returns:
            Similarity score 0-100
        """
        prompt = f"""Calculate how similar these two vacation rental properties are.

Original Property (from Airbnb):
- Name: {original_property.get('property_name')}
- Location: {original_property.get('city')}, {original_property.get('state_region')}
- Type: {original_property.get('property_type')}
- Bedrooms: {original_property.get('bedrooms')}
- Bathrooms: {original_property.get('bathrooms')}
- Amenities: {', '.join(original_property.get('amenities', [])[:5])}
- Price: ${original_property.get('price_per_night', 'N/A')}/night

Candidate Property:
- Name: {candidate_property.get('name')}
- Location: {candidate_property.get('location')}
- Type: {candidate_property.get('type')}
- Bedrooms: {candidate_property.get('bedrooms')}
- Bathrooms: {candidate_property.get('bathrooms')}
- Amenities: {', '.join(candidate_property.get('amenities', []))}
- Price: ${candidate_property.get('price', 'N/A')}/night

Scoring Criteria:
- Same complex/building: {criteria['complex']['weight'] * 100}% weight
- Location proximity: {criteria['location']['weight'] * 100}% weight
- Property specs match: {criteria['property_specs']['weight'] * 100}% weight
- Amenities match: {criteria['amenities']['weight'] * 100}% weight
- Price similarity: {criteria['price']['weight'] * 100}% weight

Respond with JSON:
{{
    "similarity_score": 0-100,
    "category": "same_complex" | "nearby" | "city_wide",
    "reasoning": "brief explanation",
    "matching_features": ["feature1", "feature2"],
    "differences": ["diff1", "diff2"]
}}

Categories:
- same_complex: 90-100 (same building, different unit)
- nearby: 80-89 (within 0.5 miles, similar specs)
- city_wide: 70-79 (same city, similar features)"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert at comparing vacation rental properties."},
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
                return result.get('similarity_score', 0)
            else:
                return 0

        except Exception as e:
            print(f"Error calculating similarity: {e}")
            return 0

    def find_similar_properties(
        self,
        original_property: Dict,
        platform_results: List[Dict],
        min_similarity: float = 70.0
    ) -> List[Dict]:
        """
        Find and rank similar properties from platform search results.

        Args:
            original_property: Original Airbnb property details
            platform_results: List of properties from Booking.com, VRBO, etc.
            min_similarity: Minimum similarity score to include (0-100)

        Returns:
            List of similar properties sorted by similarity score
        """
        print(f"\nAnalyzing {len(platform_results)} candidate properties...")

        criteria = self.generate_search_criteria(original_property)
        similar_properties = []

        for i, candidate in enumerate(platform_results, 1):
            if i % 10 == 0:
                print(f"  Analyzed {i}/{len(platform_results)}...")

            # Calculate similarity score
            similarity = self.calculate_similarity_score(
                original_property,
                candidate,
                criteria
            )

            if similarity >= min_similarity:
                similar_properties.append({
                    **candidate,
                    'similarity_score': similarity,
                    'category': self._categorize_similarity(similarity)
                })

        # Sort by similarity score (highest first)
        similar_properties.sort(key=lambda x: x['similarity_score'], reverse=True)

        print(f"\n✓ Found {len(similar_properties)} similar properties (≥{min_similarity}% match)")

        return similar_properties

    def _categorize_similarity(self, score: float) -> str:
        """Categorize similarity score into human-readable categories."""
        if score >= 90:
            return "same_complex"
        elif score >= 80:
            return "nearby"
        elif score >= 70:
            return "city_wide"
        else:
            return "different"

    def format_results_for_user(
        self,
        similar_properties: List[Dict],
        original_property: Dict
    ) -> str:
        """
        Format similar property results for display to user.

        Args:
            similar_properties: List of similar properties with scores
            original_property: Original Airbnb property

        Returns:
            Formatted text for display
        """
        if not similar_properties:
            return "No similar properties found."

        output = []
        output.append(f"Similar to: {original_property.get('property_name')}")
        output.append(f"Original Price: ${original_property.get('price_per_night', 'N/A')}/night")
        output.append("\n" + "=" * 80)
        output.append("SIMILAR PROPERTIES")
        output.append("=" * 80)

        for i, prop in enumerate(similar_properties[:10], 1):  # Top 10
            score = prop['similarity_score']
            category = prop['category']

            # Category badge
            if category == "same_complex":
                badge = "🏢 SAME BUILDING"
            elif category == "nearby":
                badge = "📍 NEARBY"
            else:
                badge = "🌆 SAME AREA"

            output.append(f"\n{i}. {badge} - {score:.0f}% Match")
            output.append(f"   {prop.get('name')}")
            output.append(f"   {prop.get('location')}")
            output.append(f"   {prop.get('bedrooms')}BR / {prop.get('bathrooms')}BA")
            output.append(f"   ${prop.get('price', 'N/A')}/night")
            output.append(f"   Platform: {prop.get('platform', 'Unknown')}")

            if prop.get('affiliate_link'):
                output.append(f"   🔗 Book: {prop['affiliate_link']}")
            else:
                output.append(f"   🔗 View: {prop.get('url', 'N/A')}")

        return "\n".join(output)


def test_similar_property_finder():
    """Test the similar property finder."""
    finder = SimilarPropertyFinder()

    print("=" * 80)
    print("TESTING: Similar Property Finder")
    print("=" * 80)

    # Original property (from Airbnb)
    original = {
        'property_name': "King's Crown D203",
        'city': 'Park City',
        'state_region': 'Utah',
        'property_type': 'condo',
        'bedrooms': 2,
        'bathrooms': 2,
        'max_guests': 6,
        'amenities': ['Pool', 'Hot Tub', 'Ski In/Ski Out', 'WiFi', 'Kitchen'],
        'price_per_night': 400
    }

    # Mock platform results (in real implementation, these come from platform searchers)
    platform_results = [
        {
            'name': "King's Crown B101",
            'location': 'Park City, Utah',
            'type': 'condo',
            'bedrooms': 2,
            'bathrooms': 2,
            'amenities': ['Pool', 'Hot Tub', 'Ski Access', 'WiFi'],
            'price': 380,
            'platform': 'Booking.com',
            'affiliate_link': 'https://booking.com/...',
            'url': 'https://booking.com/kings-crown-b101'
        },
        {
            'name': 'Deer Valley Luxury Condo',
            'location': 'Park City, Utah',
            'type': 'condo',
            'bedrooms': 3,
            'bathrooms': 2,
            'amenities': ['Hot Tub', 'Mountain View', 'WiFi'],
            'price': 420,
            'platform': 'VRBO',
            'affiliate_link': 'https://vrbo.com/...',
            'url': 'https://vrbo.com/deer-valley'
        },
        {
            'name': 'Park City Downtown Apartment',
            'location': 'Park City, Utah',
            'type': 'apartment',
            'bedrooms': 1,
            'bathrooms': 1,
            'amenities': ['WiFi', 'Kitchen'],
            'price': 200,
            'platform': 'Hotels.com',
            'url': 'https://hotels.com/downtown-apt'
        }
    ]

    print(f"\nOriginal Property: {original['property_name']}")
    print(f"Testing with {len(platform_results)} platform results...")

    similar = finder.find_similar_properties(
        original,
        platform_results,
        min_similarity=70.0
    )

    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)

    for prop in similar:
        print(f"\n{prop['name']}")
        print(f"  Similarity: {prop['similarity_score']:.0f}%")
        print(f"  Category: {prop['category']}")
        print(f"  Price: ${prop['price']}/night")


if __name__ == "__main__":
    test_similar_property_finder()
