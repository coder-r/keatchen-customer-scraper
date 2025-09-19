#!/usr/bin/env python3
"""
Fast KEATchen Customer Scraper - Headless and optimized
"""

import json
import time
import os
from datetime import datetime
from playwright.sync_api import sync_playwright

def extract_customer_from_modal(page, customer_basic):
    """Extract detailed customer data from modal"""
    customer = customer_basic.copy()
    customer.update({
        'contact_details': {},
        'orders': [],
        'loyalty': '',
        'coupons': [],
        'roles': '',
        'delivery': '',
        'discounts': []
    })
    
    try:
        # Wait for modal
        page.wait_for_selector('[id*="modal"]', timeout=3000)
        time.sleep(0.5)
        
        # Contact Details - extract form values
        try:
            inputs = page.query_selector_all('input[disabled]')
            for inp in inputs:
                value = inp.get_attribute('value')
                if value:
                    name = inp.get_attribute('name') or ''
                    if 'Email' in name or '@' in value:
                        customer['contact_details']['email_verified'] = value
                    elif 'Mobile' in name or '+44' in value:
                        customer['contact_details']['mobile_verified'] = value
                    elif 'First' in name:
                        customer['contact_details']['firstname'] = value
                    elif 'Last' in name:
                        customer['contact_details']['lastname'] = value
                    elif 'Address1' in name:
                        customer['contact_details']['address1'] = value
                    elif 'Address2' in name:
                        customer['contact_details']['address2'] = value
                    elif 'City' in name:
                        customer['contact_details']['city'] = value
                    elif 'County' in name:
                        customer['contact_details']['county'] = value
                    elif 'Postcode' in name:
                        customer['contact_details']['postcode_verified'] = value
            
            # DOB from dropdowns
            try:
                selects = page.query_selector_all('select[disabled]')
                if len(selects) >= 3:
                    day = selects[0].evaluate('el => el.options[el.selectedIndex].text')
                    month = selects[1].evaluate('el => el.options[el.selectedIndex].text')
                    year = selects[2].evaluate('el => el.options[el.selectedIndex].text')
                    if day and month and year and day != '' and month != '' and year != '':
                        customer['contact_details']['dob'] = f"{day}/{month}/{year}"
            except:
                pass
                
        except Exception as e:
            print(f"  ⚠️ Contact details error: {e}")
        
        # Orders tab
        try:
            page.click('div:has-text("Orders")')
            time.sleep(0.5)
            
            orders_table = page.query_selector('table')
            if orders_table:
                order_rows = orders_table.query_selector_all('tbody tr')
                for row in order_rows:
                    cells = row.query_selector_all('td')
                    if len(cells) >= 5:
                        order_no = cells[0].inner_text().strip()
                        if order_no and order_no != 'Order No.':
                            order = {
                                'order_no': order_no,
                                'date': cells[1].inner_text().strip(),
                                'status': cells[2].inner_text().strip(),
                                'method': cells[3].inner_text().strip(),
                                'total': cells[4].inner_text().strip()
                            }
                            customer['orders'].append(order)
                            
        except Exception as e:
            print(f"  ⚠️ Orders error: {e}")
        
        # Check other tabs quickly
        for tab in ["Loyalty", "Coupons", "Roles", "Delivery", "Discounts"]:
            try:
                page.click(f'div:has-text("{tab}")')
                time.sleep(0.3)
                content = page.evaluate('() => document.querySelector("[id*=modal]").innerText')
                if content and len(content) > 10:
                    customer[tab.lower()] = content[:200]  # Limit content
            except:
                pass
        
    except Exception as e:
        print(f"  ❌ Modal extraction error: {e}")
    
    return customer

def main():
    print("🚀 Fast Customer Scraper Starting...")
    
    customers_data = []
    scraped_emails = set()
    
    # Load existing data
    if os.path.exists('customer_data/customers_complete.json'):
        try:
            with open('customer_data/customers_complete.json', 'r') as f:
                customers_data = json.load(f)
                scraped_emails = {c.get('email', '').lower() for c in customers_data}
                print(f"📚 Loaded {len(customers_data)} existing customers")
        except:
            pass
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)  # Fast headless mode
        page = browser.new_page()
        
        try:
            # Login
            print("🔐 Logging in...")
            page.goto("https://keatchenunited.app4food.co.uk/admin/Account/Login")
            page.wait_for_load_state('networkidle')
            
            page.fill('input[placeholder*="email"]', "admin@keatchen")
            page.fill('input[type="password"]', "keatchen22")
            page.click('button:has-text("Log In")')
            page.wait_for_load_state('networkidle')
            
            if not page.query_selector('a:has-text("Logout")'):
                print("❌ Login failed")
                return
            
            # Navigate to customers
            print("🗂️ Going to customers...")
            page.goto("https://keatchenunited.app4food.co.uk/admin/Customer")
            page.wait_for_load_state('networkidle')
            
            total_scraped = 0
            
            # Process all 27 pages
            for page_num in range(1, 28):
                print(f"\n📄 === PAGE {page_num}/27 ===")
                
                # Get customer rows on current page
                customer_rows = page.query_selector_all('tbody tr')
                page_scraped = 0
                
                for i, row in enumerate(customer_rows):
                    try:
                        cells = row.query_selector_all('td')
                        if len(cells) < 6:
                            continue
                        
                        row_text = row.inner_text()
                        if "Firstname" in row_text or "of 27" in row_text:
                            continue
                        
                        # Basic customer info
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
                        if customer['email'].lower() in scraped_emails:
                            print(f"  ⏭️ Skip: {customer['email']}")
                            continue
                        
                        print(f"  🔍 {customer['first_name']} {customer['last_name']} ({customer['email']})")
                        
                        # Click Details
                        details_button = row.query_selector('button')
                        if details_button:
                            details_button.click()
                            time.sleep(1)
                            
                            # Extract modal data
                            customer = extract_customer_from_modal(page, customer)
                            
                            # Close modal
                            close_btn = page.query_selector('button:has-text("Close")')
                            if close_btn:
                                close_btn.click()
                                time.sleep(0.5)
                            
                            # Add to database
                            customers_data.append(customer)
                            scraped_emails.add(customer['email'].lower())
                            page_scraped += 1
                            total_scraped += 1
                            
                            print(f"    ✅ Scraped! ({total_scraped} total)")
                            
                    except Exception as e:
                        print(f"    ❌ Row error: {e}")
                        continue
                
                print(f"📊 Page {page_num}: {page_scraped} new customers | Total: {total_scraped}")
                
                # Save progress every page
                os.makedirs('customer_data', exist_ok=True)
                with open('customer_data/customers_complete.json', 'w') as f:
                    json.dump(customers_data, f, indent=2)
                
                # Go to next page
                if page_num < 27:
                    try:
                        page_dropdown = page.query_selector('combobox:first-of-type, select:first-of-type')
                        if page_dropdown:
                            page_dropdown.select_option(str(page_num + 1))
                            page.wait_for_load_state('networkidle')
                            time.sleep(1)
                    except Exception as e:
                        print(f"❌ Navigation error: {e}")
                        break
            
            print(f"\n🎉 === COMPLETE ===")
            print(f"🏆 Total customers scraped: {total_scraped}")
            print(f"📚 Database size: {len(customers_data)}")
            
            # Final save with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            final_file = f'customer_data/keatchen_customers_final_{timestamp}.json'
            with open(final_file, 'w') as f:
                json.dump(customers_data, f, indent=2)
            
            print(f"💾 Final data: {final_file}")
            
        except Exception as e:
            print(f"❌ Main error: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    main()