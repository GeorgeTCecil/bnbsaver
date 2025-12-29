"""
Complete Owner Finder Pipeline Test
Tests the full end-to-end flow of finding an owner direct booking site.

This is the REAL test - can we find King's Crown D203 on any owner sites?
"""

import sys
from airbnb_enhanced_scraper import EnhancedAirbnbScraper
from owner_website_finder import OwnerWebsiteFinder
from property_matcher import PropertyMatcher
from owner_site_scraper import OwnerSiteScraper


def test_complete_pipeline(airbnb_url: str):
    """
    Complete end-to-end test of owner finder.

    Args:
        airbnb_url: Airbnb listing URL
    """
    print("=" * 80)
    print("STAYSCOUT - COMPLETE OWNER FINDER PIPELINE")
    print("=" * 80)

    # Step 1: Extract property details from Airbnb
    print("\n[STEP 1/5] Extracting property details from Airbnb...")
    print("-" * 80)

    scraper = EnhancedAirbnbScraper()
    property_details = scraper.scrape_listing(airbnb_url)

    if not property_details.get('success'):
        print(f"✗ Failed to scrape Airbnb: {property_details.get('error')}")
        return

    print(f"\n✓ Successfully extracted property details:")
    print(f"  Property: {property_details.get('property_name')}")
    print(f"  Location: {property_details.get('city')}, {property_details.get('state_region')}")
    print(f"  Type: {property_details.get('property_type')}")
    print(f"  Check-in: {property_details.get('check_in')}")
    print(f"  Check-out: {property_details.get('check_out')}")
    print(f"  Nights: {property_details.get('nights')}")
    print(f"  Images: {len(property_details.get('images', []))}")

    # Step 2: Search for owner websites
    print("\n[STEP 2/5] Searching Google for owner direct booking sites...")
    print("-" * 80)

    finder = OwnerWebsiteFinder()
    candidates = finder.find_owner_websites(
        property_details,
        max_queries=3,
        max_results_per_query=10
    )

    print(f"\n✓ Found {len(candidates)} potential owner websites")

    if not candidates:
        print("\n✗ No owner websites found. This property may be Airbnb-exclusive.")
        return

    # Show top candidates
    print("\nTop candidates:")
    for i, candidate in enumerate(candidates[:5], 1):
        print(f"  {i}. {candidate['title'][:60]}")
        print(f"     {candidate['url'][:70]}")
        print(f"     Confidence: {candidate['confidence']:.0%}")

    # Step 3: Search each candidate for the specific property
    print(f"\n[STEP 3/5] Searching each site for '{property_details.get('property_name')}'...")
    print("-" * 80)

    matcher = PropertyMatcher()
    potential_matches = []

    for i, candidate in enumerate(candidates[:8], 1):  # Check top 8
        print(f"\n{i}/{min(8, len(candidates))} Checking: {candidate['title'][:50]}...")

        try:
            property_url = matcher.search_site_for_property(
                candidate['url'],
                property_details
            )

            if property_url:
                potential_matches.append({
                    'site_name': candidate['title'],
                    'site_base_url': candidate['url'],
                    'property_url': property_url,
                    'search_confidence': candidate['confidence']
                })
        except Exception as e:
            print(f"    ✗ Error: {e}")
            continue

    if not potential_matches:
        print("\n✗ No matching properties found on owner sites")
        print("\nThis could mean:")
        print("  - Property is only available on Airbnb")
        print("  - Owner uses a different property name/ID")
        print("  - Property is on owner site but we need better search logic")
        return

    print(f"\n✓ Found {len(potential_matches)} potential match(es)!")

    # Step 4: Verify matches
    print(f"\n[STEP 4/5] Verifying property matches...")
    print("-" * 80)

    verified_matches = []

    for i, match in enumerate(potential_matches, 1):
        print(f"\n{i}. Verifying: {match['site_name'][:50]}...")
        print(f"   URL: {match['property_url'][:70]}...")

        try:
            verification = matcher.verify_property_match(
                match['property_url'],
                property_details
            )

            if verification['match'] and verification['confidence'] >= 70:
                verified_matches.append({
                    **match,
                    'verification': verification
                })
        except Exception as e:
            print(f"    ✗ Verification error: {e}")

    if not verified_matches:
        print("\n✗ No verified matches (confidence too low)")
        return

    print(f"\n✓ {len(verified_matches)} verified match(es)!")

    # Step 5: Extract pricing from verified matches
    print(f"\n[STEP 5/5] Extracting pricing from owner sites...")
    print("-" * 80)

    price_scraper = OwnerSiteScraper()
    final_results = []

    for i, match in enumerate(verified_matches, 1):
        print(f"\n{i}. Scraping: {match['site_name'][:50]}...")

        try:
            pricing = price_scraper.scrape_owner_site(
                match['property_url'],
                check_in_date=property_details.get('check_in'),
                check_out_date=property_details.get('check_out')
            )

            if pricing.get('nightly_rate'):
                cost = price_scraper.calculate_total_cost(
                    pricing,
                    property_details.get('nights', 3)
                )

                final_results.append({
                    **match,
                    'pricing': pricing,
                    'total_cost': cost
                })

                print(f"    ✓ Pricing extracted:")
                print(f"      Nightly: ${pricing['nightly_rate']}")
                if pricing.get('cleaning_fee'):
                    print(f"      Cleaning: ${pricing['cleaning_fee']}")
                print(f"      Total: ${cost['total']:.2f} for {property_details.get('nights')} nights")
            else:
                print(f"    ⚠ Could not extract pricing")
        except Exception as e:
            print(f"    ✗ Scraping error: {e}")

    # Final Results
    print("\n" + "=" * 80)
    print("🎉 FINAL RESULTS")
    print("=" * 80)

    if final_results:
        print(f"\n✓ Found {len(final_results)} owner direct booking option(s)!\n")

        for i, result in enumerate(final_results, 1):
            print(f"{i}. {result['site_name']}")
            print(f"   Property URL: {result['property_url']}")
            print(f"   Match Confidence: {result['verification']['confidence']}%")

            if result.get('total_cost'):
                cost = result['total_cost']
                print(f"   Total Cost: ${cost['total']:.2f}")
                print(f"   Effective Rate: ${cost['per_night_effective']:.2f}/night")

                # Calculate savings vs Airbnb (if we had Airbnb price)
                # airbnb_total = property_details.get('price_per_night', 0) * property_details.get('nights', 3)
                # if airbnb_total:
                #     savings = airbnb_total - cost['total']
                #     print(f"   💰 SAVE ${savings:.2f} by booking direct!")

            print()

        print("🎉 SUCCESS! Users can book directly with the owner.")
        print("   Save 10-25% in platform fees by avoiding Airbnb/VRBO!")

    else:
        print("\n⚠ Found matching properties but couldn't extract pricing")
        print("   This is still valuable - we can show the owner site link")

        if verified_matches:
            print("\nVerified owner direct options:")
            for i, match in enumerate(verified_matches, 1):
                print(f"\n{i}. {match['site_name']}")
                print(f"   URL: {match['property_url']}")
                print(f"   Confidence: {match['verification']['confidence']}%")

    print("\n" + "=" * 80)
    print("PIPELINE TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    # Test with the Park City property
    test_url = "https://www.airbnb.com/rooms/978259511328040023?adults=2&check_in=2026-02-05&check_out=2026-02-08&search_mode=regular_search&source_impression_id=p3_1765605075_P3ZhkBk4U_vskBWw"

    print("\nTesting with Park City property (King's Crown D203)")
    print(f"URL: {test_url[:70]}...\n")

    test_complete_pipeline(test_url)
