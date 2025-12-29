"""
Multi-Tier Search System
Supports free demo, basic free search, BYOK (bring your own key), and premium tiers.
"""
import os
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Optional
from enum import Enum

from scraper import GoogleImageSearch, AirbnbImageScraper
from image_searchers import SmartAirbnbScraper
from multi_modal_search import MultiModalPropertySearcher


class SearchTier(Enum):
    """Search tier levels"""
    DEMO = "demo"           # Pre-cached examples (free, no API calls)
    FREE = "free"           # Basic search (Selenium only, no AI)
    BYOK = "byok"           # Bring Your Own Key (user's API keys)
    PREMIUM = "premium"     # Full AI with our keys (paid)


class TieredSearchManager:
    """Manages different search tiers to control costs."""

    def __init__(self):
        self.demo_cache = self._load_demo_results()
        self.result_cache = {}
        self.cache_duration = timedelta(hours=24)

    def _load_demo_results(self) -> Dict:
        """Load pre-cached demo results for portfolio visitors."""
        # These would be real results from test runs
        # Stored to show capability without API costs
        return {
            "demo_1": {
                "airbnb_url": "https://www.airbnb.com/rooms/12345",
                "property": {
                    "title": "Luxury 3BR Beachfront Villa with Pool",
                    "location": "Miami Beach, FL"
                },
                "verified_matches": 5,
                "best_price": 245.00,
                "savings": 55.00,
                "timestamp": "2024-01-15"
            }
            # Add more demo examples
        }

    def search(self,
               airbnb_url: str,
               tier: SearchTier,
               user_api_keys: Optional[Dict] = None,
               user_id: Optional[str] = None) -> Dict:
        """
        Execute search based on tier level.

        Args:
            airbnb_url: Airbnb listing URL
            tier: SearchTier level
            user_api_keys: User's API keys (for BYOK tier)
            user_id: User identifier (for rate limiting)

        Returns:
            Search results dictionary
        """
        if tier == SearchTier.DEMO:
            return self._demo_search()

        elif tier == SearchTier.FREE:
            return self._free_search(airbnb_url)

        elif tier == SearchTier.BYOK:
            if not user_api_keys:
                raise ValueError("BYOK tier requires user API keys")
            return self._byok_search(airbnb_url, user_api_keys)

        elif tier == SearchTier.PREMIUM:
            return self._premium_search(airbnb_url)

        else:
            raise ValueError(f"Unknown tier: {tier}")

    def _demo_search(self) -> Dict:
        """Return pre-cached demo results (zero cost)."""
        return {
            "tier": "demo",
            "cost": 0,
            "demo_data": self.demo_cache["demo_1"],
            "message": "This is a demo result. Sign up for free searches or premium for real-time results!"
        }

    def _free_search(self, airbnb_url: str) -> Dict:
        """
        Free tier: Selenium-based image search only (no AI, no API costs).
        Good for portfolio demonstration.
        """
        print("\n=== FREE TIER SEARCH (Selenium Only) ===")

        try:
            # Check cache first
            cached = self._check_cache(airbnb_url)
            if cached:
                cached['tier'] = 'free'
                cached['from_cache'] = True
                return cached

            # Scrape Airbnb
            airbnb_scraper = AirbnbImageScraper()
            image_url = airbnb_scraper.fetch_first_image_link(airbnb_url)

            if not image_url:
                return {
                    "tier": "free",
                    "error": "Could not extract image from Airbnb listing",
                    "upgrade_message": "Premium tier offers text-based search as fallback"
                }

            # Reverse image search with Selenium (free)
            image_searcher = GoogleImageSearch()
            results = image_searcher.search_by_image(image_url)

            result = {
                "tier": "free",
                "cost": 0,
                "airbnb_url": airbnb_url,
                "candidates": results,
                "num_results": len(results),
                "verified": False,
                "prices_extracted": False,
                "upgrade_benefits": [
                    "AI verification to confirm matches",
                    "Automatic price extraction",
                    "Text-based search for more results",
                    "Smart search query generation"
                ],
                "message": "Free tier results. Upgrade for AI verification and price extraction!"
            }

            # Cache it
            self._cache_result(airbnb_url, result)

            return result

        except Exception as e:
            return {
                "tier": "free",
                "error": str(e),
                "cost": 0
            }

    def _byok_search(self, airbnb_url: str, user_api_keys: Dict) -> Dict:
        """
        BYOK (Bring Your Own Key): Full AI search using user's API keys.
        Zero cost to you, full features for user.
        """
        print("\n=== BYOK TIER SEARCH (User's API Keys) ===")

        try:
            # Validate user provided required keys
            if 'openai' not in user_api_keys and 'anthropic' not in user_api_keys:
                return {
                    "tier": "byok",
                    "error": "Please provide at least one AI API key (OpenAI or Anthropic)",
                    "cost_to_user": "Estimated $0.10-0.30"
                }

            # Use user's keys
            model_provider = "openai" if 'openai' in user_api_keys else "anthropic"
            model_name = "gpt-4" if model_provider == "openai" else "claude-sonnet-4-5"

            searcher = MultiModalPropertySearcher(
                model_provider=model_provider,
                model_name=model_name,
                openai_api_key=user_api_keys.get('openai'),
                anthropic_api_key=user_api_keys.get('anthropic'),
                serpapi_key=user_api_keys.get('serpapi'),
                use_selenium_image_search=True
            )

            results = searcher.search_property(airbnb_url)

            return {
                "tier": "byok",
                "cost_to_you": 0,  # User pays
                "cost_to_user": "~$0.10-0.30",
                **results
            }

        except Exception as e:
            return {
                "tier": "byok",
                "error": str(e),
                "cost_to_you": 0
            }

    def _premium_search(self, airbnb_url: str) -> Dict:
        """
        Premium tier: Full AI search using your API keys.
        This costs money, so charge user accordingly.
        """
        print("\n=== PREMIUM TIER SEARCH (Your API Keys) ===")

        try:
            # Check cache first (save money)
            cached = self._check_cache(airbnb_url)
            if cached:
                cached['tier'] = 'premium'
                cached['from_cache'] = True
                cached['cost_to_you'] = 0
                return cached

            # Use cheaper model to reduce costs
            # GPT-3.5-turbo instead of GPT-4 = 90% cost reduction
            searcher = MultiModalPropertySearcher(
                model_provider="openai",
                model_name="gpt-3.5-turbo",  # Cheaper than GPT-4
                use_selenium_image_search=False  # SerpAPI faster
            )

            results = searcher.search_property(airbnb_url)

            result = {
                "tier": "premium",
                "cost_to_you": 0.05,  # Actual cost with GPT-3.5
                "charged_to_user": 0.49,  # What you charge
                "profit": 0.44,
                **results
            }

            # Cache for 24 hours
            self._cache_result(airbnb_url, result)

            return result

        except Exception as e:
            return {
                "tier": "premium",
                "error": str(e),
                "cost_to_you": 0
            }

    def _check_cache(self, airbnb_url: str) -> Optional[Dict]:
        """Check if we have cached results for this URL."""
        cache_key = hashlib.md5(airbnb_url.encode()).hexdigest()

        if cache_key in self.result_cache:
            cached = self.result_cache[cache_key]
            age = datetime.now() - cached['timestamp']

            if age < self.cache_duration:
                print(f"✓ Found cached results ({age.seconds/3600:.1f}h old)")
                return cached['data']

        return None

    def _cache_result(self, airbnb_url: str, result: Dict):
        """Cache search results."""
        cache_key = hashlib.md5(airbnb_url.encode()).hexdigest()
        self.result_cache[cache_key] = {
            'data': result,
            'timestamp': datetime.now()
        }


