#!/usr/bin/env python3
"""
Extract ALL missing customers - headless mode with extended timeouts
"""

import json
import time
import os
import sqlite3
from datetime import datetime
from playwright.sync_api import sync_playwright

def extract_all_missing():
    print("🎯 EXTRACTING ALL REMAINING CUSTOMERS")
    print("=====================================")
    
    # Missing pages that we haven't extracted
    missing_pages = [14, 15, 16, 17, 18, 19, 21, 22, 23, 24]
    print(f"📋 Missing pages: {missing_pages}")
    print(f"📊 Estimated customers: ~{len(missing_pages) * 20}")
    
    # Database setup
    db_path = "/app/data/customers.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM customers WHERE is_active = TRUE")
    initial_count = cursor.fetchone()[0]
    print(f"📚 Starting with {initial_count} customers")
    conn.close()
    
    total_new = 0
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu']
        )
        
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        )
        
        page = context.new_page()
        page.set_default_timeout(60000)  # 60 second timeout
        
        try:
            # Login
            print("🔐 Logging in...")
            page.goto("https://keatchenunited.app4food.co.uk/admin/Account/Login", wait_until='networkidle')
            
            page.fill('input[placeholder*="email"]', "admin@keatchen")
            page.fill('input[type="password"]', "keatchen22")
            page.click('button:has-text("Log In")')
            page.wait_for_load_state('networkidle')
            
            if not page.query_selector('a:has-text("Logout")'):
                print("❌ Login failed")
                return
            
            print("✅ Login successful")
            
            # Navigate to customers
            page.goto("https://keatchenunited.app4food.co.uk/admin/Customer", wait_until='networkidle')
            
            # Extract each missing page
            for page_num in missing_pages:
                print(f"\\n📄 === PAGE {page_num}/{max(missing_pages)} ===")
                
                try:
                    # Navigate to page
                    dropdown = page.query_selector('select:first-of-type')
                    if dropdown:
                        dropdown.select_option(str(page_num))
                        page.wait_for_load_state('networkidle')
                        time.sleep(3)  # Extended wait
                    
                    # Extract customers
                    rows = page.query_selector_all('tbody tr')
                    page_new = 0
                    
                    for row in rows:
                        try:
                            cells = row.query_selector_all('td')
                            if len(cells) < 6:
                                continue
                            
                            text = row.inner_text()
                            if 'Firstname' in text or 'of 27' in text:
                                continue
                            
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
                            
                            # Add to database
                            conn = sqlite3.connect(db_path)
                            cursor = conn.cursor()
                            
                            cursor.execute('''
                                INSERT OR IGNORE INTO customers (
                                    email, first_name, last_name, mobile, address,
                                    postcode, page, first_seen, last_updated, is_active
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (
                                customer['email'], customer['first_name'], customer['last_name'],
                                customer['mobile'], customer['address'], customer['postcode'],
                                customer['page'], customer['extracted_at'], customer['extracted_at'], True
                            ))
                            
                            conn.commit()
                            conn.close()
                            
                            page_new += 1
                            total_new += 1
                            
                            print(f"    ✅ {customer['first_name']} {customer['last_name']}")
                            
                        except Exception as e:
                            continue
                    
                    print(f"📊 Page {page_num}: {page_new} customers | Total new: {total_new}")
                    
                except Exception as e:
                    print(f"❌ Page {page_num} failed: {e}")
                    continue
            
            # Final database count
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM customers WHERE is_active = TRUE")
            final_count = cursor.fetchone()[0]
            conn.close()
            
            print(f"\\n🎉 === FINAL RESULTS ===")
            print(f"🏆 Total customers: {final_count}")
            print(f"📈 Added: {final_count - initial_count} new customers")
            print(f"📊 Completion: {final_count/538*100:.1f}%")
            
            if final_count >= 500:
                print("🎉 SUCCESS: Nearly complete customer database!")
            else:
                print(f"⚠️ Partial: {538 - final_count} customers still missing")
                
        except Exception as e:
            print(f"❌ Extraction error: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    extract_all_missing()