"""
Results Aggregator
Combines and ranks property search results from all sources (owner sites + platforms).

This is the core of StayScout's "True Comparison" strategy:
- Show ALL options (owner direct + platforms)
- Rank by actual best price (not our commission potential)
- Builds trust by being genuinely helpful
- Earn affiliate revenue naturally when platforms are competitive
"""

from typing import Dict, List, Optional
from similar_property_finder import SimilarPropertyFinder


class ResultsAggregator:
    """
    Aggregates and ranks property search results from multiple sources.

    Sources:
    1. Owner direct websites (no commission, but best savings)
    2. Platform exact matches (Booking.com, VRBO, Hotels.com)
    3. Similar properties (affiliate opportunities when no exact match)

    Output Format:
    - Sorted by actual best price
    - Clearly labeled (owner vs platform, affiliate vs non-affiliate)
    - Similar properties grouped separately
    """

    def __init__(self):
        """Initialize the results aggregator."""
        self.similarity_finder = SimilarPropertyFinder()

    def aggregate_results(
        self,
        original_property: Dict,
        owner_sites: List[Dict],
        platform_results: Dict[str, List[Dict]],
        min_similarity: float = 70.0
    ) -> Dict:
        """
        Aggregate and rank all search results.

        Args:
            original_property: Original Airbnb property details
            owner_sites: List of owner direct booking sites found
            platform_results: Dict of platform results:
                {
                    'Booking.com': [properties],
                    'VRBO': [properties],
                    'Hotels.com': [properties]
                }
            min_similarity: Minimum similarity score for similar properties

        Returns:
            Aggregated results dict:
            {
                'original': original_property,
                'exact_matches': [
                    {
                        'source': 'owner' | 'Booking.com' | 'VRBO' | 'Hotels.com',
                        'type': 'owner_direct' | 'platform',
                        'has_affiliate': True/False,
                        'property': {...},
                        'total_cost': 1200,
                        'savings_vs_airbnb': 300
                    }
                ],
                'similar_properties': [...],
                'stats': {
                    'total_sources_searched': 5,
                    'exact_matches_found': 3,
                    'similar_properties_found': 8,
                    'best_price_source': 'Owner Direct',
                    'max_savings': 450
                }
            }
        """
        # Flatten all platform results
        all_platform_properties = []
        for platform, properties in platform_results.items():
            all_platform_properties.extend(properties)

        # Separate exact matches from similar properties
        exact_matches = []
        all_properties_for_similarity = []

        # Add owner sites (assumed to be exact matches if found)
        for owner_site in owner_sites:
            exact_matches.append({
                'source': 'Owner Direct',
                'type': 'owner_direct',
                'has_affiliate': False,
                'property': owner_site,
                'confidence': owner_site.get('verification', {}).get('confidence', 100)
            })

        # Process platform results
        # In a real implementation, we'd verify if each is an exact match
        # For now, we'll pass them all to the similarity finder
        all_properties_for_similarity = all_platform_properties

        # Find similar properties
        print(f"\nFinding similar properties from {len(all_properties_for_similarity)} platform results...")
        similar_properties = self.similarity_finder.find_similar_properties(
            original_property,
            all_properties_for_similarity,
            min_similarity=min_similarity
        )

        # Separate high-confidence matches (90%+) from similar properties
        for prop in similar_properties:
            if prop['similarity_score'] >= 90:
                # High confidence - treat as exact match
                exact_matches.append({
                    'source': prop.get('platform', 'Unknown'),
                    'type': 'platform',
                    'has_affiliate': bool(prop.get('affiliate_link')),
                    'property': prop,
                    'confidence': prop['similarity_score'],
                    'match_category': prop['category']
                })

        # Calculate costs and rank by price
        exact_matches_ranked = self._rank_by_price(
            exact_matches,
            original_property
        )

        similar_properties_ranked = sorted(
            [p for p in similar_properties if p['similarity_score'] < 90],
            key=lambda x: x.get('price', 999999)
        )

        # Calculate stats
        stats = self._calculate_stats(
            exact_matches_ranked,
            similar_properties_ranked,
            original_property,
            platform_results
        )

        return {
            'original': original_property,
            'exact_matches': exact_matches_ranked,
            'similar_properties': similar_properties_ranked,
            'stats': stats
        }

    def _rank_by_price(
        self,
        matches: List[Dict],
        original_property: Dict
    ) -> List[Dict]:
        """
        Rank matches by actual total cost (lowest first).

        Args:
            matches: List of match dicts
            original_property: Original property for comparison

        Returns:
            Sorted list with cost calculations added
        """
        nights = original_property.get('nights', 3)
        airbnb_total = original_property.get('total_price', 0)

        for match in matches:
            prop = match['property']

            # Calculate total cost
            if match['type'] == 'owner_direct' and prop.get('total_cost'):
                # Owner site already has total cost calculated
                total = prop['total_cost']['total']
            else:
                # Platform property - calculate from nightly rate
                nightly = prop.get('price', 0)
                total = nightly * nights if nightly else 0

            match['total_cost'] = total
            match['per_night_effective'] = total / nights if nights and total else 0
            match['savings_vs_airbnb'] = airbnb_total - total if airbnb_total and total else 0

        # Sort by total cost (lowest first)
        return sorted(matches, key=lambda x: x.get('total_cost', 999999))

    def _calculate_stats(
        self,
        exact_matches: List[Dict],
        similar_properties: List[Dict],
        original_property: Dict,
        platform_results: Dict
    ) -> Dict:
        """
        Calculate statistics about the search results.

        Args:
            exact_matches: Exact match results
            similar_properties: Similar property results
            original_property: Original Airbnb property
            platform_results: Platform search results

        Returns:
            Stats dict
        """
        total_sources = 1 + len(platform_results)  # Owner finder + platforms

        best_price_source = "None"
        max_savings = 0

        if exact_matches:
            best_match = exact_matches[0]
            best_price_source = best_match['source']
            max_savings = best_match.get('savings_vs_airbnb', 0)

        return {
            'total_sources_searched': total_sources,
            'exact_matches_found': len(exact_matches),
            'similar_properties_found': len(similar_properties),
            'best_price_source': best_price_source,
            'max_savings': max_savings,
            'owner_direct_found': any(m['type'] == 'owner_direct' for m in exact_matches),
            'affiliate_opportunities': sum(1 for m in exact_matches if m.get('has_affiliate'))
        }

    def format_for_display(self, results: Dict) -> str:
        """
        Format aggregated results for user display.

        Args:
            results: Aggregated results from aggregate_results()

        Returns:
            Formatted text output
        """
        output = []
        original = results['original']
        exact_matches = results['exact_matches']
        similar = results['similar_properties']
        stats = results['stats']

        # Header
        output.append("=" * 80)
        output.append("STAYSCOUT - YOUR COMPLETE PRICE COMPARISON")
        output.append("=" * 80)
        output.append(f"\nOriginal Listing: {original.get('property_name')}")
        output.append(f"Location: {original.get('city')}, {original.get('state_region')}")
        output.append(f"Check-in: {original.get('check_in')} | Check-out: {original.get('check_out')}")
        output.append(f"Nights: {original.get('nights', 'N/A')}")

        if original.get('total_price'):
            output.append(f"Airbnb Total: ${original['total_price']:.2f}")

        # Stats summary
        output.append(f"\n✓ Searched {stats['total_sources_searched']} booking platforms for you")
        output.append(f"✓ Found {stats['exact_matches_found']} exact/near-exact matches")
        output.append(f"✓ Found {stats['similar_properties_found']} similar alternatives")

        if stats['max_savings'] > 0:
            output.append(f"\n💰 BEST DEAL: Save ${stats['max_savings']:.2f} by booking with {stats['best_price_source']}")

        # Exact Matches
        if exact_matches:
            output.append("\n" + "=" * 80)
            output.append("EXACT MATCHES - SAME PROPERTY")
            output.append("=" * 80)

            for i, match in enumerate(exact_matches, 1):
                prop = match['property']
                source = match['source']
                is_owner = match['type'] == 'owner_direct'

                # Badge
                if is_owner:
                    badge = "🏠 OWNER DIRECT"
                elif match.get('has_affiliate'):
                    badge = f"🔗 {source.upper()}"
                else:
                    badge = f"📍 {source.upper()}"

                output.append(f"\n{i}. {badge}")

                # Property name
                output.append(f"   {prop.get('name', 'Property Listing')}")

                # Pricing
                if match.get('total_cost'):
                    output.append(f"   Total: ${match['total_cost']:.2f} ({original.get('nights', 3)} nights)")
                    output.append(f"   Per Night: ${match['per_night_effective']:.2f}")

                    if match.get('savings_vs_airbnb', 0) > 0:
                        output.append(f"   💰 SAVE ${match['savings_vs_airbnb']:.2f} vs Airbnb")
                    elif match.get('savings_vs_airbnb', 0) < 0:
                        output.append(f"   ⚠️  ${abs(match['savings_vs_airbnb']):.2f} more than Airbnb")

                # URL
                url = prop.get('affiliate_link') or prop.get('url') or prop.get('property_url')
                if url:
                    if match.get('has_affiliate'):
                        output.append(f"   🔗 Book Now: {url[:60]}... (we earn a small commission)")
                    elif is_owner:
                        output.append(f"   🔗 Book Direct: {url[:60]}... (NO booking fees!)")
                    else:
                        output.append(f"   🔗 View Listing: {url[:60]}...")

                # Confidence
                if match.get('confidence') and match['confidence'] < 100:
                    output.append(f"   Match Confidence: {match['confidence']:.0f}%")

        # Similar Properties
        if similar:
            output.append("\n" + "=" * 80)
            output.append("SIMILAR PROPERTIES - GREAT ALTERNATIVES")
            output.append("=" * 80)

            for i, prop in enumerate(similar[:5], 1):  # Top 5 similar
                score = prop['similarity_score']
                category = prop['category']

                # Category badge
                if category == "nearby":
                    badge = "📍 NEARBY"
                else:
                    badge = "🌆 SAME AREA"

                output.append(f"\n{i}. {badge} - {score:.0f}% Match")
                output.append(f"   {prop.get('name')}")
                output.append(f"   {prop.get('location')}")
                output.append(f"   {prop.get('bedrooms')}BR / {prop.get('bathrooms')}BA")

                if prop.get('price'):
                    output.append(f"   ${prop['price']}/night")

                if prop.get('affiliate_link'):
                    output.append(f"   🔗 Book: {prop['affiliate_link'][:60]}...")

        # Footer
        output.append("\n" + "=" * 80)
        output.append("HOW WE MAKE MONEY (TRANSPARENCY)")
        output.append("=" * 80)
        output.append("• Owner Direct sites: We earn NOTHING (help you save 10-25%!)")
        output.append("• Platform links marked 🔗: We earn a small commission")
        output.append("• We show ALL results honestly - your savings come first")
        output.append("\nBuilt with ❤️ by StayScout")

        return "\n".join(output)


