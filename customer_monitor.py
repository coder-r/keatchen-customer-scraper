#!/usr/bin/env python3
"""
KEATchen Customer Monitor - Production Service
Monitors for new customers and maintains incremental database
"""

import json
import time
import os
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Set, Optional
from playwright.sync_api import sync_playwright
import schedule
from dotenv import load_dotenv
import pandas as pd

# Load environment variables
load_dotenv()

class KEATchenCustomerMonitor:
    def __init__(self):
        # Configuration
        self.base_url = os.getenv("KEATCHEN_URL", "https://keatchenunited.app4food.co.uk")
        self.username = os.getenv("KEATCHEN_USERNAME", "admin@keatchen")
        self.password = os.getenv("KEATCHEN_PASSWORD", "keatchen22")
        self.data_dir = os.getenv("DATA_DIR", "/app/data")
        self.headless = os.getenv("HEADLESS", "true").lower() == "true"
        
        # Ensure data directory exists
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs("logs", exist_ok=True)
        
        # Setup logging
        logging.basicConfig(
            level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/customer_monitor.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Initialize database
        self.init_database()
        
        self.logger.info("🚀 KEATchen Customer Monitor initialized")
    
    def init_database(self):
        """Initialize SQLite database for tracking customers"""
        self.db_path = os.path.join(self.data_dir, "customers.db")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create customers table
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
                verified_email TEXT,
                verified_mobile TEXT,
                dob TEXT,
                city TEXT,
                county TEXT,
                total_orders INTEGER DEFAULT 0,
                has_loyalty BOOLEAN DEFAULT FALSE,
                has_coupons BOOLEAN DEFAULT FALSE,
                is_active BOOLEAN DEFAULT TRUE
            )
        ''')
        
        # Create monitoring log table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS monitoring_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                action TEXT,
                customers_found INTEGER,
                new_customers INTEGER,
                updated_customers INTEGER,
                errors INTEGER,
                execution_time REAL
            )
        ''')
        
        # Create new_customers table for notifications
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS new_customers_today (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT,
                first_name TEXT,
                last_name TEXT,
                mobile TEXT,
                detected_at TEXT,
                notified BOOLEAN DEFAULT FALSE
            )
        ''')
        
        conn.commit()
        conn.close()
        
        self.logger.info("✅ Database initialized")
    
    def login(self, page) -> bool:
        """Login to KEATchen admin"""
        try:
            self.logger.info("🔐 Logging in...")
            page.goto(f"{self.base_url}/admin/Account/Login")
            page.wait_for_load_state('networkidle')
            
            page.fill('input[placeholder*="email"]', self.username)
            page.fill('input[type="password"]', self.password)
            page.click('button:has-text("Log In")')
            page.wait_for_load_state('networkidle')
            
            if page.query_selector('a:has-text("Logout")'):
                self.logger.info("✅ Login successful")
                return True
            else:
                self.logger.error("❌ Login failed")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Login error: {e}")
            return False
    
    def extract_customer_from_modal(self, page, basic_customer: Dict) -> Dict:
        """Extract detailed customer data from modal"""
        customer = basic_customer.copy()
        
        try:
            # Wait for modal
            page.wait_for_selector('[id*="modal"]', timeout=3000)
            time.sleep(0.5)
            
            # Extract contact details
            contact_details = {}
            
            # Get form fields
            inputs = page.query_selector_all('input[disabled]')
            for inp in inputs:
                value = inp.get_attribute('value')
                name = inp.get_attribute('name') or ''
                
                if value:
                    if '@' in value:
                        contact_details['verified_email'] = value
                    elif '+44' in value:
                        contact_details['verified_mobile'] = value
                    elif 'First' in name:
                        contact_details['verified_firstname'] = value
                    elif 'Last' in name:
                        contact_details['verified_lastname'] = value
                    elif 'City' in name:
                        contact_details['city'] = value
                    elif 'County' in name:
                        contact_details['county'] = value
            
            # Extract DOB
            try:
                selects = page.query_selector_all('select[disabled]')
                if len(selects) >= 3:
                    day = selects[0].evaluate('el => el.options[el.selectedIndex].text')
                    month = selects[1].evaluate('el => el.options[el.selectedIndex].text')
                    year = selects[2].evaluate('el => el.options[el.selectedIndex].text')
                    if all(x and x != '' for x in [day, month, year]):
                        contact_details['dob'] = f"{day}/{month}/{year}"
            except:
                pass
            
            # Extract orders
            orders = []
            try:
                page.click('div:has-text("Orders")')
                time.sleep(0.3)
                orders_table = page.query_selector('table')
                if orders_table:
                    order_rows = orders_table.query_selector_all('tbody tr')
                    for row in order_rows:
                        cells = row.query_selector_all('td')
                        if len(cells) >= 5:
                            order_no = cells[0].inner_text().strip()
                            if order_no and order_no != 'Order No.':
                                orders.append({
                                    'order_no': order_no,
                                    'date': cells[1].inner_text().strip(),
                                    'total': cells[4].inner_text().strip()
                                })
            except:
                pass
            
            customer.update({
                'contact_details': contact_details,
                'orders': orders,
                'total_orders': len(orders),
                'has_loyalty': False,  # Will be extracted later
                'has_coupons': False   # Will be extracted later
            })
            
        except Exception as e:
            self.logger.warning(f"Modal extraction error: {e}")
        
        return customer
    
    def get_existing_customers(self) -> Set[str]:
        """Get set of existing customer emails from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT email FROM customers WHERE is_active = TRUE")
        existing_emails = {row[0].lower() for row in cursor.fetchall()}
        
        conn.close()
        return existing_emails
    
    def save_customer_to_db(self, customer: Dict, is_new: bool = False):
        """Save customer to SQLite database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            contact = customer.get('contact_details', {})
            
            if is_new:
                # Insert new customer
                cursor.execute('''
                    INSERT OR REPLACE INTO customers (
                        email, first_name, last_name, mobile, address, postcode,
                        page, first_seen, last_updated, verified_email, verified_mobile,
                        dob, city, county, total_orders, has_loyalty, has_coupons
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    customer.get('email', ''),
                    customer.get('first_name', ''),
                    customer.get('last_name', ''),
                    customer.get('mobile', ''),
                    customer.get('address', ''),
                    customer.get('postcode', ''),
                    customer.get('page', 0),
                    customer.get('scraped_at', ''),
                    customer.get('scraped_at', ''),
                    contact.get('verified_email', ''),
                    contact.get('verified_mobile', ''),
                    contact.get('dob', ''),
                    contact.get('city', ''),
                    contact.get('county', ''),
                    customer.get('total_orders', 0),
                    customer.get('has_loyalty', False),
                    customer.get('has_coupons', False)
                ))
                
                # Add to new customers notification list
                cursor.execute('''
                    INSERT INTO new_customers_today (email, first_name, last_name, mobile, detected_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    customer.get('email', ''),
                    customer.get('first_name', ''),
                    customer.get('last_name', ''),
                    customer.get('mobile', ''),
                    datetime.now().isoformat()
                ))
                
            else:
                # Update existing customer
                cursor.execute('''
                    UPDATE customers SET
                        last_updated = ?, total_orders = ?, has_loyalty = ?, has_coupons = ?
                    WHERE email = ?
                ''', (
                    customer.get('scraped_at', ''),
                    customer.get('total_orders', 0),
                    customer.get('has_loyalty', False),
                    customer.get('has_coupons', False),
                    customer.get('email', '')
                ))
            
            conn.commit()
            
        except Exception as e:
            self.logger.error(f"Database save error: {e}")
        finally:
            conn.close()
    
    def scan_for_new_customers(self) -> Dict:
        """Scan all pages for new customers"""
        start_time = time.time()
        stats = {
            'customers_found': 0,
            'new_customers': 0,
            'updated_customers': 0,
            'errors': 0
        }
        
        existing_emails = self.get_existing_customers()
        self.logger.info(f"📚 Starting scan. {len(existing_emails)} existing customers in database")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            page = browser.new_page()
            
            try:
                # Login
                if not self.login(page):
                    stats['errors'] += 1
                    return stats
                
                # Navigate to customers
                page.goto(f"{self.base_url}/admin/Customer")
                page.wait_for_load_state('networkidle')
                
                # Scan all 27 pages
                for page_num in range(1, 28):
                    self.logger.info(f"🔍 Scanning page {page_num}/27")
                    
                    # Navigate to page
                    if page_num > 1:
                        try:
                            dropdown = page.query_selector('select:first-of-type')
                            if dropdown:
                                dropdown.select_option(str(page_num))
                                page.wait_for_load_state('networkidle')
                                time.sleep(0.5)
                        except Exception as e:
                            self.logger.error(f"Navigation error page {page_num}: {e}")
                            stats['errors'] += 1
                            continue
                    
                    # Extract customers from current page
                    try:
                        customer_rows = page.query_selector_all('tbody tr')
                        
                        for row in customer_rows:
                            try:
                                cells = row.query_selector_all('td')
                                if len(cells) < 6:
                                    continue
                                
                                # Skip header/pagination rows
                                row_text = row.inner_text()
                                if 'Firstname' in row_text or 'of 27' in row_text:
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
                                    'scraped_at': datetime.now().isoformat()
                                }
                                
                                stats['customers_found'] += 1
                                
                                # Check if this is a new customer
                                if customer['email'].lower() not in existing_emails:
                                    self.logger.info(f"🆕 NEW CUSTOMER: {customer['first_name']} {customer['last_name']} ({customer['email']})")
                                    
                                    # Click Details for full extraction
                                    details_btn = row.query_selector('button')
                                    if details_btn:
                                        details_btn.click()
                                        time.sleep(0.8)
                                        
                                        # Extract detailed data
                                        customer = self.extract_customer_from_modal(page, customer)
                                        
                                        # Close modal
                                        close_btn = page.query_selector('button:has-text("Close")')
                                        if close_btn:
                                            close_btn.click()
                                            time.sleep(0.3)
                                    
                                    # Save new customer
                                    self.save_customer_to_db(customer, is_new=True)
                                    existing_emails.add(customer['email'].lower())
                                    stats['new_customers'] += 1
                                    
                                else:
                                    # Existing customer - quick update check
                                    stats['updated_customers'] += 1
                                
                            except Exception as e:
                                self.logger.error(f"Customer processing error: {e}")
                                stats['errors'] += 1
                                continue
                        
                        self.logger.info(f"✅ Page {page_num}: {stats['customers_found']} total, {stats['new_customers']} new")
                        
                    except Exception as e:
                        self.logger.error(f"Page {page_num} scanning error: {e}")
                        stats['errors'] += 1
                        continue
                
                execution_time = time.time() - start_time
                self.logger.info(f"🎉 Scan complete in {execution_time:.1f}s")
                
                # Log scan results
                self.log_scan_results(stats, execution_time)
                
            except Exception as e:
                self.logger.error(f"❌ Fatal scan error: {e}")
                stats['errors'] += 1
            finally:
                browser.close()
        
        return stats
    
    def log_scan_results(self, stats: Dict, execution_time: float):
        """Log scan results to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO monitoring_log (
                timestamp, action, customers_found, new_customers, 
                updated_customers, errors, execution_time
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            'full_scan',
            stats['customers_found'],
            stats['new_customers'],
            stats['updated_customers'],
            stats['errors'],
            execution_time
        ))
        
        conn.commit()
        conn.close()
    
    def get_new_customers_today(self) -> List[Dict]:
        """Get list of new customers detected today"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute('''
            SELECT email, first_name, last_name, mobile, detected_at
            FROM new_customers_today
            WHERE date(detected_at) = ? AND notified = FALSE
        ''', (today,))
        
        new_customers = []
        for row in cursor.fetchall():
            new_customers.append({
                'email': row[0],
                'first_name': row[1],
                'last_name': row[2],
                'mobile': row[3],
                'detected_at': row[4]
            })
        
        conn.close()
        return new_customers
    
    def export_current_database(self):
        """Export current database to JSON and CSV"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        conn = sqlite3.connect(self.db_path)
        
        # Export to JSON
        df = pd.read_sql_query("SELECT * FROM customers WHERE is_active = TRUE", conn)
        
        json_file = os.path.join(self.data_dir, f"customers_export_{timestamp}.json")
        df.to_json(json_file, orient='records', indent=2)
        
        # Export to CSV
        csv_file = os.path.join(self.data_dir, f"customers_export_{timestamp}.csv")
        df.to_csv(csv_file, index=False)
        
        # Create summary
        summary_file = os.path.join(self.data_dir, f"database_summary_{timestamp}.txt")
        with open(summary_file, 'w') as f:
            f.write(f"KEATchen Customer Database Export\\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\\n")
            f.write(f"Total active customers: {len(df)}\\n\\n")
            
            # Recent activity
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COUNT(*) FROM new_customers_today 
                WHERE date(detected_at) = date('now')
            ''')
            today_new = cursor.fetchone()[0]
            
            cursor.execute('''
                SELECT COUNT(*) FROM new_customers_today 
                WHERE date(detected_at) >= date('now', '-7 days')
            ''')
            week_new = cursor.fetchone()[0]
            
            f.write(f"New customers today: {today_new}\\n")
            f.write(f"New customers this week: {week_new}\\n")
        
        conn.close()
        
        self.logger.info(f"📄 Database exported: {len(df)} customers")
        self.logger.info(f"   JSON: {json_file}")
        self.logger.info(f"   CSV: {csv_file}")
        
        return json_file, csv_file, summary_file
    
    def generate_new_customer_report(self) -> str:
        """Generate report of new customers detected"""
        new_customers = self.get_new_customers_today()
        
        if not new_customers:
            return "✅ No new customers detected today"
        
        report = f"🆕 NEW CUSTOMERS DETECTED: {len(new_customers)}\\n"
        report += "=" * 50 + "\\n"
        
        for i, customer in enumerate(new_customers, 1):
            report += f"{i:2d}. {customer['first_name']} {customer['last_name']}\\n"
            report += f"    📧 {customer['email']}\\n"
            report += f"    📱 {customer['mobile']}\\n"
            report += f"    🕒 Detected: {customer['detected_at']}\\n\\n"
        
        # Mark as notified
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE new_customers_today SET notified = TRUE WHERE notified = FALSE")
        conn.commit()
        conn.close()
        
        return report
    
    def run_monitoring_cycle(self):
        """Run one complete monitoring cycle"""
        self.logger.info("🔄 Starting monitoring cycle...")
        
        try:
            # Scan for new customers
            stats = self.scan_for_new_customers()
            
            # Generate reports
            if stats['new_customers'] > 0:
                report = self.generate_new_customer_report()
                self.logger.info(f"📢 NEW CUSTOMER ALERT:\\n{report}")
            
            # Export database
            self.export_current_database()
            
            self.logger.info(f"✅ Monitoring cycle complete: {stats['new_customers']} new customers")
            
        except Exception as e:
            self.logger.error(f"❌ Monitoring cycle error: {e}")
    
    def start_monitoring(self):
        """Start continuous monitoring service"""
        self.logger.info("🚀 Starting KEATchen Customer Monitoring Service")
        
        # Schedule monitoring runs
        schedule.every(1).hours.do(self.run_monitoring_cycle)  # Every hour
        schedule.every().day.at("09:00").do(self.export_current_database)  # Daily export
        
        # Run initial scan
        self.logger.info("🔍 Running initial scan...")
        self.run_monitoring_cycle()
        
        # Start scheduling loop
        self.logger.info("⏰ Monitoring service active - checking every hour")
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute

def main():
    """Main monitoring service entry point"""
    monitor = KEATchenCustomerMonitor()
    
    # Check if this is a one-time run or continuous monitoring
    if os.getenv("RUN_ONCE", "false").lower() == "true":
        monitor.run_monitoring_cycle()
    else:
        monitor.start_monitoring()

if __name__ == "__main__":
    main()