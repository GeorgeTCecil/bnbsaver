"""
Test the FREE tier - Selenium-based search (no AI, no API costs)
This is what portfolio visitors will use.
"""
import sys
from search_tiers import TieredSearchManager, SearchTier

if len(sys.argv) < 2:
    print("Usage: python test_free_tier.py <airbnb_url>")
    sys.exit(1)

airbnb_url = sys.argv[1]

print("=" * 80)
print("FREE TIER TEST (Selenium Only - $0 Cost)")
print("=" * 80)
print(f"\nURL: {airbnb_url}\n")

manager = TieredSearchManager()

print("Running FREE tier search (no AI, no API costs)...")
print("This uses Selenium for reverse image search only.\n")

results = manager.search(airbnb_url, SearchTier.FREE)

print("\n" + "=" * 80)
print("RESULTS")
print("=" * 80)

if results.get("error"):
    print(f"\n❌ Error: {results['error']}")
else:
    print(f"\n✓ Tier: {results['tier'].upper()}")
    print(f"✓ Cost to you: ${results['cost']}")
    print(f"✓ Candidates found: {results.get('num_results', 0)}")

    if results.get('from_cache'):
        print("✓ From cache (even faster!)")

    candidates = results.get('candidates', [])
    if candidates:
        print(f"\nFound {len(candidates)} potential listings:")
        for i, url in enumerate(candidates[:10], 1):
            print(f"  {i}. {url}")

        if len(candidates) > 10:
            print(f"  ... and {len(candidates) - 10} more")

    # Show upgrade benefits
    if results.get('upgrade_benefits'):
        print("\n" + "-" * 80)
        print("UPGRADE TO PREMIUM FOR:")
        print("-" * 80)
        for benefit in results['upgrade_benefits']:
            print(f"  ✓ {benefit}")

print("\n" + "=" * 80)
print("FREE TIER TEST COMPLETE")
print("=" * 80)
print("\nThis is what your portfolio visitors will see!")
print("Zero cost to you, shows off your scraping skills.")
