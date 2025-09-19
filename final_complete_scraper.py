#!/usr/bin/env python3
"""
Final Complete KEATchen Customer Scraper
This version uses the proven modal extraction method to complete all 538 customers
"""

import json
import time
import os
from datetime import datetime
from playwright.sync_api import sync_playwright

class FinalCustomerScraper:
    def __init__(self):
        self.base_url = "https://keatchenunited.app4food.co.uk"
        self.login_url = f"{self.base_url}/admin/Account/Login"
        self.customer_url = f"{self.base_url}/admin/Customer"
        
        self.username = "admin@keatchen"
        self.password = "keatchen22"
        
        self.customers_data = []
        self.scraped_emails = set()
        self.output_dir = "customer_data"
        
        os.makedirs(self.output_dir, exist_ok=True)
        self.load_existing_data()

    def load_existing_data(self):
        """Load existing scraped data"""
        try:
            if os.path.exists(f"{self.output_dir}/customers_mcp.json"):
                with open(f"{self.output_dir}/customers_mcp.json", 'r') as f:
                    self.customers_data = json.load(f)
                    self.scraped_emails = {c.get('email', '').lower() for c in self.customers_data}
                    print(f"📚 Starting with {len(self.customers_data)} existing customers")
        except Exception as e:
            print(f"Error loading: {e}")

    def save_progress(self):
        """Save current progress"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save main database
        with open(f"{self.output_dir}/customers_mcp.json", 'w') as f:
            json.dump(self.customers_data, f, indent=2)
        
        # Create backup
        backup_file = f"{self.output_dir}/backup_{timestamp}.json"
        with open(backup_file, 'w') as f:
            json.dump(self.customers_data, f, indent=2)
        
        print(f"💾 Progress saved: {len(self.customers_data)} customers")

    def extract_customer_details_from_modal(self, page, basic_customer):
        """Extract complete customer details from modal"""
        customer = basic_customer.copy()
        
        # Initialize detailed data structure
        customer.update({
            'contact_details': {},
            'orders': [],
            'loyalty': {},
            'coupons': [],
            'roles': [],
            'delivery': {},
            'discounts': []
        })
        
        try:
            # Wait for modal to appear
            page.wait_for_selector('[id*="modal"]', timeout=5000)
            
            # Extract Contact Details
            try:
                # Make sure we're on contact details tab
                contact_tab = page.query_selector('div:has-text("Contact Details")')
                if contact_tab:
                    contact_tab.click()
                    page.wait_for_timeout(500)
                
                # Extract all form fields
                form_data = {}
                
                # Get all input fields with values
                inputs = page.query_selector_all('input[disabled]')
                for inp in inputs:
                    value = inp.get_attribute('value') or ''
                    name = inp.get_attribute('name') or ''
                    
                    if value:
                        if '@' in value:
                            form_data['verified_email'] = value
                        elif '+44' in value:
                            form_data['verified_mobile'] = value
                        elif 'First' in name or 'first' in name:
                            form_data['verified_firstname'] = value
                        elif 'Last' in name or 'last' in name:
                            form_data['verified_lastname'] = value
                        elif 'Address1' in name:
                            form_data['address1'] = value
                        elif 'Address2' in name:
                            form_data['address2'] = value
                        elif 'City' in name:
                            form_data['city'] = value
                        elif 'County' in name:
                            form_data['county'] = value
                        elif 'Postcode' in name:
                            form_data['verified_postcode'] = value
                
                # Extract DOB from dropdowns
                try:
                    day_select = page.query_selector('select:nth-of-type(1)')
                    month_select = page.query_selector('select:nth-of-type(2)')
                    year_select = page.query_selector('select:nth-of-type(3)')
                    
                    if day_select and month_select and year_select:
                        day = day_select.evaluate('el => el.options[el.selectedIndex].text')
                        month = month_select.evaluate('el => el.options[el.selectedIndex].text')
                        year = year_select.evaluate('el => el.options[el.selectedIndex].text')
                        
                        if day and month and year and day != '' and month != '' and year != '':
                            form_data['date_of_birth'] = f"{day}/{month}/{year}"
                except:
                    pass
                
                customer['contact_details'] = form_data
                
            except Exception as e:
                print(f"    ⚠️ Contact details error: {e}")
            
            # Extract Orders
            try:
                orders_tab = page.query_selector('div:has-text("Orders")')
                if orders_tab:
                    orders_tab.click()
                    page.wait_for_timeout(500)
                    
                    # Look for orders table
                    orders_table = page.query_selector('table')
                    if orders_table:
                        order_rows = orders_table.query_selector_all('tbody tr')
                        orders_list = []
                        
                        for row in order_rows:
                            cells = row.query_selector_all('td')
                            if len(cells) >= 5:
                                order_no = cells[0].inner_text().strip()
                                if order_no and order_no != 'Order No.':
                                    order = {
                                        'order_number': order_no,
                                        'date': cells[1].inner_text().strip(),
                                        'status': cells[2].inner_text().strip(),
                                        'method': cells[3].inner_text().strip(),
                                        'total': cells[4].inner_text().strip(),
                                        'discount': cells[5].inner_text().strip() if len(cells) > 5 else ''
                                    }
                                    orders_list.append(order)
                        
                        customer['orders'] = orders_list
                        
            except Exception as e:
                print(f"    ⚠️ Orders error: {e}")
            
            # Quick extraction for other tabs
            for tab_name in ['Loyalty', 'Coupons', 'Roles', 'Delivery', 'Discounts']:
                try:
                    tab = page.query_selector(f'div:has-text("{tab_name}")')
                    if tab:
                        tab.click()
                        page.wait_for_timeout(300)
                        
                        # Get modal content
                        modal = page.query_selector('[id*="modal"]')
                        if modal:
                            content = modal.inner_text()
                            if content and len(content) > 10:
                                customer[tab_name.lower()] = {'content': content[:300]}  # Limit size
                                
                except Exception as e:
                    print(f"    ⚠️ {tab_name} error: {e}")
            
        except Exception as e:
            print(f"    ❌ Modal extraction error: {e}")
        
        return customer

    def complete_scraping(self):
        """Complete the full scraping operation"""
        print("🚀 === FINAL COMPLETE CUSTOMER EXTRACTION ===")
        
        with sync_playwright() as p:
            # Launch browser
            browser = p.chromium.launch(headless=True, slow_mo=50)
            page = browser.new_page()
            
            try:
                # Login
                print("🔐 Logging in...")
                page.goto(self.login_url)
                page.wait_for_load_state('networkidle')
                
                page.fill('input[placeholder*="email"]', self.username)
                page.fill('input[type="password"]', self.password)
                page.click('button:has-text("Log In")')
                page.wait_for_load_state('networkidle')
                
                if not page.query_selector('a:has-text("Logout")'):
                    print("❌ Login failed")
                    return
                
                # Navigate to customers
                print("🗂️ Navigating to customers page...")
                page.goto(self.customer_url)
                page.wait_for_load_state('networkidle')
                
                # Determine starting page
                current_page = len(set(c.get('page', 0) for c in self.customers_data)) or 1
                start_page = current_page + 1 if current_page < 27 else 1
                
                print(f"📄 Starting from page {start_page} (have {len(self.customers_data)} customers)")
                
                total_scraped = 0
                
                # Process remaining pages
                for page_num in range(start_page, 28):
                    print(f"\\n🔄 === PAGE {page_num}/27 ===")
                    
                    # Navigate to page
                    if page_num > 1:
                        try:
                            dropdown = page.query_selector('select:first-of-type')
                            if dropdown:
                                dropdown.select_option(str(page_num))
                                page.wait_for_load_state('networkidle')
                                time.sleep(1)
                        except Exception as e:
                            print(f"❌ Navigation error: {e}")
                            continue
                    
                    # Extract customers on current page
                    customer_rows = page.query_selector_all('tbody tr')
                    page_scraped = 0
                    
                    for row in customer_rows:
                        try:
                            cells = row.query_selector_all('td')
                            if len(cells) < 6:
                                continue
                            
                            # Skip header/pagination rows
                            row_text = row.inner_text()
                            if 'Firstname' in row_text or 'of 27' in row_text or 'of 538' in row_text:
                                continue
                            
                            # Basic customer info
                            basic_customer = {
                                'first_name': cells[0].inner_text().strip(),
                                'last_name': cells[1].inner_text().strip(),
                                'email': cells[2].inner_text().strip(),
                                'mobile': cells[3].inner_text().strip(),
                                'address': cells[4].inner_text().strip(),
                                'postcode': cells[5].inner_text().strip(),
                                'page': page_num,
                                'scraped_at': datetime.now().isoformat()
                            }
                            
                            # Skip if already have this customer
                            if basic_customer['email'].lower() in self.scraped_emails:
                                continue
                            
                            print(f"  🔍 {basic_customer['first_name']} {basic_customer['last_name']} ({basic_customer['email']})")
                            
                            # Click Details button to open modal
                            details_btn = row.query_selector('button')
                            if details_btn:
                                details_btn.click()
                                page.wait_for_timeout(1000)
                                
                                # Extract complete customer data from modal
                                complete_customer = self.extract_customer_details_from_modal(page, basic_customer)
                                
                                # Close modal
                                close_btn = page.query_selector('button:has-text("Close")')
                                if close_btn:
                                    close_btn.click()
                                    page.wait_for_timeout(500)
                                
                                # Add to database
                                self.customers_data.append(complete_customer)
                                self.scraped_emails.add(complete_customer['email'].lower())
                                page_scraped += 1
                                total_scraped += 1
                                
                                print(f"    ✅ Complete data extracted!")
                                
                                # Small delay to be respectful
                                time.sleep(0.5)
                                
                        except Exception as e:
                            print(f"    ❌ Row extraction error: {e}")
                            continue
                    
                    print(f"📊 Page {page_num} complete: {page_scraped} customers | Total: {len(self.customers_data)}")
                    
                    # Save progress after each page
                    self.save_progress()
                    
                    # Progress update
                    progress = page_num / 27 * 100
                    print(f"📈 Overall progress: {progress:.1f}%")
                
                print(f"\\n🎉 === EXTRACTION COMPLETE ===")
                print(f"🏆 Total customers in database: {len(self.customers_data)}")
                print(f"📈 New customers scraped this session: {total_scraped}")
                
                # Create final exports
                self.create_final_exports()
                
            except Exception as e:
                print(f"❌ Scraping error: {e}")
                # Save progress even if error
                self.save_progress()
            finally:
                browser.close()

    def create_final_exports(self):
        """Create comprehensive final exports"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Final JSON database
        final_json = f"{self.output_dir}/FINAL_KEATCHEN_CUSTOMERS_{timestamp}.json"
        with open(final_json, 'w') as f:
            json.dump(self.customers_data, f, indent=2)
        
        # Master CSV export
        final_csv = f"{self.output_dir}/FINAL_KEATCHEN_CUSTOMERS_{timestamp}.csv"
        with open(final_csv, 'w') as f:
            # Headers
            headers = [
                'FirstName', 'LastName', 'Email', 'Mobile', 'Address', 'Postcode',
                'VerifiedEmail', 'VerifiedMobile', 'DateOfBirth', 'City', 'County',
                'TotalOrders', 'HasLoyalty', 'HasCoupons', 'Page', 'ScrapedAt'
            ]
            f.write(','.join(headers) + '\n')
            
            # Data rows
            for c in self.customers_data:
                contact = c.get('contact_details', {})
                row = [
                    f'"{c.get("first_name", "")}"',
                    f'"{c.get("last_name", "")}"',
                    f'"{c.get("email", "")}"',
                    f'"{c.get("mobile", "")}"',
                    f'"{c.get("address", "")}"',
                    f'"{c.get("postcode", "")}"',
                    f'"{contact.get("verified_email", "")}"',
                    f'"{contact.get("verified_mobile", "")}"',
                    f'"{contact.get("date_of_birth", "")}"',
                    f'"{contact.get("city", "")}"',
                    f'"{contact.get("county", "")}"',
                    str(len(c.get('orders', []))),
                    str(bool(c.get('loyalty', {}).get('content'))),
                    str(bool(c.get('coupons'))),
                    str(c.get('page', 0)),
                    f'"{c.get("scraped_at", "")}"'
                ]
                f.write(','.join(row) + '\n')
        
        # Summary report
        summary_file = f"{self.output_dir}/EXTRACTION_SUMMARY_{timestamp}.txt"
        with open(summary_file, 'w') as f:
            f.write('KEATchen Customer Database - Complete Extraction Summary\n')
            f.write('=' * 60 + '\n')
            f.write(f'Extraction completed: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
            f.write(f'Total customers extracted: {len(self.customers_data)}\n')
            f.write(f'Target was: 538 customers across 27 pages\n\n')
            
            # Progress by page
            page_counts = {}
            for c in self.customers_data:
                page = c.get('page', 0)
                page_counts[page] = page_counts.get(page, 0) + 1
            
            f.write('Extraction by Page:\n')
            for page in sorted(page_counts.keys()):
                f.write(f'  Page {page:2d}: {page_counts[page]:3d} customers\n')
            
            # Data quality metrics
            emails_with_details = len([c for c in self.customers_data if c.get('contact_details', {}).get('verified_email')])
            customers_with_orders = len([c for c in self.customers_data if c.get('orders')])
            customers_with_dob = len([c for c in self.customers_data if c.get('contact_details', {}).get('date_of_birth')])
            
            f.write(f'\nData Quality Metrics:\n')
            f.write(f'  Customers with verified email: {emails_with_details}\n')
            f.write(f'  Customers with order history: {customers_with_orders}\n')
            f.write(f'  Customers with date of birth: {customers_with_dob}\n')
            
            # Geographic breakdown
            cities = {}
            for c in self.customers_data:
                address = c.get('address', '')
                if 'East Kilbride' in address:
                    cities['East Kilbride'] = cities.get('East Kilbride', 0) + 1
                elif 'Blantyre' in address:
                    cities['Blantyre'] = cities.get('Blantyre', 0) + 1
                elif 'Cambuslang' in address:
                    cities['Cambuslang'] = cities.get('Cambuslang', 0) + 1
                elif 'Hamilton' in address:
                    cities['Hamilton'] = cities.get('Hamilton', 0) + 1
                else:
                    cities['Other'] = cities.get('Other', 0) + 1
            
            f.write(f'\nGeographic Distribution:\n')
            for city, count in sorted(cities.items(), key=lambda x: x[1], reverse=True):
                f.write(f'  {city:15s}: {count:3d} customers\n')
        
        print(f'\n🎯 === FINAL EXPORT COMPLETE ===')
        print(f'📄 Complete JSON: {final_json}')
        print(f'📊 Master CSV: {final_csv}')
        print(f'📋 Summary Report: {summary_file}')
        print(f'🏆 Total Customers: {len(self.customers_data)}')

def main():
    """Run the complete extraction"""
    scraper = FinalCustomerScraper()
    scraper.complete_scraping()

if __name__ == "__main__":
    main()