#!/usr/bin/env python3
"""
KEATchen Customer Data Scraper
Scrapes all customer data from the admin panel including:
- Contact Details
- Roles  
- Loyalty
- Coupons
- Orders
- Delivery
- Discounts
"""

import json
import csv
import time
import os
from datetime import datetime
from typing import Dict, List, Set, Optional
import requests
from playwright.sync_api import sync_playwright, Page, Browser
import pandas as pd

class KEATchenCustomerScraper:
    def __init__(self, base_url: str = "https://keatchenunited.app4food.co.uk"):
        self.base_url = base_url
        self.login_url = f"{base_url}/admin/Account/Login"
        self.customer_url = f"{base_url}/admin/Customer"
        
        # Credentials
        self.username = "admin@keatchen"
        self.password = "keatchen22"
        
        # Data storage
        self.customers_data = []
        self.scraped_emails: Set[str] = set()
        self.output_dir = "customer_data"
        
        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Load existing data if available
        self.load_existing_data()
        
        print(f"Scraper initialized. Found {len(self.scraped_emails)} existing customers.")
    
    def load_existing_data(self):
        """Load existing customer data to avoid duplicates"""
        try:
            if os.path.exists(f"{self.output_dir}/customers.json"):
                with open(f"{self.output_dir}/customers.json", 'r') as f:
                    self.customers_data = json.load(f)
                    self.scraped_emails = {customer.get('email', '').lower() for customer in self.customers_data}
                    print(f"Loaded {len(self.customers_data)} existing customers")
        except Exception as e:
            print(f"Error loading existing data: {e}")
    
    def save_data(self):
        """Save scraped data to JSON and CSV files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save to JSON
        json_file = f"{self.output_dir}/customers.json"
        with open(json_file, 'w') as f:
            json.dump(self.customers_data, f, indent=2)
        
        # Save to CSV
        csv_file = f"{self.output_dir}/customers_{timestamp}.csv"
        if self.customers_data:
            df = pd.json_normalize(self.customers_data)
            df.to_csv(csv_file, index=False)
            print(f"Data saved: {len(self.customers_data)} customers")
            print(f"JSON: {json_file}")
            print(f"CSV: {csv_file}")
    
    def login(self, page: Page) -> bool:
        """Login to the admin panel"""
        try:
            print("Logging in...")
            page.goto(self.login_url)
            page.wait_for_load_state('networkidle')
            
            # Enter credentials  
            email_field = page.query_selector('input[placeholder*="email"], input[type="email"], input[name*="email"]')
            if email_field:
                email_field.fill(self.username)
            else:
                # Try alternative selector
                page.fill('input:nth-of-type(1)', self.username)
            
            password_field = page.query_selector('input[type="password"]')
            if password_field:
                password_field.fill(self.password)
            
            # Click login
            page.click('button:has-text("Log In")')
            page.wait_for_load_state('networkidle')
            
            # Check if login successful - look for logout link or admin dashboard
            current_url = page.url
            print(f"Current URL after login: {current_url}")
            
            if "admin/" in current_url and page.query_selector('a:has-text("Logout")'):
                print("✅ Login successful!")
                return True
            else:
                print("❌ Login failed - checking page content...")
                print(f"Page title: {page.title()}")
                return False
                
        except Exception as e:
            print(f"❌ Login error: {e}")
            return False
    
    def verify_customer_page(self, page: Page) -> bool:
        """Verify we're on the correct customer page"""
        try:
            current_url = page.url
            page_title = page.title()
            
            print(f"Verifying customer page...")
            print(f"Current URL: {current_url}")
            print(f"Page title: {page_title}")
            
            # Check URL contains Customer
            if "/admin/Customer" not in current_url:
                print("❌ Not on customer page - URL check failed")
                return False
            
            # Check for customer table
            table = page.query_selector('table')
            if not table:
                print("❌ Customer table not found")
                return False
            
            # Check for customer data in table
            customer_rows = page.query_selector_all('tbody tr')
            if len(customer_rows) < 2:  # Should have at least header + one customer
                print("❌ No customer data found in table")
                return False
            
            # Check for pagination info
            pagination = page.query_selector('text*="of 538"')
            if pagination:
                print("✅ Pagination found - confirmed customer page")
                return True
            
            print("✅ Customer page verified")
            return True
            
        except Exception as e:
            print(f"❌ Error verifying customer page: {e}")
            return False
    
    def extract_customer_basic_info(self, row_element) -> Optional[Dict]:
        """Extract basic customer info from table row"""
        try:
            cells = row_element.query_selector_all('td')
            if len(cells) < 6:
                return None
                
            # Skip pagination rows
            row_text = row_element.inner_text()
            if "of 27" in row_text or "Firstname" in row_text:
                return None
                
            customer = {
                'first_name': cells[0].inner_text().strip(),
                'last_name': cells[1].inner_text().strip(),
                'email': cells[2].inner_text().strip(),
                'mobile': cells[3].inner_text().strip(),
                'address': cells[4].inner_text().strip(),
                'postcode': cells[5].inner_text().strip(),
                'scraped_at': datetime.now().isoformat()
            }
            
            return customer
            
        except Exception as e:
            print(f"Error extracting basic info: {e}")
            return None
    
    def extract_customer_details(self, page: Page, customer: Dict) -> Dict:
        """Extract detailed customer information from details page"""
        try:
            print(f"Extracting details for {customer['first_name']} {customer['last_name']}")
            
            # Initialize detail sections
            customer['contact_details'] = {}
            customer['roles'] = []
            customer['loyalty'] = {}
            customer['coupons'] = []
            customer['orders'] = []
            customer['delivery'] = {}
            customer['discounts'] = []
            
            # Wait for page to load
            page.wait_for_load_state('networkidle')
            
            # Extract Contact Details
            try:
                contact_section = page.query_selector('div:has-text("Contact Details")')
                if contact_section:
                    contact_info = contact_section.query_selector('..').inner_text()
                    customer['contact_details']['raw_text'] = contact_info
            except:
                pass
            
            # Extract Roles
            try:
                roles_section = page.query_selector('div:has-text("Roles")')
                if roles_section:
                    roles_text = roles_section.query_selector('..').inner_text()
                    customer['roles'] = [role.strip() for role in roles_text.split('\n') if role.strip()]
            except:
                pass
            
            # Extract Loyalty
            try:
                loyalty_section = page.query_selector('div:has-text("Loyalty")')
                if loyalty_section:
                    loyalty_text = loyalty_section.query_selector('..').inner_text()
                    customer['loyalty']['raw_text'] = loyalty_text
            except:
                pass
            
            # Extract Coupons
            try:
                coupons_section = page.query_selector('div:has-text("Coupons")')
                if coupons_section:
                    coupon_elements = coupons_section.query_selector_all('..//tr')
                    for coupon_row in coupon_elements:
                        coupon_text = coupon_row.inner_text()
                        if coupon_text and coupon_text != "Coupons":
                            customer['coupons'].append(coupon_text)
            except:
                pass
            
            # Extract Orders
            try:
                orders_section = page.query_selector('div:has-text("Orders")')
                if orders_section:
                    order_elements = orders_section.query_selector_all('..//tr')
                    for order_row in order_elements[1:]:  # Skip header
                        cells = order_row.query_selector_all('td')
                        if len(cells) >= 3:
                            order = {
                                'order_id': cells[0].inner_text().strip(),
                                'date': cells[1].inner_text().strip(),
                                'total': cells[2].inner_text().strip()
                            }
                            customer['orders'].append(order)
            except:
                pass
            
            # Extract Delivery
            try:
                delivery_section = page.query_selector('div:has-text("Delivery")')
                if delivery_section:
                    delivery_text = delivery_section.query_selector('..').inner_text()
                    customer['delivery']['raw_text'] = delivery_text
            except:
                pass
            
            # Extract Discounts
            try:
                discounts_section = page.query_selector('div:has-text("Discounts")')
                if discounts_section:
                    discount_elements = discounts_section.query_selector_all('..//tr')
                    for discount_row in discount_elements[1:]:  # Skip header
                        discount_text = discount_row.inner_text()
                        if discount_text:
                            customer['discounts'].append(discount_text)
            except:
                pass
            
            return customer
            
        except Exception as e:
            print(f"Error extracting details: {e}")
            return customer
    
    def scrape_current_page(self, page: Page) -> int:
        """Scrape all customers on current page"""
        scraped_count = 0
        
        try:
            # Wait for table to load
            page.wait_for_selector('table')
            print("Table found, looking for customer rows...")
            
            # Find all customer rows - use more specific selector
            customer_rows = page.query_selector_all('tbody tr')
            print(f"Found {len(customer_rows)} table rows")
            
            for i, row in enumerate(customer_rows):
                try:
                    # Extract basic info
                    customer = self.extract_customer_basic_info(row)
                    if not customer:
                        print(f"Row {i+1}: Skipped (header/pagination row)")
                        continue
                    
                    print(f"Row {i+1}: Processing {customer['first_name']} {customer['last_name']} ({customer['email']})")
                    
                    # Check if already scraped
                    if customer['email'].lower() in self.scraped_emails:
                        print(f"Skipping {customer['email']} - already scraped")
                        continue
                    
                    # Click Details button - try multiple selectors
                    details_button = (
                        row.query_selector('button:has-text("Details")') or
                        row.query_selector('td:last-child button') or
                        row.query_selector('input[type="button"][value="Details"]') or
                        row.query_selector('button') or
                        row.query_selector('input[type="submit"]')
                    )
                    
                    if details_button:
                        print(f"Clicking Details button for {customer['email']}")
                        details_button.click()
                        page.wait_for_load_state('networkidle')
                        
                        # Extract detailed information
                        customer = self.extract_customer_details(page, customer)
                        
                        # Add to data
                        self.customers_data.append(customer)
                        self.scraped_emails.add(customer['email'].lower())
                        scraped_count += 1
                        
                        print(f"✅ Scraped customer {scraped_count}: {customer['first_name']} {customer['last_name']}")
                        
                        # Go back to customer list
                        page.go_back()
                        page.wait_for_load_state('networkidle')
                        
                        # Small delay to be respectful
                        time.sleep(1)
                    else:
                        print(f"❌ No Details button found for {customer['email']}")
                        
                except Exception as e:
                    print(f"❌ Error processing customer {i+1}: {e}")
                    continue
            
            return scraped_count
            
        except Exception as e:
            print(f"❌ Error scraping page: {e}")
            return 0
    
    def scrape_all_customers(self):
        """Main scraping function - handles all pages"""
        with sync_playwright() as p:
            # Launch browser
            browser = p.chromium.launch(headless=False)  # Set to True for headless
            page = browser.new_page()
            
            try:
                # Login
                if not self.login(page):
                    print("Failed to login. Exiting.")
                    return
                
                # Navigate to customers page
                print(f"Navigating to customer page: {self.customer_url}")
                page.goto(self.customer_url)
                page.wait_for_load_state('networkidle')
                
                # Verify we're on the correct page
                if not self.verify_customer_page(page):
                    print("❌ Failed to reach customer page. Exiting.")
                    return
                
                # Get total pages info
                pagination_text = page.query_selector('text*="of 27"')
                if pagination_text:
                    total_pages = 27
                    print(f"Found {total_pages} pages to scrape")
                else:
                    total_pages = 1
                    print("Single page detected")
                
                total_scraped = 0
                
                # Scrape each page
                for page_num in range(1, total_pages + 1):
                    print(f"\n=== Scraping Page {page_num}/{total_pages} ===")
                    
                    # Scrape current page
                    page_scraped = self.scrape_current_page(page)
                    total_scraped += page_scraped
                    
                    print(f"Page {page_num} complete. Scraped {page_scraped} customers.")
                    
                    # Save progress after each page
                    self.save_data()
                    
                    # Navigate to next page if not last page
                    if page_num < total_pages:
                        try:
                            # Find and click next page
                            page_dropdown = page.query_selector('select')
                            if page_dropdown:
                                page_dropdown.select_option(str(page_num + 1))
                                page.wait_for_load_state('networkidle')
                        except Exception as e:
                            print(f"Error navigating to next page: {e}")
                            break
                
                print(f"\n=== Scraping Complete ===")
                print(f"Total customers scraped: {total_scraped}")
                print(f"Total customers in database: {len(self.customers_data)}")
                
                # Final save
                self.save_data()
                
            except Exception as e:
                print(f"Scraping error: {e}")
            finally:
                browser.close()

def main():
    """Main function"""
    scraper = KEATchenCustomerScraper()
    scraper.scrape_all_customers()

if __name__ == "__main__":
    main()