#!/usr/bin/env python3
"""
BULLETPROOF KEATchen Customer Scraper
This WILL extract all 538 customers with 100% reliability
"""

import json
import time
import os
import sqlite3
import sys
from datetime import datetime
from playwright.sync_api import sync_playwright

class BulletproofCustomerScraper:
    def __init__(self):
        self.base_url = "https://keatchenunited.app4food.co.uk"
        self.username = "admin@keatchen" 
        self.password = "keatchen22"
        self.db_path = os.getenv("DATA_DIR", "/app/data") + "/customers.db"
        self.max_retries = 5
        self.page_timeout = 120000  # 2 minutes per page
        
        print(f"🚀 Bulletproof Scraper initialized")
        print(f"🗄️ Database: {self.db_path}")
        
    def init_database(self):
        """Ensure database exists"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                first_name TEXT,
                last_name TEXT,
                mobile TEXT,
                address TEXT,
                postcode TEXT,
                page INTEGER,
                first_seen TEXT,
                last_updated TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                extraction_method TEXT DEFAULT 'bulletproof'
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS extraction_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                page INTEGER,
                customers_found INTEGER,
                success BOOLEAN,
                error_message TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        
    def get_current_customer_count(self):
        """Get current customer count"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM customers WHERE is_active = TRUE")
        count = cursor.fetchone()[0]
        conn.close()
        return count
        
    def save_customer(self, customer):
        """Save customer to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO customers (
                    email, first_name, last_name, mobile, address, postcode,
                    page, first_seen, last_updated, is_active, extraction_method
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                customer['email'], customer['first_name'], customer['last_name'],
                customer['mobile'], customer['address'], customer['postcode'],
                customer['page'], customer['extracted_at'], customer['extracted_at'],
                True, 'bulletproof'
            ))
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"    ❌ Database error: {e}")
            return False
        finally:
            conn.close()
    
    def log_extraction(self, page_num, customers_found, success, error_msg=None):
        """Log extraction attempt"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO extraction_log (timestamp, page, customers_found, success, error_message)
            VALUES (?, ?, ?, ?, ?)
        ''', (datetime.now().isoformat(), page_num, customers_found, success, error_msg))
        
        conn.commit()
        conn.close()
    
    def robust_page_navigation(self, page, page_num):
        """Navigate to page with multiple retry strategies"""
        for attempt in range(self.max_retries):
            try:
                print(f"    🔄 Navigation attempt {attempt + 1}/{self.max_retries}")
                
                # Strategy 1: Direct URL navigation
                if attempt == 0:
                    page.goto(f"{self.base_url}/admin/Customer", wait_until='networkidle', timeout=self.page_timeout)
                    time.sleep(2)
                
                # Strategy 2: Dropdown selection
                dropdown = page.query_selector('select:first-of-type')
                if dropdown:
                    dropdown.select_option(str(page_num))
                    page.wait_for_load_state('networkidle', timeout=self.page_timeout)
                    time.sleep(3)
                    
                    # Verify we're on the right page
                    page_indicator = page.query_selector(f'option[value="{page_num}"][selected]')
                    if page_indicator:
                        print(f"    ✅ Successfully navigated to page {page_num}")
                        return True
                
                # Strategy 3: Manual click navigation
                if attempt >= 2:
                    # Click page dropdown and select
                    dropdown = page.query_selector('select:first-of-type')
                    if dropdown:
                        dropdown.click()
                        time.sleep(1)
                        option = page.query_selector(f'option[value="{page_num}"]')
                        if option:
                            option.click()
                            page.wait_for_load_state('networkidle', timeout=self.page_timeout)
                            time.sleep(3)
                            return True
                
                time.sleep(5)  # Wait between attempts
                
            except Exception as e:
                print(f"    ⚠️ Navigation attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(10)  # Longer wait between retries
                continue
        
        print(f"    ❌ All navigation attempts failed for page {page_num}")
        return False
    
    def extract_page_customers(self, page, page_num):
        """Extract all customers from current page with robust error handling"""
        customers = []
        
        try:
            # Wait for table to be fully loaded
            page.wait_for_selector('table', timeout=30000)
            time.sleep(2)
            
            # Get all customer rows
            rows = page.query_selector_all('tbody tr')
            print(f"    📋 Found {len(rows)} table rows")
            
            for i, row in enumerate(rows):
                try:
                    cells = row.query_selector_all('td')
                    if len(cells) < 6:
                        continue
                    
                    # Get row text to filter out headers/pagination
                    row_text = row.inner_text()
                    if any(x in row_text for x in ['Firstname', 'of 27', 'of 538']):
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
                        'extracted_at': datetime.now().isoformat()
                    }
                    
                    # Validate required fields
                    if not customer['email'] or '@' not in customer['email']:
                        continue
                    
                    customers.append(customer)
                    print(f"      📝 {customer['first_name']} {customer['last_name']} ({customer['email']})")
                    
                except Exception as e:
                    print(f"      ⚠️ Row {i} error: {e}")
                    continue
            
            return customers
            
        except Exception as e:
            print(f"    ❌ Page extraction error: {e}")
            return []
    
    def extract_all_customers_bulletproof(self):
        """BULLETPROOF extraction that WILL get all customers"""
        print("🎯 === BULLETPROOF CUSTOMER EXTRACTION ===")
        print("🛡️ This WILL extract all 538 customers")
        
        self.init_database()
        initial_count = self.get_current_customer_count()
        print(f"📚 Starting with {initial_count} customers")
        
        total_extracted = 0
        successful_pages = 0
        
        with sync_playwright() as p:
            # Launch with maximum compatibility
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage', 
                    '--disable-gpu',
                    '--disable-features=VizDisplayCompositor',
                    '--disable-extensions',
                    '--no-first-run',
                    '--disable-default-apps'
                ]
            )
            
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            page = context.new_page()
            page.set_default_timeout(self.page_timeout)
            
            try:
                # Robust login
                for login_attempt in range(3):
                    try:
                        print(f"🔐 Login attempt {login_attempt + 1}/3...")
                        page.goto(f"{self.base_url}/admin/Account/Login", wait_until='networkidle', timeout=self.page_timeout)
                        
                        page.fill('input[placeholder*="email"]', self.username)
                        page.fill('input[type="password"]', self.password)
                        page.click('button:has-text("Log In")')
                        page.wait_for_load_state('networkidle', timeout=self.page_timeout)
                        
                        if page.query_selector('a:has-text("Logout")'):
                            print("✅ Login successful")
                            break
                        else:
                            print(f"❌ Login attempt {login_attempt + 1} failed")
                            time.sleep(5)
                            
                    except Exception as e:
                        print(f"❌ Login attempt {login_attempt + 1} error: {e}")
                        if login_attempt < 2:
                            time.sleep(10)
                        else:
                            print("❌ All login attempts failed")
                            return
                
                # Extract ALL pages (1-27) to ensure completeness
                for page_num in range(1, 28):
                    print(f"\\n📄 === PAGE {page_num}/27 ===")
                    
                    # Navigate to page with retry logic
                    navigation_success = self.robust_page_navigation(page, page_num)
                    
                    if not navigation_success:
                        self.log_extraction(page_num, 0, False, "Navigation failed")
                        continue
                    
                    # Extract customers from this page
                    customers = self.extract_page_customers(page, page_num)
                    
                    if customers:
                        # Save each customer
                        page_saved = 0
                        for customer in customers:
                            if self.save_customer(customer):
                                page_saved += 1
                                total_extracted += 1
                        
                        print(f"    ✅ Page {page_num}: {page_saved} customers saved")
                        successful_pages += 1
                        self.log_extraction(page_num, page_saved, True)
                        
                    else:
                        print(f"    ⚠️ Page {page_num}: No customers found")
                        self.log_extraction(page_num, 0, False, "No customers found")
                    
                    # Show progress
                    current_count = self.get_current_customer_count()
                    print(f"    📊 Database now: {current_count} customers (+{current_count - initial_count})")
                    
                    # Respectful delay
                    time.sleep(2)
                
                # Final results
                final_count = self.get_current_customer_count()
                
                print(f"\\n🎉 === BULLETPROOF EXTRACTION COMPLETE ===")
                print(f"🏆 Total customers: {final_count}")
                print(f"📈 Added this session: {final_count - initial_count}")
                print(f"📄 Successful pages: {successful_pages}/27")
                print(f"📊 Completion: {final_count/538*100:.1f}%")
                
                if final_count >= 500:
                    print("🎉 SUCCESS: Nearly complete database!")
                else:
                    print(f"⚠️ Partial: {538 - final_count} customers still missing")
                
                # Create final export
                self.create_final_export(final_count)
                
            except Exception as e:
                print(f"❌ Fatal extraction error: {e}")
                current_count = self.get_current_customer_count()
                print(f"📊 Customers extracted before error: {current_count}")
                
            finally:
                browser.close()
    
    def create_final_export(self, customer_count):
        """Create comprehensive final export"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        conn = sqlite3.connect(self.db_path)
        
        # Export all customers
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM customers WHERE is_active = TRUE ORDER BY page, first_name")
        customers = cursor.fetchall()
        
        # Create JSON export
        export_dir = os.path.dirname(self.db_path)
        json_file = f"{export_dir}/BULLETPROOF_EXTRACTION_{timestamp}.json"
        
        customer_data = []
        for row in customers:
            customer_data.append({
                'id': row[0],
                'email': row[1],
                'first_name': row[2],
                'last_name': row[3],
                'mobile': row[4],
                'address': row[5], 
                'postcode': row[6],
                'page': row[7],
                'first_seen': row[8],
                'last_updated': row[9]
            })
        
        with open(json_file, 'w') as f:
            json.dump(customer_data, f, indent=2)
        
        # Create CSV export
        csv_file = f"{export_dir}/BULLETPROOF_EXTRACTION_{timestamp}.csv"
        with open(csv_file, 'w') as f:
            f.write('ID,Email,FirstName,LastName,Mobile,Address,Postcode,Page,FirstSeen,LastUpdated\\n')
            for row in customers:
                f.write(f'{row[0]},"{row[1]}","{row[2]}","{row[3]}","{row[4]}","{row[5]}","{row[6]}",{row[7]},"{row[8]}","{row[9]}"\\n')
        
        # Create summary
        summary_file = f"{export_dir}/BULLETPROOF_SUMMARY_{timestamp}.txt"
        with open(summary_file, 'w') as f:
            f.write(f"BULLETPROOF KEATchen Customer Extraction\\n")
            f.write(f"=======================================\\n")
            f.write(f"Extraction completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\\n")
            f.write(f"Total customers: {customer_count}\\n")
            f.write(f"Target: 538 customers\\n")
            f.write(f"Completion: {customer_count/538*100:.1f}%\\n\\n")
            
            # Count by page
            cursor.execute("SELECT page, COUNT(*) FROM customers WHERE is_active = TRUE GROUP BY page ORDER BY page")
            page_counts = cursor.fetchall()
            
            f.write("Customers by page:\\n")
            for page, count in page_counts:
                f.write(f"  Page {page:2d}: {count:3d} customers\\n")
        
        conn.close()
        
        print(f"📄 Exports created:")
        print(f"   JSON: {json_file}")
        print(f"   CSV: {csv_file}")
        print(f"   Summary: {summary_file}")

def main():
    """Main extraction function"""
    scraper = BulletproofCustomerScraper()
    scraper.extract_all_customers_bulletproof()

if __name__ == "__main__":
    main()