#!/usr/bin/env python3
"""
MCP-based Customer Scraper
Uses the same Playwright MCP session that's already logged in
"""

import json
import os
from datetime import datetime

class MCPCustomerScraper:
    def __init__(self):
        self.customers_data = []
        self.scraped_emails = set()
        self.output_dir = "customer_data"
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Load existing data
        self.load_existing_data()
        
    def load_existing_data(self):
        try:
            if os.path.exists(f"{self.output_dir}/customers_mcp.json"):
                with open(f"{self.output_dir}/customers_mcp.json", 'r') as f:
                    self.customers_data = json.load(f)
                    self.scraped_emails = {c.get('email', '').lower() for c in self.customers_data}
                    print(f"📚 Loaded {len(self.customers_data)} existing customers")
        except Exception as e:
            print(f"Error loading: {e}")
    
    def save_data(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save main JSON
        json_file = f"{self.output_dir}/customers_mcp.json"
        with open(json_file, 'w') as f:
            json.dump(self.customers_data, f, indent=2)
        
        # Save timestamped backup
        backup_file = f"{self.output_dir}/backup_customers_{timestamp}.json"
        with open(backup_file, 'w') as f:
            json.dump(self.customers_data, f, indent=2)
        
        print(f"💾 Saved {len(self.customers_data)} customers to {json_file}")
        
        # Create simple CSV
        csv_file = f"{self.output_dir}/customers_simple_{timestamp}.csv"
        with open(csv_file, 'w') as f:
            f.write("FirstName,LastName,Email,Mobile,Address,Postcode,DOB,City,County,TotalOrders\n")
            for c in self.customers_data:
                contact = c.get('contact_details', {})
                f.write(f'"{c.get("first_name","")}","{c.get("last_name","")}","{c.get("email","")}","{c.get("mobile","")}","{c.get("address","")}","{c.get("postcode","")}","{contact.get("dob","")}","{contact.get("city","")}","{contact.get("county","")}",{len(c.get("orders",[]))}\n')
        
        print(f"📊 CSV exported: {csv_file}")

# Global scraper instance
scraper = MCPCustomerScraper()

def extract_customer_from_row_data(row_data):
    """Extract customer from table row text"""
    parts = row_data.split('\t')
    if len(parts) >= 6:
        return {
            'first_name': parts[0].strip(),
            'last_name': parts[1].strip(), 
            'email': parts[2].strip(),
            'mobile': parts[3].strip(),
            'address': parts[4].strip(),
            'postcode': parts[5].strip(),
            'scraped_at': datetime.now().isoformat(),
            'contact_details': {},
            'orders': [],
            'loyalty': '',
            'coupons': [],
            'roles': '',
            'delivery': '',
            'discounts': []
        }
    return None

print("🚀 MCP Customer Scraper Ready!")
print("📋 Instructions:")
print("1. Make sure you're on the customer page")
print("2. Run: scraper.save_data() to save progress anytime")
print("3. Use: extract_customer_from_row_data(row_text) for quick extraction")
print(f"📊 Current database: {len(scraper.customers_data)} customers")

# If run directly, provide interactive mode
if __name__ == "__main__":
    print("\n🎯 Interactive Mode - You can now use:")
    print("   scraper.save_data() - Save current data")
    print("   scraper.customers_data - View all data")
    print("   extract_customer_from_row_data(text) - Extract from row")