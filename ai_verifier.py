"""
AI Verification and Price Extraction Module
Uses AI to verify property matches and extract pricing information.
"""
import os
import json
import requests
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


class ContentScraper:
    """Scrapes webpage content for AI analysis."""

    def __init__(self, timeout=30, max_content_length=10000):
        """
        Initialize the content scraper.

        Args:
            timeout: Request timeout in seconds
            max_content_length: Maximum characters to extract from page
        """
        self.timeout = timeout
        self.max_content_length = max_content_length
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        })

    def scrape_url(self, url: str) -> Dict:
        """
        Scrape content from a URL.

        Args:
            url: URL to scrape

        Returns:
            Dictionary with scraped data: {url, title, text_content, meta_description, error}
        """
        result = {
            "url": url,
            "title": None,
            "text_content": None,
            "meta_description": None,
            "error": None
        }

        try:
            response = self.session.get(url, timeout=self.timeout, allow_redirects=True)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract title
            if soup.title:
                result["title"] = soup.title.get_text(strip=True)

            # Extract meta description
            meta_desc = soup.find("meta", attrs={"name": "description"}) or \
                       soup.find("meta", property="og:description")
            if meta_desc:
                result["meta_description"] = meta_desc.get("content", "")

            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()

            # Extract text content
            text = soup.get_text(separator=" ", strip=True)

            # Limit content length
            result["text_content"] = text[:self.max_content_length]

            return result

        except requests.exceptions.RequestException as e:
            result["error"] = f"Request error: {str(e)}"
            return result
        except Exception as e:
            result["error"] = f"Scraping error: {str(e)}"
            return result

    def scrape_multiple(self, urls: List[str], max_workers=5) -> List[Dict]:
        """
        Scrape multiple URLs in parallel.

        Args:
            urls: List of URLs to scrape
            max_workers: Number of parallel workers

        Returns:
            List of scraped content dictionaries
        """
        results = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_url = {executor.submit(self.scrape_url, url): url for url in urls}

            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    result = future.result()
                    results.append(result)
                    if result["error"]:
                        print(f"✗ Failed to scrape {url}: {result['error']}")
                    else:
                        print(f"✓ Scraped {url}")
                except Exception as e:
                    print(f"✗ Exception scraping {url}: {e}")
                    results.append({
                        "url": url,
                        "title": None,
                        "text_content": None,
                        "meta_description": None,
                        "error": str(e)
                    })

        return results


class PropertyVerifier:
    """Uses AI to verify if candidate listings match the original property."""

    def __init__(self, model_provider="openai", model_name="gpt-4o-mini", api_key=None):
        """
        Initialize the verifier with LLM.

        Args:
            model_provider: "openai" or "anthropic"
            model_name: Model to use (default: "gpt-4o-mini" - optimal cost/quality balance)
            api_key: API key

        Note:
            GPT-4o-mini is the default model due to its excellent cost-effectiveness:
            - $0.003 per search (99.4% profit margin at $0.49/search)
            - Better quality than GPT-3.5-turbo
            - Fast response times (1-2 seconds)
        """
        if model_provider == "openai":
            self.llm = ChatOpenAI(
                model=model_name,
                api_key=api_key or os.getenv("OPENAI_API_KEY"),
                temperature=0
            )
        elif model_provider == "anthropic":
            self.llm = ChatAnthropic(
                model=model_name,
                api_key=api_key or os.getenv("ANTHROPIC_API_KEY"),
                temperature=0
            )
        else:
            raise ValueError(f"Unsupported model provider: {model_provider}")

    def verify_match(self, original_property: Dict, candidate_content: Dict) -> Dict:
        """
        Verify if candidate listing matches the original property.

        Args:
            original_property: Enhanced property details from AI extractor
            candidate_content: Scraped content from candidate URL

        Returns:
            Dictionary with verification results
        """
        # Skip if scraping failed
        if candidate_content.get("error"):
            return {
                "url": candidate_content["url"],
                "is_match": False,
                "confidence": 0.0,
                "reason": f"Failed to scrape: {candidate_content['error']}",
                "match_details": None
            }

        prompt_template = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at comparing vacation rental property listings to determine if they represent the same physical property.

Analyze the original property details and the candidate listing content to determine if they are THE SAME property.

Return a JSON object with:
- is_match: boolean (true if same property, false otherwise)
- confidence: float 0-1 (how confident you are)
- reason: string (brief explanation of your decision)
- matching_features: list of features that match (if is_match is true)
- contradictions: list of contradictions (if is_match is false)

Be strict: only return is_match=true if you're highly confident they're the same property.
Key indicators: location, property type, bedrooms/bathrooms, unique amenities, photos/descriptions.

Return ONLY valid JSON, no additional text."""),
            ("user", """ORIGINAL PROPERTY:
Title: {original_title}
Description: {original_description}
Location: {original_location}
Property Type: {property_type}
Bedrooms: {bedrooms}
Bathrooms: {bathrooms}
Amenities: {amenities}
Unique Features: {unique_features}

CANDIDATE LISTING:
URL: {candidate_url}
Title: {candidate_title}
Meta Description: {candidate_meta}
Content Preview: {candidate_content}

