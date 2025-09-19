#!/usr/bin/env python3
"""
Bulk extract all remaining customer pages
This script will process pages 4-27 systematically
"""

import json
import os
from datetime import datetime

def bulk_extract():
    """Extract all remaining pages efficiently"""
    
    # Load existing data
    try:
        with open('customer_data/customers_mcp.json', 'r') as f:
            customers = json.load(f)
        print(f"📚 Starting with {len(customers)} existing customers")
    except:
        customers = []
    
    # Define all remaining pages' customer data
    # This will be populated manually from the MCP Playwright session
    all_pages_data = {}
    
    # Page 4 data (from current view)
    all_pages_data[4] = [
        ('Jillian', 'Lang', 'jillianlang1974@gmail.com', '+447833514198', '48 Mount Cameron Drive North, East Kilbride, East Kilbride', 'G74 2ES'),
        ('Hannah', 'Muir', 'shinyrainbowflake@gmail.com', '+447845142151', '3 Lochranza Lane, East Kilbride', 'G75 9NG'),
        ('Dionne', 'Cassidy', 'deedee_87@hotmail.co.uk', '+447926321340', '252 Telford Road, East Kilbride', 'G75 0DL'),
        ('Alan', 'Paton', 'jamespaton78@gmail.com', '+447903474252', '8 Bosfield Corner, East Kilbride', 'G74 4AZ'),
        ('Allan', 'Lang', 'langa9006@gmail.com', '+447702061094', '48 Mount Cameron Drive North, East Kilbride', 'G74 2ES'),
        ('Tammy', 'Garvie', 'tammygarvie@hotmail.com', '+447472603315', '44 Letterickhills Crescent, Cambuslang', 'G72 8XL'),
        ('Adam', 'McKenzie', 'adamsko14498@gmail.com', '+447780238999', '77 Old Vic Court, East Kilbride', 'G74 3NE'),
        ('Nikki', 'Noble', 'nikkinoble@live.com', '+447710894426', '42 Simpson Drive, East Kilbride', 'G75 0AX'),
        ('Aidan', 'Knox', 'atknox02@gmail.com', '', '48 Mount Cameron Drive North, East Kilbride', 'G74 2ES'),
        ('Lesley', 'Hunter', 'Lah120311@gmail.com', '+447921953814', '18 Glen More, East Kilbride', 'G74 2AW'),
        ('Scott', 'McLeod', 'smcleod221991@gmail.com', '+447972596284', '21 Newton Avenue, Cambuslang', 'G72 7RL'),
        ('Stuart', 'Douglas', 'Studouglas1914@gmail.com', '+447817213339', '4 Pyotshaw Way, Cambuslang', 'G72 8WW'),
        ('Kevin', 'Paterson', 'kevshoose@gmail.com', '+447981209128', '7 St. Vincent Place, East Kilbride', 'G75 8NT')
    ]
    
    # Process page 4
    for fname, lname, email, mobile, address, postcode in all_pages_data[4]:
        customer = {
            'first_name': fname,
            'last_name': lname,
            'email': email,
            'mobile': mobile,
            'address': address,
            'postcode': postcode,
            'page': 4,
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
    
    # Save page 4
    with open('customer_data/customers_mcp.json', 'w') as f:
        json.dump(customers, f, indent=2)
    
    print(f'✅ Page 4 processed: {len(all_pages_data[4])} customers added')
    print(f'📊 Total customers: {len(customers)}')
    print(f'📄 Progress: 4/27 pages complete ({4/27*100:.1f}%)')
    
    return len(customers)

def create_extraction_summary():
    """Create summary of extraction progress"""
    try:
        with open('customer_data/customers_mcp.json', 'r') as f:
            customers = json.load(f)
        
        # Count by page
        page_counts = {}
        for c in customers:
            page = c.get('page', 0)
            page_counts[page] = page_counts.get(page, 0) + 1
        
        print("\\n📊 EXTRACTION SUMMARY")
        print(f"Total Customers: {len(customers)}")
        print("\\nBy Page:")
        for page in sorted(page_counts.keys()):
            print(f"  Page {page}: {page_counts[page]} customers")
        
        # Calculate remaining
        completed_pages = len(page_counts)
        remaining_pages = 27 - completed_pages
        estimated_remaining = remaining_pages * 20
        
        print(f"\\n📈 Progress:")
        print(f"  Completed: {completed_pages}/27 pages ({completed_pages/27*100:.1f}%)")
        print(f"  Remaining: {remaining_pages} pages")
        print(f"  Estimated customers remaining: ~{estimated_remaining}")
        
    except Exception as e:
        print(f"Error creating summary: {e}")

if __name__ == "__main__":
    bulk_extract()
    create_extraction_summary()