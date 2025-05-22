import unittest
from unittest.mock import patch, MagicMock
import os

# Import the class to be tested
from image_searchers import SerpApiGoogleImageSearch

class TestSerpApiGoogleImageSearch(unittest.TestCase):

    def setUp(self):
        # Set a dummy API key for most tests to pass the __init__ check
        self.dummy_api_key = "test_api_key_12345"
        # Store original env var if it exists
        self.original_env_api_key = os.environ.get("SERPAPI_API_KEY")
        os.environ["SERPAPI_API_KEY"] = self.dummy_api_key

    def tearDown(self):
        # Restore original env var
        if self.original_env_api_key is not None:
            os.environ["SERPAPI_API_KEY"] = self.original_env_api_key
        elif "SERPAPI_API_KEY" in os.environ:
            del os.environ["SERPAPI_API_KEY"]

    def test_initialization_with_env_variable(self):
        # Relies on setUp setting the env var
        searcher = SerpApiGoogleImageSearch()
        self.assertEqual(searcher.api_key, self.dummy_api_key)

    def test_initialization_with_argument(self):
        arg_api_key = "arg_key_67890"
        searcher = SerpApiGoogleImageSearch(api_key=arg_api_key)
        self.assertEqual(searcher.api_key, arg_api_key)

    def test_initialization_no_api_key_raises_error(self):
        if "SERPAPI_API_KEY" in os.environ: # Temporarily remove for this test
            del os.environ["SERPAPI_API_KEY"]
        with self.assertRaisesRegex(ValueError, "SerpApi API key not found"):
            SerpApiGoogleImageSearch()
        # Put it back for other tests if it was there (setUp will handle it on next run anyway)
        os.environ["SERPAPI_API_KEY"] = self.dummy_api_key


    # We need to mock 'serpapi.GoogleSearch' which is used inside the search_by_image method
    @patch('image_searchers.GoogleSearch') # Patch where it's LOOKED UP (in image_searchers.py)
    def test_search_by_image_success_with_target_domains(self, MockGoogleSearch):
        # --- Arrange ---
        # 1. Configure the mock for GoogleSearch instance and its get_dict() method
        mock_search_instance = MagicMock()
        mock_api_response = {
            "image_sources": [
                {"link": "https://www.vrbo.com/listing123", "source": "vrbo.com"},
                {"link": "https://www.booking.com/hotelABC", "source": "booking.com"},
                {"link": "https://www.someotherblog.com/image-featured", "source": "someotherblog.com"},
                {"link": "https://www.airbnb.com/rooms/original_room", "source": "airbnb.com"} # Should be filtered out if image_url is airbnb
            ]
        }
        mock_search_instance.get_dict.return_value = mock_api_response
        MockGoogleSearch.return_value = mock_search_instance # When GoogleSearch() is called, it returns our mock_search_instance

        # 2. Instantiate our class
        searcher = SerpApiGoogleImageSearch(api_key=self.dummy_api_key)
        test_image_url = "https://a0.muscache.com/im/pictures/miso/some_image.jpeg"
        target_domains = ["vrbo.com", "booking.com"]

        # --- Act ---
        results = searcher.search_by_image(test_image_url, target_domains=target_domains)

        # --- Assert ---
        # Check that GoogleSearch was called with the correct parameters
        MockGoogleSearch.assert_called_once_with({
            "engine": "google_reverse_image",
            "image_url": test_image_url,
            "api_key": self.dummy_api_key,
            "hl": "en",
            "gl": "us",
        })
        mock_search_instance.get_dict.assert_called_once() # Ensure get_dict was called

        self.assertIn("https://www.vrbo.com/listing123", results)
        self.assertIn("https://www.booking.com/hotelABC", results)
        self.assertNotIn("https://www.someotherblog.com/image-featured", results)
        # Airbnb link from image_sources should be filtered by target_domains
        self.assertNotIn("https://www.airbnb.com/rooms/original_room", results)
        self.assertEqual(len(results), 2)


    @patch('image_searchers.GoogleSearch')
    def test_search_by_image_success_no_target_domains(self, MockGoogleSearch):
        mock_search_instance = MagicMock()
        mock_api_response = {
            "image_sources": [
                {"link": "https://www.vrbo.com/listing123", "source": "vrbo.com"},
                {"link": "https://www.booking.com/hotelABC", "source": "booking.com"},
                {"link": "https://www.airbnb.com/rooms/original_room", "source": "airbnb.com"} # Should be filtered out by default
            ]
        }
        mock_search_instance.get_dict.return_value = mock_api_response
        MockGoogleSearch.return_value = mock_search_instance

        searcher = SerpApiGoogleImageSearch(api_key=self.dummy_api_key)
        test_image_url = "https://a0.muscache.com/im/pictures/miso/another_image.jpeg" # An airbnb image

        results = searcher.search_by_image(test_image_url) # No target domains

        expected_results = sorted([
            "https://www.vrbo.com/listing123",
            "https://www.booking.com/hotelABC"
        ]) # airbnb.com link should be filtered out by the generic filter
        self.assertEqual(results, expected_results)
        self.assertEqual(len(results), 2)


    @patch('image_searchers.GoogleSearch')
    def test_search_by_image_api_error(self, MockGoogleSearch):
        mock_search_instance = MagicMock()
        mock_api_response = {"error": "The API key is invalid."} # Simulate SerpApi error
        mock_search_instance.get_dict.return_value = mock_api_response
        MockGoogleSearch.return_value = mock_search_instance

        searcher = SerpApiGoogleImageSearch(api_key=self.dummy_api_key)
        results = searcher.search_by_image("http://example.com/image.jpg")

        self.assertEqual(results, []) # Expect empty list on error


    @patch('image_searchers.GoogleSearch')
    def test_search_by_image_no_relevant_results_in_image_sources(self, MockGoogleSearch):
        mock_search_instance = MagicMock()
        mock_api_response = {
            "image_sources": [ # Has sources, but none match target
                {"link": "https://www.randomsite.com/pic", "source": "randomsite.com"}
            ]
        }
        mock_search_instance.get_dict.return_value = mock_api_response
        MockGoogleSearch.return_value = mock_search_instance

        searcher = SerpApiGoogleImageSearch(api_key=self.dummy_api_key)
        results = searcher.search_by_image("http://example.com/image.jpg", target_domains=["vrbo.com"])

        self.assertEqual(results, [])


    @patch('image_searchers.GoogleSearch')
    def test_search_by_image_empty_response_from_api(self, MockGoogleSearch):
        mock_search_instance = MagicMock()
        mock_api_response = {} # Completely empty
        mock_search_instance.get_dict.return_value = mock_api_response
        MockGoogleSearch.return_value = mock_search_instance

        searcher = SerpApiGoogleImageSearch(api_key=self.dummy_api_key)
        results = searcher.search_by_image("http://example.com/image.jpg")
        self.assertEqual(results, [])

    @patch('image_searchers.GoogleSearch')
    def test_search_uses_image_results_if_image_sources_missing(self, MockGoogleSearch):
        mock_search_instance = MagicMock()
        # No 'image_sources', but has 'image_results'
        mock_api_response = {
            "image_results": [
                {"link": "https://www.vrbo.com/from_image_results", "source": "vrbo.com"},
                {"link": "https://www.other.com/other_img_res", "source": "other.com"},
            ]
        }
        mock_search_instance.get_dict.return_value = mock_api_response
        MockGoogleSearch.return_value = mock_search_instance

        searcher = SerpApiGoogleImageSearch(api_key=self.dummy_api_key)
        test_image_url = "https://some.non.airbnb.url/image.jpeg" # Non-Airbnb image URL
        results = searcher.search_by_image(test_image_url, target_domains=["vrbo.com"])
        
        self.assertIn("https://www.vrbo.com/from_image_results", results)
        self.assertNotIn("https://www.other.com/other_img_res", results) # Filtered by target_domains
        self.assertEqual(len(results), 1)


if __name__ == '__main__':
    unittest.main(verbosity=2)