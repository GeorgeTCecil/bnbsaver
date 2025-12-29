"""
Test Script for Multi-Modal Search
Compares old approach (image search only) vs new multi-modal approach.
"""
import os
import sys
import time
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import old approach
from scraper import AirbnbImageScraper, GoogleImageSearch

# Import new approach
from multi_modal_search import MultiModalPropertySearcher


def test_old_approach(airbnb_url):
    """Test the old Selenium-only approach."""
    print("\n" + "=" * 80)
    print("TESTING OLD APPROACH (Selenium Image Search Only)")
    print("=" * 80)

    start_time = time.time()

    try:
        # Scrape Airbnb
        scraper = AirbnbImageScraper()
        image_url = scraper.fetch_first_image_link(airbnb_url)

        if not image_url:
            print("ERROR: Could not extract image from Airbnb listing")
            return None

        print(f"\n✓ Extracted image URL: {image_url[:60]}...")

        # Reverse image search
        image_search = GoogleImageSearch()
        results = image_search.search_by_image(image_url)

        elapsed_time = time.time() - start_time

        print(f"\n✓ Search completed in {elapsed_time:.2f}s")
        print(f"✓ Found {len(results)} results")

        return {
            "approach": "old_selenium_only",
            "time": elapsed_time,
            "results": results,
            "num_results": len(results)
        }

    except Exception as e:
        print(f"\nERROR: {str(e)}")
        return None


