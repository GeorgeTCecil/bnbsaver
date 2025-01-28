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
This project is licensed under the **GNU General Public License v3.0 (GPL-3.0)**.

You are free to:
- Use this code for any purpose.
- Modify the code and distribute your changes.
- Contribute to this project.

However:
- Any changes you make must also be distributed under the GPL-3.0 license.
- You cannot integrate this code or its derivatives into proprietary software.

For more details, see the [COPYING](./COPYING) file.

