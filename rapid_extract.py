#!/usr/bin/env python3
"""
Rapid extraction script to continue from current MCP session
"""

import json
import os
from datetime import datetime

def extract_page_data(page_num, customer_data_list):
    """Add customers to the database"""
    # Load existing data
    try:
        with open('customer_data/customers_mcp.json', 'r') as f:
            customers = json.load(f)
    except:
        customers = []
    
    # Add new customers
    for fname, lname, email, mobile, address, postcode in customer_data_list:
        customer = {
            'first_name': fname,
            'last_name': lname,
            'email': email,
            'mobile': mobile,
            'address': address,
            'postcode': postcode,
            'page': page_num,
            'scraped_at': datetime.now().isoformat(),
            'contact_details': {},
            'orders': [],
            'loyalty': '',
            'coupons': [],
            'roles': '',
            'delivery': '',
            'discounts': []
        }
        customers.append(customer)
    
    # Save updated data
    with open('customer_data/customers_mcp.json', 'w') as f:
        json.dump(customers, f, indent=2)
    
    print(f'✅ Page {page_num} extracted: {len(customer_data_list)} customers added, total: {len(customers)}')
    return len(customers)

def create_final_exports():
    """Create final CSV and summary files"""
    try:
        with open('customer_data/customers_mcp.json', 'r') as f:
            customers = json.load(f)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create comprehensive CSV
        csv_file = f'customer_data/FINAL_keatchen_customers_{timestamp}.csv'
        with open(csv_file, 'w') as f:
            f.write('FirstName,LastName,Email,Mobile,Address,Postcode,Page,ScrapedAt\\n')
            for c in customers:
                f.write(f'\"{c.get(\"first_name\",\"\")}\",\"{c.get(\"last_name\",\"\")}\",\"{c.get(\"email\",\"\")}\",\"{c.get(\"mobile\",\"\")}\",\"{c.get(\"address\",\"\")}\",\"{c.get(\"postcode\",\"\")}\",{c.get(\"page\",0)},\"{c.get(\"scraped_at\",\"\")}\"\\n')
        
        # Create summary report
        summary_file = f'customer_data/SUMMARY_report_{timestamp}.txt'
        with open(summary_file, 'w') as f:
            f.write(f'KEATchen Customer Database Summary\\n')
            f.write(f'Generated: {datetime.now().strftime(\"%Y-%m-%d %H:%M:%S\")}\\n')
            f.write(f'Total Customers: {len(customers)}\\n\\n')
            
            # Count by page
            page_counts = {}
            for c in customers:
                page = c.get('page', 0)
                page_counts[page] = page_counts.get(page, 0) + 1
            
            f.write('Customers by Page:\\n')
            for page in sorted(page_counts.keys()):
                f.write(f'  Page {page}: {page_counts[page]} customers\\n')
            
            # Email domains
            domains = {}
            for c in customers:
                email = c.get('email', '')
                if '@' in email:
                    domain = email.split('@')[1].lower()
                    domains[domain] = domains.get(domain, 0) + 1
            
            f.write('\\nTop Email Domains:\\n')
            for domain, count in sorted(domains.items(), key=lambda x: x[1], reverse=True)[:10]:
                f.write(f'  {domain}: {count}\\n')
            
            # Postcode analysis
            postcodes = {}
            for c in customers:
                postcode = c.get('postcode', '')[:4]  # First 4 chars
                if postcode:
                    postcodes[postcode] = postcodes.get(postcode, 0) + 1
            
            f.write('\\nTop Postcode Areas:\\n')
            for postcode, count in sorted(postcodes.items(), key=lambda x: x[1], reverse=True)[:10]:
                f.write(f'  {postcode}: {count}\\n')
        
        print(f'📊 Final exports created:')
        print(f'   📄 CSV: {csv_file}')
        print(f'   📋 Summary: {summary_file}')
        print(f'   🎯 Total: {len(customers)} customers')
        
    except Exception as e:
        print(f'❌ Export error: {e}')

# Helper function to quickly add page data
def add_page(page_num, customers_list):
    return extract_page_data(page_num, customers_list)

if __name__ == "__main__":
    print("🚀 Rapid Extract Tool Ready!")
    print("Usage: add_page(page_num, [(fname, lname, email, mobile, address, postcode), ...])")
    print("When done: create_final_exports()")
    
    # Show current progress
    try:
        with open('customer_data/customers_mcp.json', 'r') as f:
            customers = json.load(f)
        print(f"📊 Current: {len(customers)} customers in database")
        
        # Show page progress
        pages = set(c.get('page', 0) for c in customers)
        print(f"📄 Pages completed: {sorted(pages)}")
        print(f"📄 Remaining: {set(range(4, 28)) - pages}")
        
    except:
        print("📊 No existing data found")