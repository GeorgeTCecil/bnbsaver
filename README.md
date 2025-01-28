# BnbSaver

## Overview
**BnbSaver** is a Python and Flask web application designed to help users discover better deals on short-term rentals. By inputting an Airbnb listing URL, the app uses **Selenium** to perform a reverse image search, identifying other platforms hosting the same listing. This approach helps users find listings without Airbnb's service fees, potentially saving money.

---

## Features
- **Input Airbnb URL**: Enter the URL of an Airbnb listing.
- **Web Scraping with Selenium**: Automates browsing to retrieve listing details.
- **Reverse Image Search**: Locates the same property on other rental websites.
- **Filtered Results**: Excludes common sales-related platforms like "zillow," "realtor," and "rent.com."
- **User-Friendly Interface**: A homepage with a search bar and a results page displaying links.

---

## Future Plans
- **React Frontend**: Replace the Flask templates with a modern React.js frontend.
- **Additional Filters**: Provide advanced options to refine search results further.
- **Price Comparison**: Show estimated savings between platforms.
- **Save Listings**: Allow users to save and compare their favorite listings.
- **Increase Performance**: Optimize performance, potentially through an API for the google search portion.
- **Mobile Responsiveness**: Optimize for mobile and tablet devices.

---

## Usage
1. On the homepage, paste the Airbnb listing URL into the search bar.
2. Click "Search."
3. Review the results for links to other platforms hosting the same property.

---

## Screenshots
### Homepage
![Screenshot 2025-01-28 141141](https://github.com/user-attachments/assets/4b7433b0-696f-447c-8e32-46d24e59b97f)


### Results Page
![Screenshot 2025-01-28 141200](https://github.com/user-attachments/assets/d09ef80c-4d6d-447b-ae54-88ff361135f8)


---

## License
This project is licensed under the **Mozilla Public License 2.0**. You are welcome to view and contribute to the code. However, any modifications to the source code must remain open and shared under the same license.

Please fork this repository to experiment with or improve the code, and submit pull requests for contributions.
