from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re

class GoogleImageSearch:
    def __init__(self):
        # Initialize the WebDriver (e.g., Chrome WebDriver)
        self.driver = webdriver.Chrome()

    def search_by_image(self, image_url):
        # Print the image URL first
        print("Image URL:", image_url)

        # Navigate to Google Images
        self.driver.get("https://images.google.com")

        # Find and click on the "Search by image" button using aria-label
        search_by_image_button = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//*[@aria-label='Search by image']"))
        )
        search_by_image_button.click()

        # Find the input field for pasting the image URL and paste the image URL
        url_input = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "cB9M7"))
        )
        url_input.send_keys(image_url)
        url_input.send_keys(Keys.ENTER)

        # Wait for the "See exact matches" link and click on it
        see_exact_matches = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[text()='See exact matches']"))
        )
        see_exact_matches.click()

        # Wait for the results list to load and locate the <ul> with aria-label="All results list"
        results_list = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//ul[@aria-label='All results list']"))
        )

        # Extract all <li> elements within the list and their links
        list_items = results_list.find_elements(By.XPATH, ".//li//a[@href]")
        result_links = [item.get_attribute('href') for item in list_items]

        # Print all extracted links
        print("\nExtracted Results:")
        for link in result_links:
            print(link)

        # Filter out any URLs containing "airbnb"
        filtered_links = [link for link in result_links if "airbnb" not in link]

        # Print all filtered links
        print("\nFiltered Results:")
        for link in filtered_links:
            print(link)

        # Close the browser
        self.driver.quit()


class AirbnbImageScraper:
    def __init__(self):
        # Initialize the WebDriver (e.g., Chrome WebDriver)
        self.driver = webdriver.Chrome()

    @staticmethod
    def trim_airbnb_url(airbnb_url):
        # Use regex to match and retain only the part of the URL up to check_in and check_out parameters
        trimmed_url = re.sub(r"(&source_impression_id=.*)?$", "", airbnb_url)
        return trimmed_url

    def fetch_first_image_link(self, airbnb_url):
        # Trim the Airbnb URL
        airbnb_url = self.trim_airbnb_url(airbnb_url)

        # Open the Airbnb listing page
        self.driver.get(airbnb_url)

        # Ensure the page loads fully
        self.driver.implicitly_wait(5)

        # Scroll down to load dynamic content
        self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.END)
        self.driver.implicitly_wait(2)

        # Locate images by their 'img' tags containing 'src' with Airbnb's image URL pattern
        image_elements = self.driver.find_elements(By.XPATH, "//img[contains(@src, 'https://a0.muscache.com/im/pictures')]")

        # Extract the first image URL
        first_image_url = image_elements[0].get_attribute('src') if image_elements else None

        # Close the Airbnb browser instance
        self.driver.quit()

        return first_image_url


# Example Usage
if __name__ == "__main__":
    # Prompt the user for the Airbnb URL
    airbnb_url = input("Enter the Airbnb listing URL: ")

    # Fetch the first image URL from the Airbnb listing
    airbnb_scraper = AirbnbImageScraper()
    first_image_url = airbnb_scraper.fetch_first_image_link(airbnb_url)

    if first_image_url:
        # Perform a Google Image Search for the extracted URL
        google_search = GoogleImageSearch()
        google_search.search_by_image(first_image_url)
    else:
        print("No image URL found.")
