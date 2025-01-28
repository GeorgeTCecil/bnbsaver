from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
import re
import time

class GoogleImageSearch:
    def __init__(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless") 
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        self.driver = webdriver.Chrome(options=chrome_options)

    def search_by_image(self, image_url):
        try:
            # navigate to google images and perform a reverse image search
            self.driver.get("https://images.google.com")

            search_by_image_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//*[@aria-label='Search by image']"))
            )
            search_by_image_button.click()

            url_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "cB9M7"))
            )

            self.driver.execute_script("arguments[0].style.display = 'block';", url_input)

            url_input.send_keys(image_url)
            url_input.send_keys(Keys.ENTER)

            # locate and click on the "Exact matches" section
            exact_matches_link = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), 'Exact matches')]/ancestor::a"))
            )
            exact_matches_link.click()

            # wait for results to load
            rso_section = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//div[@data-async-context='query:' and @id='rso']"))
            )

            # extract and filter href links from the "rso" section
            result_links = rso_section.find_elements(By.XPATH, ".//a[@href]")
            links = [link.get_attribute("href") for link in result_links]

            # filter out via keywords to minimize links unrelated to short term rentals
            exclude_keywords = ['airbnb', 'zillow', 'realtor', 'rent.com', 'sale', 'realestate',
                'properties', 'property',  'househunters', 'invest', 'listings']

            filtered_links = [
                link for link in links if not any(keyword in link for keyword in exclude_keywords)
            ]

            return filtered_links

        except TimeoutException:
            print("Error: Timed out while waiting for an element to load.")
            return []
        except Exception as e:
            print(f"Error during search: {e}")
            return []
        finally:
            self.driver.quit()

        
class AirbnbImageScraper:
    def __init__(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        self.driver = webdriver.Chrome(options=chrome_options)

    @staticmethod
    def trim_airbnb_url(airbnb_url):
        trimmed_url = re.sub(r"(&source_impression_id=.*)?$", "", airbnb_url)
        return trimmed_url

    # extract dates and guest numbers.. this will be used in the future for more in depth price saving calculations 
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

    # fetch primary image link to use in reverse image search
    def fetch_first_image_link(self, airbnb_url):
        airbnb_url = self.trim_airbnb_url(airbnb_url)
        check_in, check_out, total_guests = self.extract_dates_and_guests(airbnb_url)

        self.driver.get(airbnb_url)
        self.driver.implicitly_wait(5)

        time.sleep(2) 

        try:
            # find the meta tag with property og:image and get the content attribute
            og_image_element = self.driver.find_element(By.XPATH, "//meta[@property='og:image']")
            og_image_url = og_image_element.get_attribute('content')
        except:
            # if no og:image is found, fall back to scraping images in the page
            image_elements = self.driver.find_elements(By.XPATH, "//img[contains(@src, 'https://a0.muscache.com/im/pictures') or @id='FMP-target']")

            # filter out the specific image URL of a map.. if others are found in future, filter them here. 
            filtered_image_urls = [
                img.get_attribute('src') for img in image_elements if img.get_attribute('src') != 'https://a0.muscache.com/im/pictures/7b5cf816-6c16-49f8-99e5-cbc4adfd97e2.jpg?im_w=320'
            ]

            # get the first valid image URL
            og_image_url = filtered_image_urls[0] if filtered_image_urls else None

        self.driver.quit()

        return og_image_url
