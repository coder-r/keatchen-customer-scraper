#!/usr/bin/env python3
"""
Initialize database with existing customer data
Run this once to populate the database with the 331 customers we already extracted
"""

import json
import sqlite3
import os
from datetime import datetime

def init_database_with_existing_data():
    """Initialize the database with our extracted customer data"""
    print("🚀 Initializing database with existing customer data...")
    
    # Create data directory
    os.makedirs("data", exist_ok=True)
    
    # Initialize database
    db_path = "data/customers.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables
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
    
    # Load existing customer data
    try:
        with open('customer_data/customers_mcp.json', 'r') as f:
            customers = json.load(f)
        
        print(f"📚 Loading {len(customers)} existing customers...")
        
        # Insert all existing customers
        for customer in customers:
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO customers (
                        email, first_name, last_name, mobile, address, postcode,
                        page, first_seen, last_updated, total_orders, is_active
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    len(customer.get('orders', [])),
                    True
                ))
            except Exception as e:
                print(f"Error inserting {customer.get('email', 'unknown')}: {e}")
                continue
        
        # Log the initialization
        cursor.execute('''
            INSERT INTO monitoring_log (
                timestamp, action, customers_found, new_customers, 
                updated_customers, errors, execution_time
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            'database_init',
            len(customers),
            len(customers),
            0,
            0,
            0.0
        ))
        
        conn.commit()
        
        print(f"✅ Database initialized with {len(customers)} customers")
        print(f"📂 Database: {db_path}")
        
        # Verify
        cursor.execute("SELECT COUNT(*) FROM customers WHERE is_active = TRUE")
        count = cursor.fetchone()[0]
        print(f"✅ Verification: {count} active customers in database")
        
    except Exception as e:
        print(f"❌ Error loading existing data: {e}")
        print("ℹ️ Database created but no existing data loaded")
    
    finally:
        conn.close()

if __name__ == "__main__":
    init_database_with_existing_data()