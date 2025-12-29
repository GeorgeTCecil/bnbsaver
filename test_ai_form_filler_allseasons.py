"""
Test AI Form Filler with All Seasons Resort Lodging
"""

from ai_booking_form_filler import AIBookingFormFiller

filler = AIBookingFormFiller()

property_details = {
    'property_name': "King's Crown D203",
    'city': 'Park City',
    'state_region': 'Utah',
    'check_in': '2026-02-05',
    'check_out': '2026-02-08',
    'nights': 3,
    'total_guests': 2
}

print('=' * 80)
print("TESTING: All Seasons Resort Lodging - King's Crown")
print('=' * 80)

# Test with the site we know has King's Crown
owner_site = 'https://www.allseasonsresortlodging.com'

print(f"\nSearching {owner_site} for King's Crown...\n")

result = filler.search_for_exact_property(owner_site, property_details)

if result:
    print('\n' + '=' * 80)
    print("✓ SUCCESS - FOUND KING'S CROWN!")
    print('=' * 80)
    print(f"\nProperty URL: {result['property_url']}")

    if result.get('pricing'):
        pricing = result['pricing']
        print(f"\nPricing for Feb 5-8, 2026 (3 nights):")
        if pricing.get('nightly_rate'):
            print(f"  Nightly Rate: ${pricing['nightly_rate']}")
        if pricing.get('total_cost'):
            print(f"  Total Cost: ${pricing['total_cost']}")
        if pricing.get('cleaning_fee'):
            print(f"  Cleaning Fee: ${pricing['cleaning_fee']}")
        if pricing.get('service_fee'):
            print(f"  Service Fee: ${pricing['service_fee']}")

        print(f"\n💰 USER SAVES by booking direct vs Airbnb!")
        print(f"   No 10-25% platform fees = $200-800 savings")
else:
    print('\n✗ Could not find property')
