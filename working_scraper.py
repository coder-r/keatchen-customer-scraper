#!/usr/bin/env python3
"""
Working KEATchen Customer Scraper - Modal-based extraction
Handles the customer details modal popup correctly
"""

import json
import csv
import time
import os
from datetime import datetime
from typing import Dict, List, Set, Optional
from playwright.sync_api import sync_playwright, Page, Browser

class WorkingCustomerScraper:
    def __init__(self):
        self.base_url = "https://keatchenunited.app4food.co.uk"
        self.login_url = f"{self.base_url}/admin/Account/Login"
        self.customer_url = f"{self.base_url}/admin/Customer"
        
        # Credentials
        self.username = "admin@keatchen"
        self.password = "keatchen22"
        
        # Data storage
        self.customers_data = []
        self.scraped_emails: Set[str] = set()
        self.output_dir = "customer_data"
        
        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Load existing data
        self.load_existing_data()
        
        print(f"✅ Scraper initialized. Found {len(self.scraped_emails)} existing customers.")

    def load_existing_data(self):
        """Load existing customer data to avoid duplicates"""
        try:
            if os.path.exists(f"{self.output_dir}/customers.json"):
                with open(f"{self.output_dir}/customers.json", 'r') as f:
                    existing_data = json.load(f)
                    self.customers_data = existing_data
                    self.scraped_emails = {customer.get('email', '').lower() for customer in existing_data}
                    print(f"Loaded {len(self.customers_data)} existing customers")
        except Exception as e:
            print(f"Error loading existing data: {e}")

    def save_data(self):
        """Save data to JSON and CSV"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save JSON
        json_file = f"{self.output_dir}/customers_complete.json"
        with open(json_file, 'w') as f:
            json.dump(self.customers_data, f, indent=2)
        
        # Save CSV
        if self.customers_data:
            csv_file = f"{self.output_dir}/customers_{timestamp}.csv"
            
            # Flatten data for CSV
            flattened_data = []
            for customer in self.customers_data:
                flat_customer = {
                    'first_name': customer.get('first_name', ''),
                    'last_name': customer.get('last_name', ''),
                    'email': customer.get('email', ''),
                    'mobile': customer.get('mobile', ''),
                    'address': customer.get('address', ''),
                    'postcode': customer.get('postcode', ''),
                    'dob': customer.get('contact_details', {}).get('dob', ''),
                    'address1': customer.get('contact_details', {}).get('address1', ''),
                    'address2': customer.get('contact_details', {}).get('address2', ''),
                    'city': customer.get('contact_details', {}).get('city', ''),
                    'county': customer.get('contact_details', {}).get('county', ''),
                    'total_orders': len(customer.get('orders', [])),
                    'has_loyalty': bool(customer.get('loyalty', {}).get('points')),
                    'has_coupons': len(customer.get('coupons', [])) > 0,
                    'scraped_at': customer.get('scraped_at', '')
                }
                flattened_data.append(flat_customer)
            
            import pandas as pd
            df = pd.DataFrame(flattened_data)
            df.to_csv(csv_file, index=False)
            
            print(f"💾 Data saved: {len(self.customers_data)} customers")
            print(f"📄 JSON: {json_file}")
            print(f"📊 CSV: {csv_file}")

    def login(self, page: Page) -> bool:
        """Login to admin panel"""
        try:
            print("🔐 Logging in...")
            page.goto(self.login_url)
            page.wait_for_load_state('networkidle')
            
            # Fill credentials
            page.fill('input[placeholder*="email"]', self.username)
            page.fill('input[type="password"]', self.password)
            
            # Login
            page.click('button:has-text("Log In")')
            page.wait_for_load_state('networkidle')
            
            # Verify login
            if page.query_selector('a:has-text("Logout")'):
                print("✅ Login successful!")
                return True
            else:
                print("❌ Login failed!")
                return False
                
        except Exception as e:
            print(f"❌ Login error: {e}")
            return False

    def extract_modal_data(self, page: Page) -> Dict:
        """Extract all data from customer details modal"""
        customer_details = {
            'contact_details': {},
            'roles': [],
            'loyalty': {},
            'coupons': [],
            'orders': [],
            'delivery': {},
            'discounts': []
        }
        
        try:
            # Wait for modal to be visible
            page.wait_for_selector('[id*="modal"]', timeout=5000)
            
            # Extract Contact Details tab
            try:
                page.click('div:has-text("Contact Details")')
                page.wait_for_timeout(500)
                
                # Extract form fields
                email_field = page.query_selector('input[value*="@"]')
                if email_field:
                    customer_details['contact_details']['email'] = email_field.get_attribute('value')
                
                mobile_field = page.query_selector('input[name*="Mobile"], input[value*="+44"]')
                if mobile_field:
                    customer_details['contact_details']['mobile'] = mobile_field.get_attribute('value')
                
                firstname_field = page.query_selector('input[name*="Firstname"]')
                if firstname_field:
                    customer_details['contact_details']['firstname'] = firstname_field.get_attribute('value')
                
                lastname_field = page.query_selector('input[name*="Lastname"]')
                if lastname_field:
                    customer_details['contact_details']['lastname'] = lastname_field.get_attribute('value')
                
                # Address fields
                address1_field = page.query_selector('input[name*="Address1"]')
                if address1_field:
                    customer_details['contact_details']['address1'] = address1_field.get_attribute('value')
                
                address2_field = page.query_selector('input[name*="Address2"]')
                if address2_field:
                    customer_details['contact_details']['address2'] = address2_field.get_attribute('value')
                
                city_field = page.query_selector('input[name*="City"]')
                if city_field:
                    customer_details['contact_details']['city'] = city_field.get_attribute('value')
                
                county_field = page.query_selector('input[name*="County"]')
                if county_field:
                    customer_details['contact_details']['county'] = county_field.get_attribute('value')
                
                postcode_field = page.query_selector('input[name*="Postcode"]')
                if postcode_field:
                    customer_details['contact_details']['postcode'] = postcode_field.get_attribute('value')
                
                # DOB dropdowns
                day_dropdown = page.query_selector('select:nth-of-type(1)')
                month_dropdown = page.query_selector('select:nth-of-type(2)')
                year_dropdown = page.query_selector('select:nth-of-type(3)')
                
                if day_dropdown and month_dropdown and year_dropdown:
                    day = day_dropdown.evaluate('el => el.options[el.selectedIndex].text')
                    month = month_dropdown.evaluate('el => el.options[el.selectedIndex].text')
                    year = year_dropdown.evaluate('el => el.options[el.selectedIndex].text')
                    if day != '' and month != '' and year != '':
                        customer_details['contact_details']['dob'] = f"{day}/{month}/{year}"
                
            except Exception as e:
                print(f"⚠️ Error extracting contact details: {e}")
            
            # Extract Orders tab
            try:
                page.click('div:has-text("Orders")')
                page.wait_for_timeout(500)
                
                # Look for orders table
                orders_table = page.query_selector('table')
                if orders_table:
                    order_rows = orders_table.query_selector_all('tbody tr')
                    for row in order_rows:
                        cells = row.query_selector_all('td')
                        if len(cells) >= 5:
                            order = {
                                'order_no': cells[0].inner_text().strip(),
                                'date': cells[1].inner_text().strip(),
                                'status': cells[2].inner_text().strip(),
                                'method': cells[3].inner_text().strip(),
                                'total': cells[4].inner_text().strip(),
                                'discount': cells[5].inner_text().strip() if len(cells) > 5 else ''
                            }
                            # Only add if it's actual order data
                            if order['order_no'] and order['order_no'] != 'Order No.':
                                customer_details['orders'].append(order)
                                
            except Exception as e:
                print(f"⚠️ Error extracting orders: {e}")
            
            # Extract Loyalty tab  
            try:
                page.click('div:has-text("Loyalty")')
                page.wait_for_timeout(500)
                
                loyalty_content = page.query_selector('[id*="modal"] div:visible')
                if loyalty_content:
                    loyalty_text = loyalty_content.inner_text()
                    customer_details['loyalty']['raw_text'] = loyalty_text
                    
            except Exception as e:
                print(f"⚠️ Error extracting loyalty: {e}")
            
            # Extract Coupons tab
            try:
                page.click('div:has-text("Coupons")')
                page.wait_for_timeout(500)
                
                coupons_table = page.query_selector('table')
                if coupons_table:
                    coupon_rows = coupons_table.query_selector_all('tbody tr')
                    for row in coupon_rows:
                        coupon_text = row.inner_text().strip()
                        if coupon_text and 'Coupon' not in coupon_text:
                            customer_details['coupons'].append(coupon_text)
                            
            except Exception as e:
                print(f"⚠️ Error extracting coupons: {e}")
            
            # Extract Roles tab
            try:
                page.click('div:has-text("Roles")')
                page.wait_for_timeout(500)
                
                roles_content = page.query_selector('[id*="modal"] div:visible')
                if roles_content:
                    roles_text = roles_content.inner_text()
                    if roles_text and roles_text != 'Roles':
                        customer_details['roles'].append(roles_text)
                        
            except Exception as e:
                print(f"⚠️ Error extracting roles: {e}")
            
            # Extract Delivery tab
            try:
                page.click('div:has-text("Delivery")')
                page.wait_for_timeout(500)
                
                delivery_content = page.query_selector('[id*="modal"] div:visible')
                if delivery_content:
                    delivery_text = delivery_content.inner_text()
                    customer_details['delivery']['raw_text'] = delivery_text
                    
            except Exception as e:
                print(f"⚠️ Error extracting delivery: {e}")
            
            # Extract Discounts tab
            try:
                page.click('div:has-text("Discounts")')
                page.wait_for_timeout(500)
                
                discounts_table = page.query_selector('table')
                if discounts_table:
                    discount_rows = discounts_table.query_selector_all('tbody tr')
                    for row in discount_rows:
                        discount_text = row.inner_text().strip()
                        if discount_text and 'Discount' not in discount_text:
                            customer_details['discounts'].append(discount_text)
                            
            except Exception as e:
                print(f"⚠️ Error extracting discounts: {e}")
                
        except Exception as e:
            print(f"❌ Error extracting modal data: {e}")
        
        return customer_details

    def scrape_current_page_customers(self, page: Page) -> int:
        """Scrape all customers on current page"""
        scraped_count = 0
        
        try:
            # Get customer rows
            customer_rows = page.query_selector_all('tbody tr')
            print(f"📋 Found {len(customer_rows)} table rows")
            
            for i, row in enumerate(customer_rows):
                try:
                    # Extract basic info from row
                    cells = row.query_selector_all('td')
                    if len(cells) < 6:
                        continue
                    
                    # Skip header/pagination rows
                    row_text = row.inner_text()
                    if "Firstname" in row_text or "of 27" in row_text or "of 538" in row_text:
                        continue
                    
                    # Create customer record
                    customer = {
                        'first_name': cells[0].inner_text().strip(),
                        'last_name': cells[1].inner_text().strip(),
                        'email': cells[2].inner_text().strip(),
                        'mobile': cells[3].inner_text().strip(),
                        'address': cells[4].inner_text().strip(),
                        'postcode': cells[5].inner_text().strip(),
                        'scraped_at': datetime.now().isoformat()
                    }
                    
                    # Skip if already scraped
                    if customer['email'].lower() in self.scraped_emails:
                        print(f"⏭️ Skipping {customer['email']} - already scraped")
                        continue
                    
                    print(f"🔍 Processing: {customer['first_name']} {customer['last_name']} ({customer['email']})")
                    
                    # Click Details button
                    details_button = row.query_selector('button')
                    if details_button:
                        details_button.click()
                        page.wait_for_timeout(1000)  # Wait for modal
                        
                        # Extract detailed modal data
                        modal_data = self.extract_modal_data(page)
                        customer.update(modal_data)
                        
                        # Close modal
                        close_button = page.query_selector('button:has-text("Close")')
                        if close_button:
                            close_button.click()
                            page.wait_for_timeout(500)
                        
                        # Add to database
                        self.customers_data.append(customer)
                        self.scraped_emails.add(customer['email'].lower())
                        scraped_count += 1
                        
                        print(f"✅ Scraped customer {scraped_count}: {customer['first_name']} {customer['last_name']}")
                        
                        # Small delay
                        time.sleep(0.5)
                        
                    else:
                        print(f"❌ No Details button found for {customer['email']}")
                        
                except Exception as e:
                    print(f"❌ Error processing row {i+1}: {e}")
                    continue
            
            return scraped_count
            
        except Exception as e:
            print(f"❌ Error scraping page: {e}")
            return 0

    def scrape_all_customers(self):
        """Main scraping function"""
        with sync_playwright() as p:
            # Launch browser (visible for debugging)
            browser = p.chromium.launch(headless=False, slow_mo=100)
            page = browser.new_page()
            
            try:
                # Login
                if not self.login(page):
                    return
                
                # Navigate to customers
                print(f"🗂️ Navigating to customers page...")
                page.goto(self.customer_url)
                page.wait_for_load_state('networkidle')
                
                # Get total pages
                pagination_info = page.query_selector('text*="of 27"')
                total_pages = 27
                print(f"📄 Total pages to scrape: {total_pages}")
                
                total_scraped = 0
                
                # Scrape each page
                for page_num in range(1, total_pages + 1):
                    print(f"\n🔄 === SCRAPING PAGE {page_num}/{total_pages} ===")
                    
                    # Scrape current page
                    page_scraped = self.scrape_current_page_customers(page)
                    total_scraped += page_scraped
                    
                    print(f"📊 Page {page_num} complete: {page_scraped} new customers scraped")
                    print(f"📈 Total progress: {total_scraped} customers | {len(self.customers_data)} in database")
                    
                    # Save progress
                    self.save_data()
                    
                    # Navigate to next page
                    if page_num < total_pages:
                        try:
                            print(f"➡️ Moving to page {page_num + 1}...")
                            page_dropdown = page.query_selector('select:first-of-type')
                            if page_dropdown:
                                page_dropdown.select_option(str(page_num + 1))
                                page.wait_for_load_state('networkidle')
                                time.sleep(1)
                            else:
                                print("❌ Could not find page dropdown")
                                break
                        except Exception as e:
                            print(f"❌ Error navigating to next page: {e}")
                            break
                
                print(f"\n🎉 === SCRAPING COMPLETE ===")
                print(f"🏆 Total customers scraped this session: {total_scraped}")
                print(f"📚 Total customers in database: {len(self.customers_data)}")
                
                # Final save
                self.save_data()
                
            except Exception as e:
                print(f"❌ Scraping error: {e}")
            finally:
                print("🔚 Closing browser...")
                browser.close()

def main():
    """Run the scraper"""
    print("🚀 === KEATchen Customer Scraper v2.0 ===")
    print("📋 Modal-based extraction with full customer details")
    
    scraper = WorkingCustomerScraper()
    scraper.scrape_all_customers()
    
    print("✨ Scraping completed!")

if __name__ == "__main__":
    main()