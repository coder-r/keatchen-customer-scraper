#!/usr/bin/env python3
"""
Complete extraction of ALL remaining customers
This script will run on the remote host to get the missing ~200 customers
"""

import json
import time
import os
import sqlite3
from datetime import datetime
from playwright.sync_api import sync_playwright

def get_missing_pages():
    """Identify which pages we haven't extracted yet"""
    # We extracted: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 20, 25, 26, 27]
    extracted_pages = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 20, 25, 26, 27}
    all_pages = set(range(1, 28))
    missing_pages = all_pages - extracted_pages
    return sorted(missing_pages)

def extract_missing_customers():
    """Extract customers from missing pages only"""
    print("🎯 EXTRACTING ALL REMAINING CUSTOMERS")
    print("=====================================")
    
    missing_pages = get_missing_pages()
    print(f"📋 Missing pages: {missing_pages}")
    print(f"📊 Estimated missing customers: ~{len(missing_pages) * 20}")
    
    # Connect to existing database
    db_path = "data/customers.db"
    
    if not os.path.exists(db_path):
        print("❌ Database not found!")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get current count
    cursor.execute("SELECT COUNT(*) FROM customers WHERE is_active = TRUE")
    initial_count = cursor.fetchone()[0]
    print(f"📚 Starting with {initial_count} customers")
    
    conn.close()
    
    new_customers = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=100)  # Visible for reliability
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
            
            total_extracted = 0
            
            # Extract ONLY missing pages
            for page_num in missing_pages:
                print(f"\\n🔍 === EXTRACTING PAGE {page_num} ===")
                
                try:
                    # Navigate to specific page
                    dropdown = page.query_selector('select:first-of-type')
                    if dropdown:
                        dropdown.select_option(str(page_num))
                        page.wait_for_load_state('networkidle')
                        time.sleep(2)  # Extra wait time
                    
                    # Extract customers from this page
                    customer_rows = page.query_selector_all('tbody tr')
                    page_extracted = 0
                    
                    for row in customer_rows:
                        try:
                            cells = row.query_selector_all('td')
                            if len(cells) < 6:
                                continue
                            
                            # Skip header/pagination
                            row_text = row.inner_text()
                            if 'Firstname' in row_text or 'of 27' in row_text:
                                continue
                            
                            # Extract customer
                            customer = {
                                'first_name': cells[0].inner_text().strip(),
                                'last_name': cells[1].inner_text().strip(),
                                'email': cells[2].inner_text().strip(),
                                'mobile': cells[3].inner_text().strip(),
                                'address': cells[4].inner_text().strip(),
                                'postcode': cells[5].inner_text().strip(),
                                'page': page_num,
                                'extracted_at': datetime.now().isoformat()
                            }
                            
                            print(f"  📝 {customer['first_name']} {customer['last_name']} ({customer['email']})")
                            
                            # Add to database immediately
                            conn = sqlite3.connect(db_path)
                            cursor = conn.cursor()
                            
                            cursor.execute('''
                                INSERT OR REPLACE INTO customers (
                                    email, first_name, last_name, mobile, address, 
                                    postcode, page, first_seen, last_updated, is_active
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (
                                customer['email'],
                                customer['first_name'],
                                customer['last_name'],
                                customer['mobile'],
                                customer['address'],
                                customer['postcode'],
                                customer['page'],
                                customer['extracted_at'],
                                customer['extracted_at'],
                                True
                            ))
                            
                            conn.commit()
                            conn.close()
                            
                            new_customers.append(customer)
                            page_extracted += 1
                            total_extracted += 1
                            
                        except Exception as e:
                            print(f"    ❌ Customer error: {e}")
                            continue
                    
                    print(f"✅ Page {page_num}: {page_extracted} customers extracted")
                    
                except Exception as e:
                    print(f"❌ Page {page_num} error: {e}")
                    continue
            
            print(f"\\n🎉 === EXTRACTION COMPLETE ===")
            print(f"🏆 New customers extracted: {total_extracted}")
            
            # Check final database count
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM customers WHERE is_active = TRUE")
            final_count = cursor.fetchone()[0]
            conn.close()
            
            print(f"📊 Database: {initial_count} → {final_count} customers")
            print(f"📈 Growth: +{final_count - initial_count} customers")
            print(f"📄 Target: 538 customers")
            print(f"📈 Completion: {final_count/538*100:.1f}%")
            
        except Exception as e:
            print(f"❌ Fatal error: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    extract_missing_customers()