#!/usr/bin/env python3
"""
Test script - Extract just one customer to verify modal extraction works
"""

import json
import time
import os
from datetime import datetime
from playwright.sync_api import sync_playwright

class OneCustomerTest:
    def __init__(self):
        self.base_url = "https://keatchenunited.app4food.co.uk"
        self.login_url = f"{self.base_url}/admin/Account/Login"
        self.customer_url = f"{self.base_url}/admin/Customer"
        
        self.username = "admin@keatchen"
        self.password = "keatchen22"

    def login(self, page):
        print("🔐 Logging in...")
        page.goto(self.login_url)
        page.wait_for_load_state('networkidle')
        
        page.fill('input[placeholder*="email"]', self.username)
        page.fill('input[type="password"]', self.password)
        page.click('button:has-text("Log In")')
        page.wait_for_load_state('networkidle')
        
        if page.query_selector('a:has-text("Logout")'):
            print("✅ Login successful!")
            return True
        return False

    def test_one_customer(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False, slow_mo=500)
            page = browser.new_page()
            
            try:
                if not self.login(page):
                    return
                
                print("🗂️ Going to customers page...")
                page.goto(self.customer_url)
                page.wait_for_load_state('networkidle')
                
                print("🎯 Testing first customer (Angela)...")
                
                # Click Angela's Details button
                first_customer_row = page.query_selector('tbody tr:first-child')
                if first_customer_row:
                    details_button = first_customer_row.query_selector('button')
                    if details_button:
                        print("🔍 Clicking Details button...")
                        details_button.click()
                        page.wait_for_timeout(2000)
                        
                        customer_data = {
                            'contact_details': {},
                            'orders': [],
                            'loyalty': {},
                            'coupons': [],
                            'roles': [],
                            'delivery': {},
                            'discounts': []
                        }
                        
                        # Test Contact Details tab
                        print("📞 Extracting Contact Details...")
                        try:
                            page.click('div:has-text("Contact Details")')
                            page.wait_for_timeout(1000)
                            
                            # Extract all visible input fields
                            inputs = page.query_selector_all('input[value]')
                            for inp in inputs:
                                value = inp.get_attribute('value')
                                if value:
                                    if '@' in value:
                                        customer_data['contact_details']['email'] = value
                                    elif '+44' in value:
                                        customer_data['contact_details']['mobile'] = value
                                    elif len(value) < 50:  # Likely name/address field
                                        field_name = inp.get_attribute('name') or 'unknown'
                                        customer_data['contact_details'][field_name] = value
                            
                            print(f"✅ Contact details: {customer_data['contact_details']}")
                            
                        except Exception as e:
                            print(f"❌ Contact details error: {e}")
                        
                        # Test Orders tab
                        print("🛒 Extracting Orders...")
                        try:
                            page.click('div:has-text("Orders")')
                            page.wait_for_timeout(1000)
                            
                            orders_table = page.query_selector('table')
                            if orders_table:
                                order_rows = orders_table.query_selector_all('tbody tr')
                                print(f"Found {len(order_rows)} order rows")
                                for row in order_rows:
                                    cells = row.query_selector_all('td')
                                    if len(cells) >= 3:
                                        order_text = row.inner_text().strip()
                                        if order_text and 'Order No.' not in order_text:
                                            customer_data['orders'].append(order_text)
                            
                            print(f"✅ Orders: {len(customer_data['orders'])} orders found")
                            
                        except Exception as e:
                            print(f"❌ Orders error: {e}")
                        
                        # Test other tabs
                        for tab_name in ["Loyalty", "Coupons", "Roles", "Delivery", "Discounts"]:
                            try:
                                print(f"🏷️ Extracting {tab_name}...")
                                page.click(f'div:has-text("{tab_name}")')
                                page.wait_for_timeout(1000)
                                
                                # Get tab content
                                modal_content = page.query_selector('[id*="modal"]')
                                if modal_content:
                                    tab_text = modal_content.inner_text()
                                    customer_data[tab_name.lower()] = {'raw_text': tab_text[:500]}  # Limit text
                                    print(f"✅ {tab_name}: Extracted")
                                
                            except Exception as e:
                                print(f"❌ {tab_name} error: {e}")
                        
                        # Close modal
                        close_button = page.query_selector('button:has-text("Close")')
                        if close_button:
                            close_button.click()
                            page.wait_for_timeout(500)
                        
                        # Save test data
                        with open('test_customer_data.json', 'w') as f:
                            json.dump(customer_data, f, indent=2)
                        
                        print("🎉 Test customer extracted successfully!")
                        print(f"📄 Data saved to: test_customer_data.json")
                        return customer_data
                
            except Exception as e:
                print(f"❌ Test error: {e}")
            finally:
                browser.close()

if __name__ == "__main__":
    test = OneCustomerTest()
    test.test_one_customer()