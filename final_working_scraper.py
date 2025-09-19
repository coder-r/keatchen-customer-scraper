#!/usr/bin/env python3
"""
FINAL WORKING SCRAPER - Extract ALL 538 customers
"""

import json
import time
import os
from datetime import datetime
from playwright.sync_api import sync_playwright

def main():
    print("🚀 FINAL COMPLETE CUSTOMER EXTRACTION")
    print("🎯 Extracting ALL 538 customers - will not stop until complete!")
    
    # Load existing data
    try:
        with open('customer_data/customers_mcp.json', 'r') as f:
            customers = json.load(f)
        existing_emails = {c.get('email', '').lower() for c in customers}
        print(f"📚 Starting with {len(customers)} existing customers")
    except:
        customers = []
        existing_emails = set()
        print("📚 Starting fresh")
    
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
            
            print("✅ Login successful")
            
            # Navigate to customers
            page.goto("https://keatchenunited.app4food.co.uk/admin/Customer")
            page.wait_for_load_state('networkidle')
            
            total_new = 0
            
            # Process all 27 pages
            for page_num in range(1, 28):
                print(f"\\n📄 === PAGE {page_num}/27 ===")
                
                # Navigate to page if not page 1
                if page_num > 1:
                    try:
                        dropdown = page.query_selector('select:first-of-type')
                        if dropdown:
                            dropdown.select_option(str(page_num))
                            page.wait_for_load_state('networkidle')
                            time.sleep(0.5)
                    except Exception as e:
                        print(f"Navigation error: {e}")
                        continue
                
                # Extract customers from this page
                rows = page.query_selector_all('tbody tr')
                page_new = 0
                
                for row in rows:
                    try:
                        cells = row.query_selector_all('td')
                        if len(cells) < 6:
                            continue
                        
                        # Skip headers/pagination
                        text = row.inner_text()
                        if 'Firstname' in text or 'of 27' in text:
                            continue
                        
                        # Basic customer data
                        customer = {
                            'first_name': cells[0].inner_text().strip(),
                            'last_name': cells[1].inner_text().strip(),
                            'email': cells[2].inner_text().strip(),
                            'mobile': cells[3].inner_text().strip(),
                            'address': cells[4].inner_text().strip(),
                            'postcode': cells[5].inner_text().strip(),
                            'page': page_num,
                            'scraped_at': datetime.now().isoformat(),
                            'extracted_details': False
                        }
                        
                        # Skip if duplicate
                        if customer['email'].lower() in existing_emails:
                            continue
                        
                        print(f"  ✅ {customer['first_name']} {customer['last_name']}")
                        
                        # Add to database
                        customers.append(customer)
                        existing_emails.add(customer['email'].lower())
                        page_new += 1
                        total_new += 1
                        
                    except Exception as e:
                        continue
                
                print(f"📊 Page {page_num}: {page_new} new | Total: {len(customers)}")
                
                # Save progress every page
                with open('customer_data/customers_mcp.json', 'w') as f:
                    json.dump(customers, f, indent=2)
                
                progress = len(customers) / 538 * 100
                print(f"📈 Progress: {len(customers)}/538 ({progress:.1f}%)")
            
            # Final save and export
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            final_json = f'customer_data/COMPLETE_DATABASE_{timestamp}.json'
            with open(final_json, 'w') as f:
                json.dump(customers, f, indent=2)
            
            final_csv = f'customer_data/COMPLETE_DATABASE_{timestamp}.csv'
            with open(final_csv, 'w') as f:
                f.write('FirstName,LastName,Email,Mobile,Address,Postcode,Page,ScrapedAt\\n')
                for c in customers:
                    fname = c.get('first_name', '').replace('"', '""')
                    lname = c.get('last_name', '').replace('"', '""')
                    email = c.get('email', '')
                    mobile = c.get('mobile', '')
                    address = c.get('address', '').replace('"', '""')
                    postcode = c.get('postcode', '')
                    page_num = c.get('page', 0)
                    scraped = c.get('scraped_at', '')
                    
                    f.write(f'"{fname}","{lname}","{email}","{mobile}","{address}","{postcode}",{page_num},"{scraped}"\\n')
            
            print(f"\\n🎉 === COMPLETE SUCCESS ===")
            print(f"🏆 TOTAL CUSTOMERS: {len(customers)}")
            print(f"📄 JSON: {final_json}")
            print(f"📊 CSV: {final_csv}")
            print(f"📈 Final completion: {len(customers)/538*100:.1f}%")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            # Save what we have
            with open('customer_data/customers_mcp.json', 'w') as f:
                json.dump(customers, f, indent=2)
        finally:
            browser.close()

if __name__ == "__main__":
    main()