#!/usr/bin/env python3
"""
Continue extraction from page 6 to completion
"""

import json
import os
from datetime import datetime

def continue_extraction():
    # Load existing data
    try:
        with open('customer_data/customers_mcp.json', 'r') as f:
            customers = json.load(f)
    except:
        customers = []
    
    print(f"📚 Starting with {len(customers)} existing customers")
    
    # Page 6 customers (from current view)
    page6_customers = [
        ('Stuart', 'Russell', 'stuart@therussellhousehold.co.uk', '+447805445128', '14 Loch Shin, East Kilbride', 'G74 2DH'),
        ('Gillian', 'Harvie', 'Gillianharvie@outlook.com', '+447875490855', '2 Lochaber Place, East Kilbride', 'G74 4BA'),
        ('Paul', 'Stevenson', 'paul_0008@hotmail.com', '+447742345009', '2 Louise Gardens, Holytown', 'ML1 4XF'),
        ('Thomas', 'Ather', 'thomasather666@mail.com', '+447708489031', '3 Glen Garry, East Kilbride', 'G74 2BN'),
        ('G', 'Mitchell', 'Greigmitchell_6@hotmail.co.uk', '+447545133553', '240 Pine Crescent, East Kilbride', 'G75 9HL'),
        ('Connor', 'Clark', 'connortclark11@gmail.com', '+447919818593', '65 Mauchline, East Kilbride', 'G74 3SA'),
        ('Lynne', 'Paterson', 'weelynp3031@hotmail.com', '+447400697999', '155 Owen Avenue, East Kilbride', 'G75 9AQ'),
        ('Kathleen', 'Bennett', 'kathleenbennett@hotmail.co.uk', '+447876822562', '27 Glen Farrar, East Kilbride', 'G74 2AG'),
        ('Lesley-Ann', 'Brown', 'Gel81278@gmail.com', '+447929865929', '7 Calderside Grove', 'G74 3SP'),
        ('Anna', 'Kaniuka', 'taranchik7@gmail.com', '+447376477696', '66 Easdale, East Kilbride', 'G74 2EB'),
        ('James', 'Grace', 'James.jmt.grace@hotmail.co.yk', '+447914205999', '9 Struthers Crescent, East Kilbride', 'G74 3LF'),
        ('Awsten', 'Cameron', 'cammy2106@icloud.com', '+447593854221', '5 Glen Cannich, East Kilbride', 'G74 2BW'),
        ('Kieran', 'Grant', 'kieran.grant88@googlemail.com', '+447454166551', '73 Rosslyn Avenue, East Kilbride', 'G74 4BS'),
        ('Nicolle', 'Blackley', 'nicolle.h.93@hotmail.com', '+447568567555', '100 Carnoustie Crescent, East Kilbride', 'G75 8TE'),
        ('Jamie', 'McCallum', 'Jamiemcc08@hotmail.com', '+447540278037', '8 Mauchline, East Kilbride', 'G74 3RZ'),
        ('Lisa', 'Campbell', 'Lisac1201@hotmail.co.uk', '+447432024249', '8 Mauchline, East Kilbride', 'G74 3RZ'),
        ('Lyn', 'Mitchell', 'Lyn84@outlook.com', '+447973854963', '3 Gillies Crescent, East Kilbride', 'G74 3PT'),
        ('Dean', 'Johnston', 'Deanmgp@gmail.com', '+447960329064', '69 Loch Assynt, East Kilbride', 'G74 2DN'),
        ('carlyn tasker', 'carlyn tasker', 'Carlynt88@gmail.com', '+447912215559', '10 Almond Drive, East Kilbride', 'G74 2HX'),
        ('Ian', 'Glen', 'Ianmglen14@gmail.com', '+447456239251', '5 Pitcairn Crescent, East Kilbride', 'G75 8TP')
    ]
    
    # Add page 6 customers
    for fname, lname, email, mobile, address, postcode in page6_customers:
        customer = {
            'first_name': fname,
            'last_name': lname,
            'email': email,
            'mobile': mobile,
            'address': address,
            'postcode': postcode,
            'page': 6,
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
    
    print(f'✅ Page 6 extracted: {len(page6_customers)} customers added')
    print(f'📊 Total: {len(customers)} customers')
    print(f'📈 Progress: 6/27 pages complete ({6/27*100:.1f}%)')
    
    return len(customers)

if __name__ == "__main__":
    continue_extraction()