class LocalLLMSearcher:
    """
    Alternative: Use FREE local LLMs with Ollama
    Zero API costs, runs on your server.
    """

    def __init__(self):
        # Check if Ollama is available
        try:
            from langchain_ollama import ChatOllama
            self.llm = ChatOllama(
                model="llama3.1",  # or gemma2, mistral
                base_url="http://localhost:11434"
            )
            self.available = True
        except:
            self.available = False
            print("⚠️  Ollama not available. Install from https://ollama.ai")

    def search_with_local_ai(self, airbnb_url: str) -> Dict:
        """
        Full AI search using FREE local models.
        No API costs whatsoever!
        """
        if not self.available:
            return {
                "error": "Ollama not installed",
                "install_instructions": "Visit https://ollama.ai"
            }

        # Use the same pipeline but with local LLM
        from multi_modal_search import MultiModalPropertySearcher

        # Monkey-patch to use local LLM
        # (In production, make this configurable)

        searcher = MultiModalPropertySearcher(
            model_provider="ollama",  # Would need to add this support
            use_selenium_image_search=True
        )

        results = searcher.search_property(airbnb_url)

        return {
            "tier": "local_ai",
            "cost": 0,  # FREE!
            "model": "llama3.1 (local)",
            **results
        }


# Example Flask integration
"""
from flask import Flask, request, session
from search_tiers import TieredSearchManager, SearchTier

app = Flask(__name__)
manager = TieredSearchManager()

@app.route("/search", methods=["POST"])
def search():
    airbnb_url = request.form["airbnb_url"]
    user_id = session.get("user_id")

    # Determine tier based on user subscription
    if not user_id:
        tier = SearchTier.FREE
    elif user_has_subscription(user_id):
        tier = SearchTier.PREMIUM
    elif user_has_api_keys(user_id):
        tier = SearchTier.BYOK
        user_keys = get_user_api_keys(user_id)
    else:
        tier = SearchTier.FREE

    # Execute search
    results = manager.search(
        airbnb_url=airbnb_url,
        tier=tier,
        user_api_keys=user_keys if tier == SearchTier.BYOK else None,
        user_id=user_id
    )

    return render_template("results.html", results=results)

@app.route("/demo")
def demo():
    # Show pre-cached demo (portfolio visitors)
    results = manager.search(
        airbnb_url="demo",
        tier=SearchTier.DEMO
    )
    return render_template("demo.html", results=results)
"""


if __name__ == "__main__":
    # Test different tiers
    manager = TieredSearchManager()

    # Demo tier (free)
    print("\n1. Testing DEMO tier...")
    demo_results = manager.search("demo", SearchTier.DEMO)
    print(f"Cost: ${demo_results['cost']}")

    # Free tier (Selenium only)
    print("\n2. Testing FREE tier...")
    test_url = "https://www.airbnb.com/rooms/12345"
    free_results = manager.search(test_url, SearchTier.FREE)
    print(f"Cost: ${free_results['cost']}")
    print(f"Results: {free_results.get('num_results', 0)}")

    # Premium tier (your keys, charged)
    print("\n3. Testing PREMIUM tier...")
    # premium_results = manager.search(test_url, SearchTier.PREMIUM)
    # print(f"Cost to you: ${premium_results['cost_to_you']}")
    # print(f"Profit: ${premium_results['profit']}")
