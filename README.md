# KEATchen Customer Data Scraper

A comprehensive Python script to scrape all customer data from the KEATchen admin panel.

## Features

- ✅ **Complete Customer Data Extraction**:
  - Contact Details
  - Roles
  - Loyalty information
  - Coupons
  - Orders history
  - Delivery preferences
  - Discounts

- ✅ **Smart Duplicate Prevention**: Checks existing data to avoid re-scraping customers
- ✅ **Multi-page Pagination**: Handles all 27 pages (538+ customers)
- ✅ **Multiple Export Formats**: JSON and CSV output
- ✅ **Progress Tracking**: Saves after each page
- ✅ **Error Handling**: Robust error handling and recovery

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Install Playwright browsers:
```bash
playwright install chromium
```

## Usage

### Run the Complete Scraper
```bash
python customer_scraper.py
```

The script will:
1. Login to the admin panel automatically
2. Navigate through all 27 pages
3. Extract detailed information for each customer
4. Save progress after each page
5. Export final data to JSON and CSV

### Output Files

The script creates a `customer_data/` directory with:
- `customers.json` - Complete JSON data (continuously updated)
- `customers_YYYYMMDD_HHMMSS.csv` - Timestamped CSV export

### Key Features

**Duplicate Prevention**: The script loads existing data on startup and skips customers already scraped.

**Progress Saving**: Data is saved after each page, so if interrupted, you can restart without losing progress.

**Detailed Extraction**: For each customer, the script:
1. Clicks the "Details" button
2. Extracts all section data
3. Returns to the customer list
4. Continues to next customer

**Error Handling**: If a customer page fails to load or extract, the script continues with the next customer.

## Data Structure

Each customer record contains:
```json
{
  "first_name": "John",
  "last_name": "Smith", 
  "email": "john@example.com",
  "mobile": "+447123456789",
  "address": "123 Main St, City",
  "postcode": "AB1 2CD",
  "contact_details": {...},
  "roles": [...],
  "loyalty": {...},
  "coupons": [...],
  "orders": [...],
  "delivery": {...},
  "discounts": [...],
  "scraped_at": "2025-01-18T..."
}
```

## Configuration

Edit these variables in `customer_scraper.py` if needed:
- `base_url`: The admin panel URL
- `username`/`password`: Login credentials
- `headless`: Set to `True` to run without visible browser

## Monitoring Progress

The script provides detailed console output:
- Login status
- Page progress (X/27)
- Individual customer processing
- Save confirmations
- Final statistics

## Resume Capability

If the script is interrupted, simply run it again. It will:
1. Load existing customer data
2. Skip already scraped customers
3. Continue from where it left off

## Estimated Runtime

- ~538 customers across 27 pages
- ~2-3 seconds per customer (including detail extraction)
- **Total estimated time: 25-45 minutes**

## Troubleshooting

**Login Issues**: Verify credentials in the script
**Timeout Errors**: Increase wait times in the script
**Missing Data**: Check if the page structure has changed

## Security Note

This script contains login credentials. Keep the files secure and don't commit credentials to version control.