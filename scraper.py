from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
import time
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

class GoogleImageSearch:
    def __init__(self):
        # Set up Chrome options for headless mode
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode
        chrome_options.add_argument("--no-sandbox")  # Helps in certain environments like CI/CD
        chrome_options.add_argument("--disable-dev-shm-usage")  # Solve resource issue in Docker

        # Path to chromedriver
        chrome_driver_path = '/usr/bin/chromedriver'  # Correct path for chromedriver

        # Path to chromium binary
        chrome_path = '/snap/bin/chromium'  # Correct path for chromium binary installed via snap

        chrome_options.binary_location = chrome_path  # Set the path for Chromium binary

        # Initialize the WebDriver with the service and options
        service = Service(chrome_driver_path)
        self.driver = webdriver.Chrome(service=service, options=chrome_options)

    def search_by_image(self, image_url):
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

        # Wait for the "Find image source" button and click it
        try:
            # Look for the "Find image source" button based on the provided structure
            find_image_source_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'ICt2Q') and contains(text(), 'Find image source')]"))
            )
            find_image_source_button.click()

            # Wait for the results to load
            results_list = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//ul[@aria-label='All results list']"))
            )

            # Extract all <li> elements within the list and their links
            list_items = results_list.find_elements(By.XPATH, ".//li//a[@href]")
            result_links = [item.get_attribute('href') for item in list_items]

            # Filter out any URLs containing "airbnb" and "zillow"
            filtered_links = [link for link in result_links if "airbnb" not in link and "zillow" not in link]

            # Close the browser
            self.driver.quit()

            return filtered_links

        except Exception as e:
            print(f"Error: {e}")
            self.driver.quit()
            return []

class AirbnbImageScraper:
    def __init__(self):
        # Set up Chrome options for headless mode
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        # Path to chromedriver
        chrome_driver_path = '/usr/bin/chromedriver'  # Correct path for chromedriver

        # Path to chromium binary
        chrome_path = '/snap/bin/chromium'  # Correct path for chromium binary installed via snap

        chrome_options.binary_location = chrome_path  # Set the path for Chromium binary

        # Initialize the WebDriver with the service and options
        service = Service(chrome_driver_path)
        self.driver = webdriver.Chrome(service=service, options=chrome_options)

    @staticmethod
    def trim_airbnb_url(airbnb_url):
        trimmed_url = re.sub(r"(&source_impression_id=.*)?$", "", airbnb_url)
        return trimmed_url

    @staticmethod
    def extract_dates_and_guests(airbnb_url):
        dates_match = re.search(r"check_in=(\d{4}-\d{2}-\d{2}).*?check_out=(\d{4}-\d{2}-\d{2})", airbnb_url)
        adults_match = re.search(r"adults=(\d+)", airbnb_url)
        children_match = re.search(r"children=(\d+)", airbnb_url)

        check_in = dates_match.group(1) if dates_match else None
        check_out = dates_match.group(2) if dates_match else None
        adults = int(adults_match.group(1)) if adults_match else 0
        children = int(children_match.group(1)) if children_match else 0
        total_guests = adults + children

        return check_in, check_out, total_guests

    def fetch_first_image_link(self, airbnb_url):
        airbnb_url = self.trim_airbnb_url(airbnb_url)
        check_in, check_out, total_guests = self.extract_dates_and_guests(airbnb_url)

        self.driver.get(airbnb_url)
        self.driver.implicitly_wait(5)

        # Add more time before scraping the image URL to ensure images are loaded
        time.sleep(2) 

        try:
            # Find the meta tag with property og:image and get the content attribute
            og_image_element = self.driver.find_element(By.XPATH, "//meta[@property='og:image']")
            og_image_url = og_image_element.get_attribute('content')
        except:
            # If no og:image is found, fall back to scraping images in the page
            image_elements = self.driver.find_elements(By.XPATH, "//img[contains(@src, 'https://a0.muscache.com/im/pictures') or @id='FMP-target']")

            # Filter out the specific image URL
            filtered_image_urls = [
                img.get_attribute('src') for img in image_elements if img.get_attribute('src') != 'https://a0.muscache.com/im/pictures/7b5cf816-6c16-49f8-99e5-cbc4adfd97e2.jpg?im_w=320'
            ]

            # Get the first valid image URL, if available
            og_image_url = filtered_image_urls[0] if filtered_image_urls else None

        self.driver.quit()

        return og_image_url
