"""
Quick test of Airbnb scraping and AI extraction.
Usage: python quick_test.py <airbnb_url>
"""
import sys
import os
from dotenv import load_dotenv

load_dotenv()

if len(sys.argv) < 2:
    print("Usage: python quick_test.py <airbnb_url>")
    print("\nExample:")
    print('  python quick_test.py "https://www.airbnb.com/rooms/12345"')
    sys.exit(1)

airbnb_url = sys.argv[1]

print("=" * 80)
print("QUICK TEST: Airbnb Scraping + AI Extraction")
print("=" * 80)
print(f"\nURL: {airbnb_url}\n")

# Test 1: Basic scraping
print("Step 1: Scraping Airbnb listing...")
from image_searchers import SmartAirbnbScraper

scraper = SmartAirbnbScraper()
details = scraper.get_listing_details(airbnb_url)

if details.get("error"):
    print(f"❌ Error: {details['error']}")
    sys.exit(1)

print("✓ Scraping successful!")
print(f"\n  Title: {details.get('title', 'N/A')}")
print(f"  Location: {details.get('location_text', 'N/A')}")
print(f"  Image URL: {details.get('main_image_url', 'N/A')[:60]}...")
print(f"  Check-in: {details.get('check_in', 'N/A')}")
print(f"  Check-out: {details.get('check_out', 'N/A')}")
print(f"  Guests: {details.get('total_guests', 'N/A')}")

# Test 2: AI extraction
print("\nStep 2: AI property detail extraction...")
from ai_extractor import PropertyDetailExtractor

# Using GPT-4o-mini for optimal cost/quality balance
extractor = PropertyDetailExtractor(model_provider="openai", model_name="gpt-4o-mini")
enhanced_details = extractor.extract_property_details(details)

if enhanced_details.get("ai_extraction_error"):
    print(f"⚠️  AI extraction error: {enhanced_details['ai_extraction_error']}")
elif enhanced_details.get("ai_extracted"):
    print("✓ AI extraction successful!")
    ai_data = enhanced_details["ai_extracted"]
    print(f"\n  Property Type: {ai_data.get('property_type', 'N/A')}")
    print(f"  Bedrooms: {ai_data.get('bedrooms', 'N/A')}")
    print(f"  Bathrooms: {ai_data.get('bathrooms', 'N/A')}")
    print(f"  Max Guests: {ai_data.get('max_guests', 'N/A')}")

    amenities = ai_data.get('key_amenities', [])
    if amenities:
        print(f"  Key Amenities: {', '.join(amenities[:5])}")

    features = ai_data.get('unique_features', [])
    if features:
        print(f"  Unique Features: {', '.join(features[:3])}")
else:
    print("⚠️  No AI data extracted")

# Test 3: Search query generation
print("\nStep 3: AI search query generation...")
from ai_extractor import SearchQueryGenerator

# Using GPT-4o-mini for optimal cost/quality balance
query_gen = SearchQueryGenerator(model_provider="openai", model_name="gpt-4o-mini")
queries = query_gen.generate_search_queries(enhanced_details, num_queries=5)

print("✓ Generated search queries:")
for i, query in enumerate(queries, 1):
    print(f"  {i}. {query}")

print("\n" + "=" * 80)
print("✅ QUICK TEST COMPLETE!")
print("=" * 80)
print("\nNext: Run full multi-modal search with:")
print(f'  python test_multi_modal.py "{airbnb_url}" quick')