def test_results_aggregator():
    """Test the results aggregator with mock data."""
    aggregator = ResultsAggregator()

    # Mock original property
    original = {
        'property_name': "King's Crown D203",
        'city': 'Park City',
        'state_region': 'Utah',
        'bedrooms': 2,
        'bathrooms': 2,
        'amenities': ['Pool', 'Hot Tub', 'Ski In/Ski Out'],
        'price_per_night': 400,
        'total_price': 1200,
        'nights': 3,
        'check_in': '2026-02-05',
        'check_out': '2026-02-08'
    }

    # Mock owner site results
    owner_sites = [
        {
            'site_name': 'Abode Park City',
            'property_url': 'https://abodeparkcity.com/kings-crown-d203',
            'total_cost': {
                'total': 950,
                'per_night_effective': 316.67
            },
            'verification': {'confidence': 95}
        }
    ]

    # Mock platform results
    platform_results = {
        'Booking.com': [
            {
                'name': "King's Crown B101",
                'location': 'Park City, Utah',
                'type': 'condo',
                'bedrooms': 2,
                'bathrooms': 2,
                'amenities': ['Pool', 'Hot Tub'],
                'price': 380,
                'platform': 'Booking.com',
                'affiliate_link': 'https://booking.com/kings-crown-b101',
                'url': 'https://booking.com/kings-crown-b101'
            },
            {
                'name': 'Park City Mountain Resort',
                'location': 'Park City, Utah',
                'type': 'condo',
                'bedrooms': 2,
                'bathrooms': 2,
                'amenities': ['Pool', 'Ski Access'],
                'price': 390,
                'platform': 'Booking.com',
                'affiliate_link': 'https://booking.com/pc-mountain',
                'url': 'https://booking.com/pc-mountain'
            }
        ],
        'VRBO': [
            {
                'name': "King's Crown C305",
                'location': 'Park City, Utah',
                'type': 'condo',
                'bedrooms': 3,
                'bathrooms': 2,
                'amenities': ['Pool', 'Hot Tub', 'WiFi'],
                'price': 450,
                'platform': 'VRBO',
                'affiliate_link': 'https://vrbo.com/kings-crown-c305',
                'url': 'https://vrbo.com/kings-crown-c305'
            }
        ]
    }

    print("=" * 80)
    print("TESTING: Results Aggregator")
    print("=" * 80)

    # Aggregate results
    results = aggregator.aggregate_results(
        original,
        owner_sites,
        platform_results,
        min_similarity=70.0
    )

    # Display formatted output
    print("\n")
    formatted = aggregator.format_for_display(results)
    print(formatted)


if __name__ == "__main__":
    test_results_aggregator()
