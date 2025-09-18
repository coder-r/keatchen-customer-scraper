#!/usr/bin/env python3
"""
Test script for KEATchen Customer Scraper
Tests the scraper with just the first page (20 customers)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from customer_scraper import KEATchenCustomerScraper

def test_first_page():
    """Test scraper with first page only"""
    print("=== KEATchen Customer Scraper Test ===")
    print("Testing with first page only (max 20 customers)")
    
    scraper = KEATchenCustomerScraper()
    
    # Override the scrape_all_customers method to only do first page
    scraper.scrape_first_page_only()

class TestKEATchenCustomerScraper(KEATchenCustomerScraper):
    def scrape_first_page_only(self):
        """Modified scraper that only processes the first page"""
        from playwright.sync_api import sync_playwright
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()
            
            try:
                # Login
                if not self.login(page):
                    print("Failed to login. Exiting.")
                    return
                
                # Navigate to customers page
                page.goto(self.customer_url)
                page.wait_for_load_state('networkidle')
                
                print("=== Testing First Page Only ===")
                
                # Scrape only current (first) page
                page_scraped = self.scrape_current_page(page)
                
                print(f"Test complete. Scraped {page_scraped} customers from first page.")
                print(f"Total customers in database: {len(self.customers_data)}")
                
                # Save test data
                self.save_data()
                
            except Exception as e:
                print(f"Test error: {e}")
            finally:
                browser.close()

if __name__ == "__main__":
    test_scraper = TestKEATchenCustomerScraper()
    test_scraper.scrape_first_page_only()