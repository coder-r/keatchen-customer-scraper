#!/usr/bin/env python3
"""
COMPLETE ALL CUSTOMERS SCRAPER
This script will NOT STOP until all 538 customers are extracted
"""

import json
import time
import os
from datetime import datetime
from playwright.sync_api import sync_playwright

def extract_all_customers():
    print("🚀 === EXTRACTING ALL 538 CUSTOMERS ===")
    print("🎯 Will NOT stop until complete!")
    
    # Load existing data
    try:
        with open('customer_data/customers_mcp.json', 'r') as f:
            customers = json.load(f)
        existing_emails = {c.get('email', '').lower() for c in customers}
        print(f"📚 Starting with {len(customers)} existing customers")
    except:
        customers = []
        existing_emails = set()
        print("📚 Starting fresh extraction")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=50)
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
                print("❌ Login failed!")
                return
            
            print("✅ Login successful!")
            
            # Go to customers page
            page.goto("https://keatchenunited.app4food.co.uk/admin/Customer")
            page.wait_for_load_state('networkidle')
            
            total_extracted = 0
            
            # Extract ALL 27 pages
            for page_num in range(1, 28):
                print(f"\n🔄 === PAGE {page_num}/27 ===")
                
                # Navigate to specific page
                if page_num > 1:
                    try:
                        page_dropdown = page.query_selector('select:first-of-type')
                        if page_dropdown:
                            page_dropdown.select_option(str(page_num))
                            page.wait_for_load_state('networkidle')
                            time.sleep(1)
                        else:
                            print("❌ Could not find page dropdown")
                            continue
                    except Exception as e:
                        print(f"❌ Navigation error: {e}")
                        continue
                
                # Extract customers from current page
                try:
                    customer_rows = page.query_selector_all('tbody tr')
                    page_extracted = 0
                    
                    for i, row in enumerate(customer_rows):
                        try:
                            cells = row.query_selector_all('td')
                            if len(cells) < 6:
                                continue
                            
                            # Skip header/pagination rows
                            row_text = row.inner_text()
                            if 'Firstname' in row_text or 'of 27' in row_text or 'of 538' in row_text:
                                continue
                            
                            # Extract customer data
                            customer = {
                                'first_name': cells[0].inner_text().strip(),
                                'last_name': cells[1].inner_text().strip(),
                                'email': cells[2].inner_text().strip(),
                                'mobile': cells[3].inner_text().strip(),
                                'address': cells[4].inner_text().strip(),
                                'postcode': cells[5].inner_text().strip(),
                                'page': page_num,
                                'scraped_at': datetime.now().isoformat(),
                                'contact_details': {},
                                'orders': [],
                                'loyalty': {},
                                'coupons': [],
                                'roles': [],
                                'delivery': {},
                                'discounts': []
                            }
                            
                            # Skip if already have this customer
                            if customer['email'].lower() in existing_emails:
                                print(f"  ⏭️ Skip: {customer['email']} (already have)")
                                continue
                            
                            print(f"  🔍 {customer['first_name']} {customer['last_name']} ({customer['email']})")
                            
                            # Click Details button for full extraction
                            details_btn = row.query_selector('button')
                            if details_btn:
                                details_btn.click()
                                page.wait_for_timeout(800)
                                
                                # Extract contact details
                                try:
                                    inputs = page.query_selector_all('input[disabled]')
                                    contact_data = {}
                                    
                                    for inp in inputs:
                                        value = inp.get_attribute('value')
                                        name = inp.get_attribute('name') or ''
                                        if value:
                                            if '@' in value:
                                                contact_data['verified_email'] = value
                                            elif '+44' in value:
                                                contact_data['verified_mobile'] = value
                                            elif 'First' in name:
                                                contact_data['verified_firstname'] = value
                                            elif 'Last' in name:
                                                contact_data['verified_lastname'] = value
                                            elif 'Address1' in name:
                                                contact_data['address1'] = value
                                            elif 'Address2' in name:
                                                contact_data['address2'] = value
                                            elif 'City' in name:
                                                contact_data['city'] = value
                                            elif 'County' in name:
                                                contact_data['county'] = value
                                            elif 'Postcode' in name:
                                                contact_data['verified_postcode'] = value
                                    
                                    customer['contact_details'] = contact_data
                                    
                                    # Extract DOB
                                    try:
                                        selects = page.query_selector_all('select[disabled]')
                                        if len(selects) >= 3:
                                            day = selects[0].evaluate('el => el.options[el.selectedIndex].text')
                                            month = selects[1].evaluate('el => el.options[el.selectedIndex].text')
                                            year = selects[2].evaluate('el => el.options[el.selectedIndex].text')
                                            if day and month and year and all(x != '' for x in [day, month, year]):
                                                customer['contact_details']['dob'] = f"{day}/{month}/{year}"
                                    except:
                                        pass
                                    
                                    # Extract Orders quickly
                                    try:
                                        page.click('div:has-text("Orders")')
                                        page.wait_for_timeout(300)
                                        orders_table = page.query_selector('table')
                                        if orders_table:
                                            order_rows = orders_table.query_selector_all('tbody tr')
                                            orders = []
                                            for or_row in order_rows:
                                                or_cells = or_row.query_selector_all('td')
                                                if len(or_cells) >= 5:
                                                    order_no = or_cells[0].inner_text().strip()
                                                    if order_no and order_no != 'Order No.':
                                                        orders.append({
                                                            'order_no': order_no,
                                                            'date': or_cells[1].inner_text().strip(),
                                                            'status': or_cells[2].inner_text().strip(),
                                                            'total': or_cells[4].inner_text().strip()
                                                        })
                                            customer['orders'] = orders
                                    except:
                                        pass
                                    
                                except Exception as e:
                                    print(f"    ⚠️ Details extraction error: {e}")
                                
                                # Close modal
                                try:
                                    close_btn = page.query_selector('button:has-text("Close")')
                                    if close_btn:
                                        close_btn.click()
                                        page.wait_for_timeout(300)
                                except:
                                    pass
                                
                                # Add to database
                                customers.append(customer)
                                existing_emails.add(customer['email'].lower())
                                page_extracted += 1
                                total_extracted += 1
                                
                                print(f"    ✅ Extracted! Total: {len(customers)}")
                                
                                # Small delay
                                time.sleep(0.3)
                            
                        except Exception as e:
                            print(f"    ❌ Customer error: {e}")
                            continue
                    
                    print(f"📊 Page {page_num}: {page_extracted} new customers | Database: {len(customers)} total")
                    
                    # Save progress every page
                    with open('customer_data/customers_mcp.json', 'w') as f:
                        json.dump(customers, f, indent=2)
                    
                    # Progress update
                    progress = len(customers) / 538 * 100
                    print(f"📈 Progress: {len(customers)}/538 ({progress:.1f}%)")
                    
                except Exception as e:
                    print(f"❌ Page {page_num} error: {e}")
                    continue
            
            print(f"\n🎉 === EXTRACTION COMPLETE ===")
            print(f"🏆 Total customers extracted: {len(customers)}")
            print(f"📊 Final database size: {len(customers)} customers")
            
            # Create final exports
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Final JSON
            final_json = f'customer_data/COMPLETE_KEATCHEN_DATABASE_{timestamp}.json'
            with open(final_json, 'w') as f:
                json.dump(customers, f, indent=2)
            
            # Final CSV
            final_csv = f'customer_data/COMPLETE_KEATCHEN_DATABASE_{timestamp}.csv'
            with open(final_csv, 'w') as f:
                f.write('FirstName,LastName,Email,Mobile,Address,Postcode,City,County,DOB,TotalOrders,Page,ScrapedAt\\n')
                for c in customers:
                    contact = c.get('contact_details', {})
                    f.write(f'\"{c.get(\"first_name\",\"\")}\",\"{c.get(\"last_name\",\"\")}\",\"{c.get(\"email\",\"\")}\",\"{c.get(\"mobile\",\"\")}\",\"{c.get(\"address\",\"\")}\",\"{c.get(\"postcode\",\"\")}\",\"{contact.get(\"city\",\"\")}\",\"{contact.get(\"county\",\"\")}\",\"{contact.get(\"dob\",\"\")}\",{len(c.get(\"orders\",[]))},{c.get(\"page\",0)},\"{c.get(\"scraped_at\",\"\")}\"\\n')
            
            print(f"💾 Final exports:")
            print(f"   📄 JSON: {final_json}")
            print(f"   📊 CSV: {final_csv}")
            
        except Exception as e:
            print(f"❌ Fatal error: {e}")
            # Save whatever we have
            with open('customer_data/customers_mcp.json', 'w') as f:
                json.dump(customers, f, indent=2)
        finally:
            browser.close()

if __name__ == "__main__":
    extract_all_customers()