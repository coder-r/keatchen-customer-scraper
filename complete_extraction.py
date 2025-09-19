#!/usr/bin/env python3
"""
Complete the full customer extraction - all 538 customers
This script will be run in chunks as we navigate through all pages
"""

import json
import os
from datetime import datetime

def add_batch_customers(page_start, page_end, customers_batch_data):
    """Add a batch of customers from multiple pages"""
    try:
        with open('customer_data/customers_mcp.json', 'r') as f:
            customers = json.load(f)
    except:
        customers = []
    
    total_added = 0
    
    for page_num in range(page_start, page_end + 1):
        if page_num in customers_batch_data:
            page_customers = customers_batch_data[page_num]
            for fname, lname, email, mobile, address, postcode in page_customers:
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
                total_added += 1
    
    # Save updated data
    with open('customer_data/customers_mcp.json', 'w') as f:
        json.dump(customers, f, indent=2)
    
    print(f'✅ Batch {page_start}-{page_end}: {total_added} customers added, total: {len(customers)}')
    return len(customers)

def create_final_database():
    """Create the final customer database with full export"""
    try:
        with open('customer_data/customers_mcp.json', 'r') as f:
            customers = json.load(f)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create final comprehensive JSON
        final_json = f'customer_data/FINAL_KEATCHEN_CUSTOMERS_{timestamp}.json'
        with open(final_json, 'w') as f:
            json.dump(customers, f, indent=2)
        
        # Create master CSV
        final_csv = f'customer_data/FINAL_KEATCHEN_CUSTOMERS_{timestamp}.csv'
        with open(final_csv, 'w') as f:
            f.write('FirstName,LastName,Email,Mobile,Address,Postcode,Page,ScrapedAt\\n')
            for c in customers:
                fname = c.get('first_name', '').replace('\"', '\"\"')
                lname = c.get('last_name', '').replace('\"', '\"\"')
                email = c.get('email', '')
                mobile = c.get('mobile', '')
                address = c.get('address', '').replace('\"', '\"\"')
                postcode = c.get('postcode', '')
                page = c.get('page', 0)
                scraped = c.get('scraped_at', '')
                
                f.write(f'\"{fname}\",\"{lname}\",\"{email}\",\"{mobile}\",\"{address}\",\"{postcode}\",{page},\"{scraped}\"\\n')
        
        # Create summary report
        summary_file = f'customer_data/DATABASE_SUMMARY_{timestamp}.txt'
        with open(summary_file, 'w') as f:
            f.write('KEATchen Customer Database - Final Report\\n')
            f.write('=' * 50 + '\\n')
            f.write(f'Generated: {datetime.now().strftime(\"%Y-%m-%d %H:%M:%S\")}\\n')
            f.write(f'Total Customers: {len(customers)}\\n\\n')
            
            # Stats by page
            page_stats = {}
            for c in customers:
                page = c.get('page', 0)
                page_stats[page] = page_stats.get(page, 0) + 1
            
            f.write('Customers by Page:\\n')
            for page in sorted(page_stats.keys()):
                f.write(f'  Page {page:2d}: {page_stats[page]:3d} customers\\n')
            
            # Email domain analysis
            domains = {}
            for c in customers:
                email = c.get('email', '')
                if '@' in email:
                    domain = email.split('@')[1].lower()
                    domains[domain] = domains.get(domain, 0) + 1
            
            f.write('\\nTop Email Domains:\\n')
            for domain, count in sorted(domains.items(), key=lambda x: x[1], reverse=True)[:15]:
                f.write(f'  {domain:25s}: {count:3d}\\n')
            
            # Geographic analysis
            postcodes = {}
            cities = {}
            for c in customers:
                postcode = c.get('postcode', '')[:4]
                address = c.get('address', '')
                
                if postcode:
                    postcodes[postcode] = postcodes.get(postcode, 0) + 1
                
                if 'East Kilbride' in address:
                    cities['East Kilbride'] = cities.get('East Kilbride', 0) + 1
                elif 'Blantyre' in address:
                    cities['Blantyre'] = cities.get('Blantyre', 0) + 1
                elif 'Cambuslang' in address:
                    cities['Cambuslang'] = cities.get('Cambuslang', 0) + 1
                elif 'Hamilton' in address:
                    cities['Hamilton'] = cities.get('Hamilton', 0) + 1
                elif 'Glasgow' in address:
                    cities['Glasgow'] = cities.get('Glasgow', 0) + 1
            
            f.write('\\nTop Postcode Areas:\\n')
            for postcode, count in sorted(postcodes.items(), key=lambda x: x[1], reverse=True)[:15]:
                f.write(f'  {postcode:6s}: {count:3d}\\n')
            
            f.write('\\nCustomers by City:\\n')
            for city, count in sorted(cities.items(), key=lambda x: x[1], reverse=True):
                f.write(f'  {city:15s}: {count:3d}\\n')
        
        print(f'🎉 FINAL DATABASE CREATED!')
        print(f'📄 JSON: {final_json}')
        print(f'📊 CSV: {final_csv}')
        print(f'📋 Summary: {summary_file}')
        print(f'🏆 Total Customers: {len(customers)}')
        
        return customers
        
    except Exception as e:
        print(f'❌ Error creating final database: {e}')
        return None

if __name__ == "__main__":
    print("🚀 Complete Extraction Tool")
    print("Use add_batch_customers(start_page, end_page, data_dict)")
    print("When done: create_final_database()")
    
    # Show current status
    try:
        with open('customer_data/customers_mcp.json', 'r') as f:
            customers = json.load(f)
        print(f"📊 Current: {len(customers)} customers")
        
        pages_done = set(c.get('page', 0) for c in customers)
        print(f"📄 Completed pages: {sorted(pages_done)}")
        print(f"📄 Remaining pages: {set(range(6, 28)) - pages_done}")
        
    except:
        print("No data found")