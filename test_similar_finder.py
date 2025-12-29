"""
Test Similar Property Finder with Full Output
Shows both the similarity scoring and the user-friendly formatted display.
"""

from similar_property_finder import SimilarPropertyFinder


def test_with_formatted_output():
    """Test similar property finder and show formatted user output."""
    finder = SimilarPropertyFinder()

    print("=" * 80)
    print("TESTING: Similar Property Finder - Complete Output")
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

    # Mock platform results (simulating what Booking.com, VRBO searchers would return)
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
            'affiliate_link': 'https://booking.com/kings-crown-b101',
            'url': 'https://booking.com/kings-crown-b101'
        },
        {
            'name': "King's Crown C305",
            'location': 'Park City, Utah',
            'type': 'condo',
            'bedrooms': 3,
            'bathrooms': 2,
            'amenities': ['Pool', 'Hot Tub', 'Ski In/Ski Out', 'WiFi', 'Kitchen'],
            'price': 450,
            'platform': 'VRBO',
            'affiliate_link': 'https://vrbo.com/kings-crown-c305',
            'url': 'https://vrbo.com/kings-crown-c305'
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
            'affiliate_link': 'https://vrbo.com/deer-valley',
            'url': 'https://vrbo.com/deer-valley'
        },
        {
            'name': 'Park City Mountain Resort Condo',
            'location': 'Park City, Utah',
            'type': 'condo',
            'bedrooms': 2,
            'bathrooms': 2,
            'amenities': ['Pool', 'WiFi', 'Ski Access'],
            'price': 390,
            'platform': 'Booking.com',
            'affiliate_link': 'https://booking.com/pc-mountain-resort',
            'url': 'https://booking.com/pc-mountain-resort'
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

    print(f"\nOriginal Airbnb Property: {original['property_name']}")
    print(f"Location: {original['city']}, {original['state_region']}")
    print(f"Price: ${original['price_per_night']}/night")
    print(f"\nSearching {len(platform_results)} platform results for similar properties...")

    # Find similar properties
    similar = finder.find_similar_properties(
        original,
        platform_results,
        min_similarity=70.0
    )

    # Show technical results
    print("\n" + "=" * 80)
    print("TECHNICAL RESULTS (for debugging)")
    print("=" * 80)

    for prop in similar:
        print(f"\n{prop['name']}")
        print(f"  Similarity Score: {prop['similarity_score']:.0f}%")
        print(f"  Category: {prop['category']}")
        print(f"  Price: ${prop['price']}/night")
        print(f"  Platform: {prop['platform']}")

    # Show user-friendly formatted output
    print("\n\n" + "=" * 80)
    print("USER-FRIENDLY OUTPUT (what customers see)")
    print("=" * 80)
    print()

    formatted_output = finder.format_results_for_user(similar, original)
    print(formatted_output)

    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)
    print("\nKey Insights:")
    print(f"  - Found {len(similar)} similar properties (≥70% match)")
    print(f"  - {sum(1 for p in similar if p['category'] == 'same_complex')} in same building")
    print(f"  - {sum(1 for p in similar if p['category'] == 'nearby')} nearby alternatives")
    print(f"  - {sum(1 for p in similar if p['category'] == 'city_wide')} city-wide matches")
    print(f"  - {sum(1 for p in similar if p.get('affiliate_link'))} have affiliate links")
    print("\nBusiness Value:")
    print("  ✓ User gets multiple booking options")
    print("  ✓ Affiliate revenue opportunities even without exact match")
    print("  ✓ Increases conversion rate (more options = higher booking rate)")


if __name__ == "__main__":
    test_with_formatted_output()
