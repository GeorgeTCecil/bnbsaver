"""
AI Image Matcher
Uses GPT-4 Vision to compare property images and verify if websites show the same property.

This is critical for owner website verification - properties often have different names
on different platforms, so visual matching is the most reliable verification method.
"""

import os
import base64
import requests
from typing import List, Dict, Optional
from openai import OpenAI
from dotenv import load_dotenv
from io import BytesIO
from PIL import Image

load_dotenv()


class PropertyImageMatcher:
    """
    Uses AI vision models to compare property images and determine if they're the same property.

    Approach:
    1. Download images from both Airbnb and candidate website
    2. Use GPT-4 Vision to analyze unique features
    3. Calculate similarity score (0-100%)
    4. Return confidence that it's the same property
    """

    def __init__(self, openai_api_key: Optional[str] = None, model: str = "gpt-4o"):
        """
        Initialize the image matcher.

        Args:
            openai_api_key: OpenAI API key (defaults to env var)
            model: Vision model to use (gpt-4o has vision capabilities and is cheaper than gpt-4-vision-preview)
        """
        self.api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")

        self.client = OpenAI(api_key=self.api_key)
        self.model = model

    def download_image(self, url: str, max_size_mb: int = 5) -> Optional[bytes]:
        """
        Download an image from URL with size limits.

        Args:
            url: Image URL
            max_size_mb: Maximum image size in MB

        Returns:
            Image bytes or None if download fails
        """
        try:
            response = requests.get(url, timeout=10, stream=True)
            response.raise_for_status()

            # Check size
            content_length = response.headers.get('content-length')
            if content_length and int(content_length) > max_size_mb * 1024 * 1024:
                print(f"Image too large: {int(content_length) / 1024 / 1024:.1f}MB")
                return None

            # Download
            image_data = response.content

            # Verify it's a valid image
            try:
                Image.open(BytesIO(image_data))
            except:
                print(f"Invalid image format from {url}")
                return None

            return image_data

        except Exception as e:
            print(f"Error downloading image from {url}: {e}")
            return None

    def encode_image_base64(self, image_bytes: bytes) -> str:
        """
        Encode image bytes to base64 string for API.

        Args:
            image_bytes: Image data

        Returns:
            Base64 encoded string
        """
        return base64.b64encode(image_bytes).decode('utf-8')

    def compare_images(
        self,
        airbnb_image_url: str,
        candidate_image_url: str
    ) -> Dict:
        """
        Compare two property images using AI vision.

        Args:
            airbnb_image_url: URL of Airbnb listing image
            candidate_image_url: URL of candidate website image

        Returns:
            Dict with:
            {
                'match': bool,  # True if same property
                'confidence': float,  # 0-100% confidence
                'reasoning': str,  # AI explanation
                'features_matched': List[str],  # Unique features that matched
                'features_different': List[str]  # Features that didn't match
            }
        """
        # Download both images
        print(f"Downloading Airbnb image: {airbnb_image_url}")
        airbnb_img = self.download_image(airbnb_image_url)
        if not airbnb_img:
            return self._error_result("Failed to download Airbnb image")

        print(f"Downloading candidate image: {candidate_image_url}")
        candidate_img = self.download_image(candidate_image_url)
        if not candidate_img:
            return self._error_result("Failed to download candidate image")

        # Encode to base64
        airbnb_b64 = self.encode_image_base64(airbnb_img)
        candidate_b64 = self.encode_image_base64(candidate_img)

        # Create prompt for AI
        prompt = """Compare these two property images and determine if they show the SAME vacation rental property.

Look for unique identifying features:
- Architectural details (windows, doors, roof, balconies)
- Interior layout and design elements
- Pool or outdoor features (shape, tile pattern, landscaping)
- Ocean/mountain views from specific angles
- Unique furniture or decor
- Distinctive amenities (hot tub, fireplace, kitchen island)

Respond in JSON format:
{
    "is_same_property": true/false,
    "confidence_percentage": 0-100,
    "reasoning": "Detailed explanation of why you think it is or isn't the same property",
    "features_matched": ["feature1", "feature2", ...],
    "features_different": ["difference1", "difference2", ...]
}

Be conservative - only say it's the same property if you're 80%+ confident.
Different photos of the same property should still show consistent unique features."""

        try:
            # Call GPT-4 Vision API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{airbnb_b64}",
                                    "detail": "high"
                                }
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{candidate_b64}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500,
                temperature=0.1  # Low temperature for consistent results
            )

            # Parse response
            result_text = response.choices[0].message.content

            # Extract JSON from response (it might have markdown code blocks)
            import json
            import re

            # Try to find JSON in the response
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                result_json = json.loads(json_match.group())
            else:
                # Fallback parsing
                result_json = json.loads(result_text)

            return {
                'match': result_json.get('is_same_property', False),
                'confidence': result_json.get('confidence_percentage', 0),
                'reasoning': result_json.get('reasoning', ''),
                'features_matched': result_json.get('features_matched', []),
                'features_different': result_json.get('features_different', []),
                'raw_response': result_text
            }

        except Exception as e:
            print(f"Error calling vision API: {e}")
            return self._error_result(f"API error: {str(e)}")

    def compare_multiple_images(
        self,
        airbnb_image_urls: List[str],
        candidate_image_urls: List[str],
        min_confidence: float = 80.0
    ) -> Dict:
        """
        Compare multiple images from Airbnb vs candidate site.

        More reliable than single image comparison - checks if MOST images match.

        Args:
            airbnb_image_urls: List of Airbnb image URLs
            candidate_image_urls: List of candidate site image URLs
            min_confidence: Minimum confidence to consider a match

        Returns:
            Dict with overall match result
        """
        comparisons = []
        match_count = 0

        # Compare each Airbnb image with each candidate image
        # But limit to avoid too many API calls (expensive)
        max_comparisons = 6  # e.g., 3 Airbnb images × 2 candidate images

        comparison_count = 0
        for airbnb_url in airbnb_image_urls[:3]:  # First 3 Airbnb images
            for candidate_url in candidate_image_urls[:2]:  # First 2 candidate images
                if comparison_count >= max_comparisons:
                    break

                result = self.compare_images(airbnb_url, candidate_url)
                comparisons.append(result)
                comparison_count += 1

                if result['match'] and result['confidence'] >= min_confidence:
                    match_count += 1

            if comparison_count >= max_comparisons:
                break

        # Overall verdict: If majority of comparisons match, it's the same property
        total_comparisons = len(comparisons)
        match_ratio = match_count / total_comparisons if total_comparisons > 0 else 0

        avg_confidence = sum(c['confidence'] for c in comparisons) / total_comparisons if total_comparisons > 0 else 0

        return {
            'match': match_ratio >= 0.5,  # Majority vote
            'confidence': avg_confidence,
            'match_ratio': match_ratio,
            'comparisons': comparisons,
            'summary': f"{match_count}/{total_comparisons} images matched"
        }

    def _error_result(self, error_msg: str) -> Dict:
        """Return error result dict."""
        return {
            'match': False,
            'confidence': 0,
            'reasoning': error_msg,
            'features_matched': [],
            'features_different': [],
            'error': True
        }


def test_image_matcher():
    """Test the image matcher with sample images."""
    matcher = PropertyImageMatcher()

    # These would be real URLs in production
    # For testing, you'd need actual property images
    print("=" * 60)
    print("Testing AI Image Matcher")
    print("=" * 60)

    # Example usage (commented out - needs real URLs)
    """
    airbnb_img = "https://example.com/airbnb-property.jpg"
    candidate_img = "https://example.com/owner-site-property.jpg"

    result = matcher.compare_images(airbnb_img, candidate_img)

    print(f"\nMatch: {result['match']}")
    print(f"Confidence: {result['confidence']}%")
    print(f"Reasoning: {result['reasoning']}")
    print(f"\nFeatures Matched: {', '.join(result['features_matched'])}")
    print(f"Features Different: {', '.join(result['features_different'])}")
    """

    print("\nImage matcher initialized successfully!")
    print("Ready to compare property images.")
    print("\nCost estimate: ~$0.01 per image comparison (GPT-4o with vision)")


if __name__ == "__main__":
    test_image_matcher()
