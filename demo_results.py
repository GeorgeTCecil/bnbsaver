"""
Pre-generated demo results for portfolio presentation.
Shows the full capability without API costs.
"""

DEMO_RESULTS = {
    "demo_park_city_condo": {
        "airbnb_url": "https://www.airbnb.com/rooms/978259511328040023",
        "property": {
            "title": "Condo in Park City · 3 bedrooms · 5 beds · 4 baths",
            "location": "Park City, Utah",
            "property_type": "Luxury Condo",
            "bedrooms": 3,
            "bathrooms": 4,
            "max_guests": 8,
            "key_amenities": ["Ski-in/Ski-out", "Hot Tub", "Mountain View", "Fireplace", "Full Kitchen"],
            "check_in": "2026-02-05",
            "check_out": "2026-02-08",
            "nights": 3
        },
        "search_results": {
            "text_search": 12,
            "image_search": 8,
            "total_candidates": 15
        },
        "verified_matches": [
            {
                "platform": "VRBO",
                "url": "https://www.vrbo.com/example-listing-1",
                "nightly_rate": 450.00,
                "total_price": 1350.00,
                "cleaning_fee": 150.00,
                "service_fee": 189.00,
                "total_cost": 1689.00,
                "currency": "USD",
                "confidence": 0.95
            },
            {
                "platform": "Booking.com",
                "url": "https://www.booking.com/example-listing-2",
                "nightly_rate": 475.00,
                "total_price": 1425.00,
                "cleaning_fee": 125.00,
                "service_fee": 198.50,
                "total_cost": 1748.50,
                "currency": "USD",
                "confidence": 0.92
            },
            {
                "platform": "Owner Direct",
                "url": "https://example-property-website.com",
                "nightly_rate": 425.00,
                "total_price": 1275.00,
                "cleaning_fee": 100.00,
                "service_fee": 0.00,
                "total_cost": 1375.00,
                "currency": "USD",
                "confidence": 0.88,
                "note": "Direct booking - no service fees!"
            },
            {
                "platform": "Airbnb",
                "url": "https://www.airbnb.com/rooms/978259511328040023",
                "nightly_rate": 500.00,
                "total_price": 1500.00,
                "cleaning_fee": 150.00,
                "service_fee": 225.00,
                "total_cost": 1875.00,
                "currency": "USD",
                "confidence": 1.00
            }
        ],
        "best_price": {
            "platform": "Owner Direct",
            "url": "https://example-property-website.com",
            "total_cost": 1375.00,
            "savings_vs_airbnb": 500.00,
            "savings_percent": 26.7
        },
        "timing": {
            "total_seconds": 45.2,
            "scraping": 3.1,
            "ai_extraction": 2.5,
            "searches": 12.3,
            "verification": 18.4,
            "price_extraction": 8.9
        }
    },

    "demo_miami_beach_house": {
        "airbnb_url": "https://www.airbnb.com/rooms/demo-miami",
        "property": {
            "title": "Beachfront House in Miami Beach · 5 bedrooms · 8 beds · 5.5 baths",
            "location": "Miami Beach, Florida",
            "property_type": "Luxury Beach House",
            "bedrooms": 5,
            "bathrooms": 5.5,
            "max_guests": 12,
            "key_amenities": ["Ocean View", "Private Pool", "Beach Access", "Rooftop Deck", "Gourmet Kitchen"],
            "check_in": "2026-03-15",
            "check_out": "2026-03-22",
            "nights": 7
        },
        "search_results": {
            "text_search": 18,
            "image_search": 11,
            "total_candidates": 22
        },
        "verified_matches": [
            {
                "platform": "VRBO",
                "url": "https://www.vrbo.com/miami-beach-example",
                "nightly_rate": 850.00,
                "total_price": 5950.00,
                "cleaning_fee": 350.00,
                "service_fee": 823.00,
                "total_cost": 7123.00,
                "currency": "USD",
                "confidence": 0.94
            },
            {
                "platform": "Luxury Retreats",
                "url": "https://luxuryretreats.com/example",
                "nightly_rate": 900.00,
                "total_price": 6300.00,
                "cleaning_fee": 400.00,
                "service_fee": 630.00,
                "total_cost": 7330.00,
                "currency": "USD",
                "confidence": 0.89
            },
            {
                "platform": "Property Owner",
                "url": "https://miamibeachluxury.com/properties/ocean-villa",
                "nightly_rate": 800.00,
                "total_price": 5600.00,
                "cleaning_fee": 300.00,
                "service_fee": 0.00,
                "total_cost": 5900.00,
                "currency": "USD",
                "confidence": 0.91,
                "note": "Direct booking - save 20%!"
            },
            {
                "platform": "Airbnb",
                "url": "https://www.airbnb.com/rooms/demo-miami",
                "nightly_rate": 950.00,
                "total_price": 6650.00,
                "cleaning_fee": 400.00,
                "service_fee": 997.50,
                "total_cost": 8047.50,
                "currency": "USD",
                "confidence": 1.00
            }
        ],
        "best_price": {
            "platform": "Property Owner",
            "url": "https://miamibeachluxury.com/properties/ocean-villa",
            "total_cost": 5900.00,
            "savings_vs_airbnb": 2147.50,
            "savings_percent": 26.7
        },
        "timing": {
            "total_seconds": 52.8,
            "scraping": 3.4,
            "ai_extraction": 2.8,
            "searches": 15.2,
            "verification": 21.3,
            "price_extraction": 10.1
        }
    }
}