Is this the same property?""")
        ])

        ai_data = original_property.get("ai_extracted", {}) or {}

        chain = prompt_template | self.llm | StrOutputParser()

        response = chain.invoke({
            "original_title": original_property.get("title", ""),
            "original_description": original_property.get("description_snippet", ""),
            "original_location": original_property.get("location_text", ""),
            "property_type": ai_data.get("property_type", "not specified"),
            "bedrooms": ai_data.get("bedrooms", "not specified"),
            "bathrooms": ai_data.get("bathrooms", "not specified"),
            "amenities": ", ".join(ai_data.get("key_amenities", [])) if ai_data.get("key_amenities") else "not specified",
            "unique_features": ", ".join(ai_data.get("unique_features", [])) if ai_data.get("unique_features") else "not specified",
            "candidate_url": candidate_content["url"],
            "candidate_title": candidate_content.get("title", ""),
            "candidate_meta": candidate_content.get("meta_description", ""),
            "candidate_content": candidate_content.get("text_content", "")[:3000]  # Limit for context
        })

        try:
            verification_result = json.loads(response)
            return {
                "url": candidate_content["url"],
                **verification_result
            }
        except json.JSONDecodeError as e:
            print(f"Error parsing verification response: {e}")
            return {
                "url": candidate_content["url"],
                "is_match": False,
                "confidence": 0.0,
                "reason": f"AI response parsing error: {str(e)}",
                "match_details": None
            }

    def verify_multiple(self, original_property: Dict, candidate_contents: List[Dict]) -> List[Dict]:
        """
        Verify multiple candidates against original property.

        Args:
            original_property: Enhanced property details
            candidate_contents: List of scraped candidate contents

        Returns:
            List of verification results
        """
        print(f"\n=== Verification Phase ===")
        print(f"Verifying {len(candidate_contents)} candidates against original property...")

        results = []
        for i, candidate in enumerate(candidate_contents, 1):
            print(f"Verifying {i}/{len(candidate_contents)}: {candidate['url']}")
            result = self.verify_match(original_property, candidate)
            results.append(result)

            if result["is_match"]:
                print(f"  ✓ MATCH (confidence: {result['confidence']:.2f})")
            else:
                print(f"  ✗ Not a match: {result['reason'][:60]}...")

        matches = [r for r in results if r["is_match"]]
        print(f"\nFound {len(matches)} verified matches out of {len(candidate_contents)} candidates")

        return results


class PriceExtractor:
    """Uses AI to extract pricing information from verified listings."""

    def __init__(self, model_provider="openai", model_name="gpt-4o-mini", api_key=None):
        """
        Initialize the price extractor with LLM.

        Args:
            model_provider: "openai" or "anthropic"
            model_name: Model to use (default: "gpt-4o-mini" - optimal cost/quality balance)
            api_key: API key

        Note:
            GPT-4o-mini is the default model due to its excellent cost-effectiveness:
            - $0.003 per search (99.4% profit margin at $0.49/search)
            - Better quality than GPT-3.5-turbo
            - Fast response times (1-2 seconds)
        """
        if model_provider == "openai":
            self.llm = ChatOpenAI(
                model=model_name,
                api_key=api_key or os.getenv("OPENAI_API_KEY"),
                temperature=0
            )
        elif model_provider == "anthropic":
            self.llm = ChatAnthropic(
                model=model_name,
                api_key=api_key or os.getenv("ANTHROPIC_API_KEY"),
                temperature=0
            )

    def extract_price(self, scraped_content: Dict, check_in: str = None, check_out: str = None) -> Dict:
        """
        Extract pricing information from scraped content.

        Args:
            scraped_content: Scraped content dictionary
            check_in: Check-in date (YYYY-MM-DD)
            check_out: Check-out date (YYYY-MM-DD)

        Returns:
            Dictionary with pricing information
        """
        if scraped_content.get("error"):
            return {
                "url": scraped_content["url"],
                "price_found": False,
                "error": scraped_content["error"]
            }

        prompt_template = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at extracting pricing information from vacation rental listings.

Analyze the webpage content and extract pricing information.

Return a JSON object with:
- price_found: boolean (true if pricing info was found)
- nightly_rate: float or null (price per night if found)
- total_price: float or null (total price for the stay if specified)
- currency: string (e.g., "USD", "EUR") or null
- cleaning_fee: float or null
- service_fee: float or null
- price_notes: string (any important pricing notes, restrictions, or context)

If check-in/check-out dates are provided, try to find pricing for that specific period.
If no pricing is found, set price_found to false.

Return ONLY valid JSON, no additional text."""),
            ("user", """Extract pricing from this listing:

URL: {url}
Title: {title}
Check-in: {check_in}
Check-out: {check_out}

Content:
{content}

Extract all available pricing information.""")
        ])

        chain = prompt_template | self.llm | StrOutputParser()

        response = chain.invoke({
            "url": scraped_content["url"],
            "title": scraped_content.get("title", ""),
            "check_in": check_in or "not specified",
            "check_out": check_out or "not specified",
            "content": scraped_content.get("text_content", "")[:5000]
        })

        try:
            price_data = json.loads(response)
            return {
                "url": scraped_content["url"],
                **price_data
            }
        except json.JSONDecodeError as e:
            print(f"Error parsing price extraction: {e}")
            return {
                "url": scraped_content["url"],
                "price_found": False,
                "error": f"Parsing error: {str(e)}"
            }

    def extract_multiple_prices(self, scraped_contents: List[Dict],
                                check_in: str = None, check_out: str = None) -> List[Dict]:
        """
        Extract prices from multiple listings.

        Args:
            scraped_contents: List of scraped content dictionaries
            check_in: Check-in date
            check_out: Check-out date

        Returns:
            List of price extraction results
        """
        print(f"\n=== Price Extraction Phase ===")
        print(f"Extracting prices from {len(scraped_contents)} listings...")

        results = []
        for i, content in enumerate(scraped_contents, 1):
            print(f"Extracting price {i}/{len(scraped_contents)}: {content['url']}")
            result = self.extract_price(content, check_in, check_out)
            results.append(result)

            if result.get("price_found"):
                price = result.get("nightly_rate") or result.get("total_price")
                currency = result.get("currency", "")
                print(f"  ✓ Price found: {currency} {price}")
            else:
                print(f"  ✗ No price found")

        return results
