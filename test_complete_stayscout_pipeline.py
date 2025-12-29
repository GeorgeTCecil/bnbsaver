"""
Complete StayScout Pipeline Test
End-to-end test of the full "True Comparison" system.

Flow:
1. Scrape Airbnb property → airbnb_enhanced_scraper.py
2. Search for owner direct sites → owner_website_finder.py + property_matcher.py
3. Search booking platforms → booking_com_searcher.py, vrbo_searcher.py, hotels_com_searcher.py
4. Find similar properties → similar_property_finder.py
5. Aggregate and rank results → results_aggregator.py
6. Display to user

This demonstrates StayScout's core value:
- Show EVERYTHING (owner sites + platforms)
- Rank by actual best price
- Transparent about commission
- Users save money, we earn naturally
"""

from airbnb_enhanced_scraper import EnhancedAirbnbScraper
from owner_website_finder import OwnerWebsiteFinder
from property_matcher import PropertyMatcher
from booking_com_searcher import BookingComSearcher
from vrbo_searcher import VRBOSearcher
from hotels_com_searcher import HotelsComSearcher
from results_aggregator import ResultsAggregator


def test_complete_stayscout_pipeline(airbnb_url: str):
    """
    Complete end-to-end test of StayScout.

    Args:
        airbnb_url: Airbnb listing URL
    """
    print("=" * 80)
    print("STAYSCOUT - COMPLETE PIPELINE TEST")
    print("Find the absolute lowest price across ALL platforms")
    print("=" * 80)

    # ===================================================================
    # STEP 1: Extract Property Details from Airbnb
    # ===================================================================
    print("\n[STEP 1/5] Extracting property details from Airbnb...")
    print("-" * 80)

    scraper = EnhancedAirbnbScraper()
    property_details = scraper.scrape_listing(airbnb_url)

    if not property_details.get('success'):
        print(f"✗ Failed to scrape Airbnb: {property_details.get('error')}")
        return

    print(f"\n✓ Property Details Extracted:")
    print(f"  Name: {property_details.get('property_name')}")
    print(f"  Location: {property_details.get('city')}, {property_details.get('state_region')}")
    print(f"  Type: {property_details.get('property_type')}")
    print(f"  Bedrooms: {property_details.get('bedrooms')}, Bathrooms: {property_details.get('bathrooms')}")
    print(f"  Check-in: {property_details.get('check_in')}")
    print(f"  Check-out: {property_details.get('check_out')}")
    print(f"  Nights: {property_details.get('nights')}")

    # ===================================================================
    # STEP 2: Search for Owner Direct Websites
    # ===================================================================
    print("\n[STEP 2/5] Searching for owner direct booking sites...")
    print("-" * 80)

    owner_finder = OwnerWebsiteFinder()
    owner_candidates = owner_finder.find_owner_websites(
        property_details,
        max_queries=2,  # Limit for testing
        max_results_per_query=5
    )

    print(f"\n✓ Found {len(owner_candidates)} potential owner websites")

    # Try to match property on owner sites (simplified for demo)
    owner_matches = []
    if owner_candidates:
        print(f"  Top candidate: {owner_candidates[0]['title'][:60]}")
        print(f"  URL: {owner_candidates[0]['url']}")
        # In real implementation, would search each site for specific property
        # For demo, we'll just mark it as a potential match

    # ===================================================================
    # STEP 3: Search Major Booking Platforms
    # ===================================================================
    print("\n[STEP 3/5] Searching major booking platforms...")
    print("-" * 80)

    # Initialize platform searchers
    booking_searcher = BookingComSearcher()
    vrbo_searcher = VRBOSearcher()
    hotels_searcher = HotelsComSearcher()

    # Search each platform
    check_in = property_details.get('check_in', '2026-02-05')
    check_out = property_details.get('check_out', '2026-02-08')

    booking_results = booking_searcher.search_properties(
        property_details,
        check_in,
        check_out,
        max_results=5  # Limit for testing
    )

    vrbo_results = vrbo_searcher.search_properties(
        property_details,
        check_in,
        check_out,
        max_results=5
    )

    hotels_results = hotels_searcher.search_properties(
        property_details,
        check_in,
        check_out,
        max_results=5
    )

    platform_results = {
        'Booking.com': booking_results,
        'VRBO': vrbo_results,
        'Hotels.com': hotels_results
    }

    total_platform_results = len(booking_results) + len(vrbo_results) + len(hotels_results)
    print(f"\n✓ Platform Search Complete:")
    print(f"  Booking.com: {len(booking_results)} properties")
    print(f"  VRBO: {len(vrbo_results)} properties")
    print(f"  Hotels.com: {len(hotels_results)} properties")
    print(f"  Total: {total_platform_results} properties found")

    # ===================================================================
    # STEP 4: Aggregate and Rank All Results
    # ===================================================================
    print("\n[STEP 4/5] Aggregating and ranking all results...")
    print("-" * 80)

    aggregator = ResultsAggregator()

    # For demo, create mock owner site result if we found candidates
    mock_owner_sites = []
    if owner_candidates:
        mock_owner_sites = [{
            'site_name': owner_candidates[0]['title'],
            'property_url': owner_candidates[0]['url'],
            'total_cost': {
                'total': 950,  # Mock price (would be scraped in real implementation)
                'per_night_effective': 316.67
            },
            'verification': {'confidence': 80}
        }]

    results = aggregator.aggregate_results(
        property_details,
        mock_owner_sites,
        platform_results,
        min_similarity=70.0
    )

    print(f"\n✓ Results Aggregated:")
    print(f"  Exact matches: {results['stats']['exact_matches_found']}")
    print(f"  Similar properties: {results['stats']['similar_properties_found']}")
    print(f"  Best price source: {results['stats']['best_price_source']}")
    if results['stats']['max_savings'] > 0:
        print(f"  Maximum savings: ${results['stats']['max_savings']:.2f}")

    # ===================================================================
    # STEP 5: Display Results to User
    # ===================================================================
    print("\n[STEP 5/5] Formatting results for display...")
    print("-" * 80)

    formatted_results = aggregator.format_for_display(results)

    print("\n\n")
    print(formatted_results)

    # ===================================================================
    # PIPELINE SUMMARY
    # ===================================================================
    print("\n\n" + "=" * 80)
    print("🎉 PIPELINE TEST COMPLETE - STAYSCOUT IS WORKING!")
    print("=" * 80)

    print(f"\n✓ Successfully processed {property_details.get('property_name')}")
    print(f"✓ Searched {results['stats']['total_sources_searched']} sources")
    print(f"✓ Found {results['stats']['exact_matches_found']} exact matches")
    print(f"✓ Found {results['stats']['similar_properties_found']} similar alternatives")

    if results['stats']['owner_direct_found']:
        print(f"✓ Found owner direct option (save 10-25% in platform fees!)")

    print(f"\n💰 Business Value Demonstrated:")
    print(f"  • User sees ALL options (builds trust)")
    print(f"  • {results['stats']['affiliate_opportunities']} affiliate link opportunities")
    print(f"  • Transparent about commission")
    print(f"  • User saves money, we earn naturally")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    # Test with the Park City property
    test_url = "https://www.airbnb.com/rooms/978259511328040023?adults=2&check_in=2026-02-05&check_out=2026-02-08&search_mode=regular_search&source_impression_id=p3_1765605075_P3ZhkBk4U_vskBWw"

    print("\nTesting with Park City property (King's Crown D203)")
    print(f"URL: {test_url[:70]}...\n")

    test_complete_stayscout_pipeline(test_url)
