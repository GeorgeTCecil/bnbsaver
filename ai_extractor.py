"""
AI-Powered Property Detail Extractor
Extracts structured property information from Airbnb listings using LLM.
"""
import os
import json
from typing import Dict, Optional
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


class PropertyDetailExtractor:
    """Uses AI to extract structured property details from scraped Airbnb data."""

    def __init__(self, model_provider="openai", model_name="gpt-4o-mini", api_key=None):
        """
        Initialize the extractor with a specific LLM.

        Args:
            model_provider: "openai" or "anthropic"
            model_name: Model to use (default: "gpt-4o-mini" - optimal cost/quality balance)
            api_key: API key (defaults to env variables)

        Note:
            GPT-4o-mini is the default model due to its excellent cost-effectiveness:
            - $0.003 per search (99.4% profit margin at $0.49/search)
            - Better quality than GPT-3.5-turbo
            - Fast response times (1-2 seconds)
        """
        self.model_provider = model_provider

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

    def extract_property_details(self, listing_details: Dict) -> Dict:
        """
        Extract enhanced property details using AI.

        Args:
            listing_details: Dictionary from SmartAirbnbScraper.get_listing_details()

        Returns:
            Enhanced property details with AI-extracted information
        """
        # Build the prompt with available data
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at extracting structured property information from vacation rental listings.
Your task is to analyze the provided listing information and extract key details that would help identify this same property on other rental websites.

Extract and return a JSON object with the following fields:
- property_type: Type of property (apartment, house, villa, condo, etc.)
- bedrooms: Number of bedrooms (integer or null)
- bathrooms: Number of bathrooms (float or null)
- max_guests: Maximum number of guests (integer or null)
- key_amenities: List of notable amenities mentioned (pool, hot tub, ocean view, etc.)
- location_details: Specific location details (neighborhood, landmarks, street name if available)
- unique_features: List of unique/distinctive features that would help identify this property
- search_keywords: List of 5-10 keywords that would be effective for finding this property

Be thorough but only include information that is clearly stated or strongly implied. If something is not mentioned, use null.
Return ONLY valid JSON, no additional text."""),
            ("user", """Analyze this Airbnb listing:

Title: {title}
Description: {description}
Location: {location}
Check-in: {check_in}
Check-out: {check_out}
Guests: {guests}
URL: {url}

Extract the property details as specified.""")
        ])

        # Prepare the data for the prompt
        chain = prompt_template | self.llm | StrOutputParser()

        response = chain.invoke({
            "title": listing_details.get("title", "Not available"),
            "description": listing_details.get("description_snippet", "Not available"),
            "location": listing_details.get("location_text", "Not available"),
            "check_in": listing_details.get("check_in", "Not specified"),
            "check_out": listing_details.get("check_out", "Not specified"),
            "guests": listing_details.get("total_guests", "Not specified"),
            "url": listing_details.get("trimmed_url", "")
        })

        try:
            # Parse the JSON response
            extracted_data = json.loads(response)

            # Merge with original listing details
            enhanced_details = {
                **listing_details,
                "ai_extracted": extracted_data
            }

            return enhanced_details

        except json.JSONDecodeError as e:
            print(f"Error parsing AI response: {e}")
            print(f"Raw response: {response}")

            # Return original details with error
            return {
                **listing_details,
                "ai_extracted": None,
                "ai_extraction_error": str(e)
            }


class SearchQueryGenerator:
    """Generates optimized search queries for finding the same property on other sites."""

    def __init__(self, model_provider="openai", model_name="gpt-4o-mini", api_key=None):
        """
        Initialize the query generator with a specific LLM.

        Args:
            model_provider: "openai" or "anthropic"
            model_name: Model to use (default: "gpt-4o-mini" - optimal cost/quality balance)
            api_key: API key (defaults to env variables)

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
                temperature=0.3  # Slight creativity for query variations
            )
        elif model_provider == "anthropic":
            self.llm = ChatAnthropic(
                model=model_name,
                api_key=api_key or os.getenv("ANTHROPIC_API_KEY"),
                temperature=0.3
            )
        else:
            raise ValueError(f"Unsupported model provider: {model_provider}")

    def generate_search_queries(self, property_details: Dict, num_queries: int = 8) -> list:
        """
        Generate multiple search query variations for finding this property.

        Args:
            property_details: Enhanced property details with AI extraction
            num_queries: Number of search queries to generate

        Returns:
            List of search query strings
        """
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", f"""You are an expert at creating effective web search queries for finding vacation rental properties.