def get_demo_result(demo_key="demo_park_city_condo"):
    """Get a demo result by key."""
    return DEMO_RESULTS.get(demo_key)


def format_demo_results(demo_data):
    """Format demo results for display."""
    output = []
    output.append("=" * 80)
    output.append("BNBSAVER SEARCH RESULTS")
    output.append("=" * 80)

    prop = demo_data["property"]
    output.append(f"\n📍 {prop['title']}")
    output.append(f"   {prop['location']}")
    output.append(f"   {prop['check_in']} → {prop['check_out']} ({prop['nights']} nights)")

    output.append(f"\n🔍 Search Results:")
    search = demo_data["search_results"]
    output.append(f"   Text Search: {search['text_search']} results")
    output.append(f"   Image Search: {search['image_search']} results")
    output.append(f"   Total Candidates: {search['total_candidates']}")

    output.append(f"\n✅ Verified Matches: {len(demo_data['verified_matches'])}")

    # Sort by price
    matches = sorted(demo_data["verified_matches"], key=lambda x: x["total_cost"])

    output.append("\n" + "-" * 80)
    output.append("PRICE COMPARISON")
    output.append("-" * 80)

    for i, match in enumerate(matches, 1):
        marker = "💰 BEST PRICE" if i == 1 else f"   #{i}"
        output.append(f"\n{marker} - {match['platform']}")
        output.append(f"   ${match['nightly_rate']:.2f}/night × {prop['nights']} = ${match['total_price']:.2f}")
        if match.get('cleaning_fee'):
            output.append(f"   Cleaning Fee: ${match['cleaning_fee']:.2f}")
        if match.get('service_fee'):
            output.append(f"   Service Fee: ${match['service_fee']:.2f}")
        output.append(f"   TOTAL: ${match['total_cost']:.2f}")
        if match.get('note'):
            output.append(f"   ✨ {match['note']}")
        output.append(f"   🔗 {match['url']}")

    best = demo_data["best_price"]
    output.append("\n" + "=" * 80)
    output.append(f"💰 SAVE ${best['savings_vs_airbnb']:.2f} ({best['savings_percent']:.1f}%) by booking on {best['platform']}!")
    output.append("=" * 80)

    timing = demo_data["timing"]
    output.append(f"\n⏱️  Completed in {timing['total_seconds']:.1f}s")

    return "\n".join(output)


if __name__ == "__main__":
    # Display demo
    import sys
    demo_key = sys.argv[1] if len(sys.argv) > 1 else "demo_park_city_condo"

    demo = get_demo_result(demo_key)
    if demo:
        print(format_demo_results(demo))
    else:
        print(f"Demo '{demo_key}' not found.")
        print(f"Available demos: {', '.join(DEMO_RESULTS.keys())}")
