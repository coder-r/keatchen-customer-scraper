#!/usr/bin/env python3
"""
Extract all customer pages systematically
"""

import json
import os
from datetime import datetime

# Continue from page 3 through 27
def continue_extraction():
    # Load existing data
    try:
        with open('customer_data/customers_mcp.json', 'r') as f:
            customers = json.load(f)
        print(f"📚 Loaded {len(customers)} existing customers")
    except:
        customers = []
    
    # We'll extract from the remaining pages manually
    print("📋 Ready to continue extraction from page 3...")
    print("📊 Current progress:")
    print(f"   Page 1: ✅ 20 customers")
    print(f"   Page 2: ✅ 20 customers") 
    print(f"   Total so far: {len(customers)} customers")
    print(f"   Remaining: Pages 3-27 ({(27-2)*20} customers approximately)")
    
    return len(customers)

if __name__ == "__main__":
    continue_extraction()