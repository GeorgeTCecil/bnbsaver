"""
Quick setup test to verify environment and API keys are working.
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=" * 60)
print("BNBSAVER SETUP TEST")
print("=" * 60)

# Test 1: Check Python imports
print("\n1. Testing Python imports...")
try:
    from image_searchers import SmartAirbnbScraper, SerpApiGoogleImageSearch
    from ai_extractor import PropertyDetailExtractor, SearchQueryGenerator
    from web_searcher import ParallelWebSearcher
    from ai_verifier import ContentScraper, PropertyVerifier, PriceExtractor
    from multi_modal_search import MultiModalPropertySearcher
    print("   ✓ All modules imported successfully!")
except ImportError as e:
    print(f"   ✗ Import error: {e}")
    exit(1)

# Test 2: Check API keys
print("\n2. Checking API keys...")
serpapi_key = os.getenv("SERPAPI_API_KEY")
openai_key = os.getenv("OPENAI_API_KEY")
anthropic_key = os.getenv("ANTHROPIC_API_KEY")

if serpapi_key and serpapi_key != "your_serpapi_key_here":
    print(f"   ✓ SerpAPI key found ({serpapi_key[:20]}...)")
else:
    print("   ✗ SerpAPI key not found or invalid")

if openai_key and openai_key != "your_openai_key_here":
    print(f"   ✓ OpenAI key found ({openai_key[:20]}...)")
else:
    print("   ⚠ OpenAI key not found (optional for testing)")

if anthropic_key and anthropic_key != "your_anthropic_key_here":
    print(f"   ✓ Anthropic key found ({anthropic_key[:20]}...)")
else:
    print("   ⚠ Anthropic key not found (optional)")

# Test 3: Initialize components
print("\n3. Initializing components...")
try:
    scraper = SmartAirbnbScraper()
    print("   ✓ SmartAirbnbScraper initialized")

    if openai_key and openai_key != "your_openai_key_here":
        extractor = PropertyDetailExtractor(model_provider="openai", model_name="gpt-3.5-turbo")
        print("   ✓ PropertyDetailExtractor initialized (OpenAI)")

    if serpapi_key:
        image_search = SerpApiGoogleImageSearch()
        print("   ✓ SerpApiGoogleImageSearch initialized")

    print("\n" + "=" * 60)
    print("✓ SETUP TEST PASSED!")
    print("=" * 60)
    print("\nYou're ready to test the app!")
    print("\nNext steps:")
    print("  1. Test basic Airbnb scraping: python test_basic_scraping.py")
    print("  2. Test multi-modal search: python test_multi_modal.py <airbnb_url> quick")

except Exception as e:
    print(f"\n✗ Initialization error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
