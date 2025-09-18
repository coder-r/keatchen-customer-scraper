# KEATchen Customer Scraper API Documentation

## Class: KEATchenCustomerScraper

Main class for scraping customer data from the KEATchen admin panel.

### Constructor

```python
KEATchenCustomerScraper(base_url: str = "https://keatchenunited.app4food.co.uk")
```

**Parameters:**
- `base_url`: Base URL of the KEATchen admin panel

### Methods

#### `load_existing_data()`
Loads existing customer data from JSON file to avoid duplicates.

#### `save_data()`
Saves scraped data to both JSON and CSV formats with timestamp.

#### `login(page: Page) -> bool`
Logs into the admin panel using stored credentials.

**Parameters:**
- `page`: Playwright page object

**Returns:**
- `bool`: True if login successful, False otherwise

#### `extract_customer_basic_info(row_element) -> Optional[Dict]`
Extracts basic customer information from table row.

**Parameters:**
- `row_element`: Playwright element representing table row

**Returns:**
- `Dict`: Customer basic info or None if extraction fails

#### `extract_customer_details(page: Page, customer: Dict) -> Dict`
Extracts detailed customer information from details page.

**Parameters:**
- `page`: Playwright page object
- `customer`: Basic customer info dictionary

**Returns:**
- `Dict`: Enhanced customer info with all details

#### `scrape_current_page(page: Page) -> int`
Scrapes all customers on current page.

**Parameters:**
- `page`: Playwright page object

**Returns:**
- `int`: Number of customers scraped on current page

#### `scrape_all_customers()`
Main scraping function that handles all pages and pagination.

## Data Structure

### Customer Record Format

```json
{
  "first_name": "string",
  "last_name": "string",
  "email": "string",
  "mobile": "string",
  "address": "string", 
  "postcode": "string",
  "contact_details": {
    "raw_text": "string"
  },
  "roles": ["string"],
  "loyalty": {
    "raw_text": "string"
  },
  "coupons": ["string"],
  "orders": [
    {
      "order_id": "string",
      "date": "string", 
      "total": "string"
    }
  ],
  "delivery": {
    "raw_text": "string"
  },
  "discounts": ["string"],
  "scraped_at": "ISO timestamp"
}
```

## Configuration Variables

- `username`: Login username (default: "admin@keatchen")
- `password`: Login password (default: "keatchen22")
- `output_dir`: Output directory (default: "customer_data")

## Error Handling

The scraper includes robust error handling for:
- Login failures
- Network timeouts
- Missing page elements
- Data extraction errors
- File I/O errors

## Output Files

### customers.json
Complete customer database in JSON format, continuously updated.

### customers_YYYYMMDD_HHMMSS.csv
Timestamped CSV export with flattened data structure.

## Performance Considerations

- **Rate Limiting**: 1-second delay between customer details extraction
- **Memory Usage**: Data saved after each page to prevent memory issues
- **Resume Capability**: Can restart from any point without losing progress
- **Duplicate Prevention**: Checks existing data before scraping

## Browser Configuration

- **Default**: Non-headless mode for monitoring
- **Headless Mode**: Set `headless=True` in browser launch for background operation
- **Browser**: Uses Chromium for best compatibility

## Security Notes

- Credentials are stored in the script (consider environment variables)
- Admin panel access required
- Rate limiting implemented to be respectful to server
- No data transmission outside local environment