Your task is to generate {num_queries} diverse and effective search queries that would help find this exact property on other vacation rental websites (VRBO, Booking.com, personal websites, etc.).

Guidelines:
- Include location-specific terms (neighborhood, city, landmarks)
- Use property-specific features (bedrooms, amenities, views)
- Vary the query structure (some short, some detailed)
- Include terms like "vacation rental", "short term rental", "holiday home"
- Exclude "airbnb" from queries to find alternative listings
- Focus on unique/distinctive features that identify this specific property

Return ONLY a JSON array of search query strings, no additional text.
Example: ["query 1", "query 2", "query 3"]"""),
            ("user", """Generate search queries for this property:

Title: {title}
Description: {description}
Location: {location}
Property Type: {property_type}
Bedrooms: {bedrooms}
Key Amenities: {amenities}
Unique Features: {unique_features}

Generate {num_queries} effective search queries.""")
        ])

        ai_data = property_details.get("ai_extracted", {}) or {}

        chain = prompt_template | self.llm | StrOutputParser()

        response = chain.invoke({
            "title": property_details.get("title", ""),
            "description": property_details.get("description_snippet", ""),
            "location": property_details.get("location_text", ""),
            "property_type": ai_data.get("property_type", "rental property"),
            "bedrooms": ai_data.get("bedrooms", "not specified"),
            "amenities": ", ".join(ai_data.get("key_amenities", [])) if ai_data.get("key_amenities") else "not specified",
            "unique_features": ", ".join(ai_data.get("unique_features", [])) if ai_data.get("unique_features") else "not specified",
            "num_queries": num_queries
        })

        try:
            queries = json.loads(response)

            # Add some standard fallback queries
            standard_queries = []
            if property_details.get("location_text"):
                location = property_details["location_text"]
                standard_queries.append(f"{location} vacation rental -airbnb")

                if ai_data.get("property_type"):
                    prop_type = ai_data["property_type"]
                    standard_queries.append(f"{location} {prop_type} short term rental")

            # Combine AI-generated and standard queries, remove duplicates
            all_queries = list(dict.fromkeys(queries + standard_queries))

            return all_queries[:num_queries]  # Limit to requested number

        except json.JSONDecodeError as e:
            print(f"Error parsing AI query response: {e}")
            print(f"Raw response: {response}")

            # Return basic fallback queries
            fallback_queries = []
            if property_details.get("location_text"):
                location = property_details["location_text"]
                fallback_queries = [
                    f"{location} vacation rental",
                    f"{location} short term rental -airbnb",
                    f"{location} holiday home",
                ]

            return fallback_queries


# Convenience function for quick usage
def extract_and_generate_queries(airbnb_url: str, scraper, model_provider="openai", model_name="gpt-4o-mini"):
    """
    Full pipeline: scrape Airbnb, extract details, generate queries.

    Args:
        airbnb_url: Airbnb listing URL
        scraper: Instance of SmartAirbnbScraper
        model_provider: "openai" or "anthropic"
        model_name: Model to use (default: "gpt-4o-mini" for optimal cost/quality)

    Returns:
        Tuple of (enhanced_property_details, search_queries)
    """
    # Scrape the listing
    listing_details = scraper.get_listing_details(airbnb_url)

    # Extract enhanced details with AI
    extractor = PropertyDetailExtractor(model_provider, model_name)
    enhanced_details = extractor.extract_property_details(listing_details)

    # Generate search queries
    query_generator = SearchQueryGenerator(model_provider, model_name)
    search_queries = query_generator.generate_search_queries(enhanced_details)

    return enhanced_details, search_queries