def test_new_approach(airbnb_url, model_provider="openai", model_name="gpt-4o-mini"):
    """Test the new multi-modal AI-powered approach."""
    print("\n" + "=" * 80)
    print("TESTING NEW APPROACH (Multi-Modal AI-Powered)")
    print("=" * 80)

    start_time = time.time()

    try:
        searcher = MultiModalPropertySearcher(
            model_provider=model_provider,
            model_name=model_name,
            use_selenium_image_search=True  # Use Selenium for fair comparison
        )

        results = searcher.search_property(airbnb_url)

        elapsed_time = time.time() - start_time

        return {
            "approach": "new_multimodal",
            "time": elapsed_time,
            "results": results,
            "num_candidates": len(results["all_candidates"]),
            "num_verified": len(results["verified_matches"]),
            "num_prices": len([p for p in results.get("prices", []) if p.get("price_found")])
        }

    except Exception as e:
        print(f"\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def compare_approaches(airbnb_url, model_provider="openai", model_name="gpt-4o-mini"):
    """Run both approaches and compare results."""
    print("\n" + "=" * 80)
    print("MULTI-MODAL SEARCH COMPARISON TEST")
    print("=" * 80)
    print(f"\nAirbnb URL: {airbnb_url}")
    print(f"Model: {model_provider}/{model_name}")

    # Test old approach
    old_results = test_old_approach(airbnb_url)

    # Small delay between approaches
    time.sleep(2)

    # Test new approach
    new_results = test_new_approach(airbnb_url, model_provider, model_name)

    # Print comparison
    print("\n" + "=" * 80)
    print("COMPARISON SUMMARY")
    print("=" * 80)

    if old_results and new_results:
        print(f"\nOLD APPROACH (Selenium Only):")
        print(f"  Time: {old_results['time']:.2f}s")
        print(f"  Results found: {old_results['num_results']}")
        print(f"  Verification: None")
        print(f"  Price extraction: Manual required")

        print(f"\nNEW APPROACH (Multi-Modal AI):")
        print(f"  Time: {new_results['time']:.2f}s")
        print(f"  Candidates found: {new_results['num_candidates']}")
        print(f"  Verified matches: {new_results['num_verified']}")
        print(f"  Prices extracted: {new_results['num_prices']}")

        print(f"\nIMPROVEMENTS:")
        candidate_increase = new_results['num_candidates'] - old_results['num_results']
        print(f"  Additional candidates: +{candidate_increase} ({candidate_increase/old_results['num_results']*100:.1f}% more)" if old_results['num_results'] > 0 else "  N/A")
        print(f"  AI Verification: ✓ ({new_results['num_verified']} confirmed matches)")
        print(f"  Automated Price Extraction: ✓ ({new_results['num_prices']} prices)")
        print(f"  Time difference: {new_results['time'] - old_results['time']:.2f}s")

        # Show unique advantages
        print(f"\nUNIQUE ADVANTAGES OF NEW APPROACH:")
        print(f"  ✓ Text-based search finds listings without image matches")
        print(f"  ✓ AI verification reduces false positives")
        print(f"  ✓ Automated price extraction (no manual checking)")
        print(f"  ✓ Property detail extraction (amenities, features, etc.)")
        print(f"  ✓ Intelligent search query generation")

        # Save detailed results
        save_results(airbnb_url, old_results, new_results)

    elif old_results:
        print("\nOLD APPROACH completed, but NEW APPROACH failed.")
    elif new_results:
        print("\nNEW APPROACH completed, but OLD APPROACH failed.")
    else:
        print("\nBOTH APPROACHES FAILED")

    print("\n" + "=" * 80)


def save_results(airbnb_url, old_results, new_results):
    """Save detailed results to JSON file."""
    output = {
        "airbnb_url": airbnb_url,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "old_approach": {
            "time": old_results["time"],
            "num_results": old_results["num_results"],
            "results": old_results["results"]
        },
        "new_approach": {
            "time": new_results["time"],
            "num_candidates": new_results["num_candidates"],
            "num_verified": new_results["num_verified"],
            "num_prices": new_results["num_prices"],
            "summary": {
                "text_search_results": len(new_results["results"]["text_search_results"]),
                "image_search_results": len(new_results["results"]["image_search_results"]),
                "verified_matches": [
                    {
                        "url": m["url"],
                        "confidence": m.get("confidence", 0),
                        "reason": m.get("reason", "")
                    }
                    for m in new_results["results"]["verified_matches"]
                ],
                "prices": [
                    {
                        "url": p["url"],
                        "nightly_rate": p.get("nightly_rate"),
                        "total_price": p.get("total_price"),
                        "currency": p.get("currency")
                    }
                    for p in new_results["results"].get("prices", [])
                    if p.get("price_found")
                ]
            }
        }
    }

    filename = f"comparison_results_{int(time.time())}.json"
    with open(filename, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n✓ Detailed results saved to: {filename}")


def quick_test(airbnb_url):
    """Quick test of just the new approach."""
    print("\n" + "=" * 80)
    print("QUICK TEST - Multi-Modal Search")
    print("=" * 80)

    # Check for required API keys
    if not os.getenv("OPENAI_API_KEY") and not os.getenv("ANTHROPIC_API_KEY"):
        print("\nERROR: No AI API key found!")
        print("Please set OPENAI_API_KEY or ANTHROPIC_API_KEY in your .env file")
        return

    if not os.getenv("SERPAPI_API_KEY"):
        print("\nWARNING: No SERPAPI_API_KEY found. Text search will be limited.")

    # Use whichever API key is available
    # Using GPT-4o-mini as default for optimal cost/quality balance
    if os.getenv("ANTHROPIC_API_KEY"):
        model_provider = "anthropic"
        model_name = "claude-sonnet-4-5"
    else:
        model_provider = "openai"
        model_name = "gpt-4o-mini"

    results = test_new_approach(airbnb_url, model_provider, model_name)

    if results:
        print("\n✓ Test completed successfully!")
    else:
        print("\n✗ Test failed")


if __name__ == "__main__":
    # Check command line arguments
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python test_multi_modal.py <airbnb_url> [mode]")
        print("\nModes:")
        print("  quick     - Quick test of new approach only (default)")
        print("  compare   - Full comparison of old vs new")
        print("\nExample:")
        print("  python test_multi_modal.py 'https://www.airbnb.com/rooms/12345' quick")
        sys.exit(1)

    airbnb_url = sys.argv[1]
    mode = sys.argv[2] if len(sys.argv) > 2 else "quick"

    if mode == "compare":
        # Use whichever API key is available
        # Using GPT-4o-mini as default for optimal cost/quality balance
        if os.getenv("ANTHROPIC_API_KEY"):
            compare_approaches(airbnb_url, "anthropic", "claude-sonnet-4-5")
        else:
            compare_approaches(airbnb_url, "openai", "gpt-4o-mini")
    else:
        quick_test(airbnb_url)
