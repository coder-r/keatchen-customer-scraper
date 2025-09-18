#!/usr/bin/env python3
"""
Data analysis script for scraped customer data
Generates reports and insights from the customer database
"""

import json
import pandas as pd
import os
from collections import Counter
from datetime import datetime

class CustomerDataAnalyzer:
    def __init__(self, data_file="customer_data/customers.json"):
        self.data_file = data_file
        self.customers = []
        self.load_data()
    
    def load_data(self):
        """Load customer data from JSON file"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    self.customers = json.load(f)
                print(f"Loaded {len(self.customers)} customers for analysis")
            else:
                print(f"Data file not found: {self.data_file}")
        except Exception as e:
            print(f"Error loading data: {e}")
    
    def generate_summary_report(self):
        """Generate summary statistics report"""
        if not self.customers:
            print("No customer data available")
            return
        
        print("\n=== CUSTOMER DATABASE SUMMARY ===")
        print(f"Total Customers: {len(self.customers)}")
        
        # Email domains analysis
        domains = []
        for customer in self.customers:
            email = customer.get('email', '')
            if '@' in email:
                domain = email.split('@')[1].lower()
                domains.append(domain)
        
        domain_counts = Counter(domains)
        print(f"\nTop Email Domains:")
        for domain, count in domain_counts.most_common(10):
            print(f"  {domain}: {count}")
        
        # Postcode analysis
        postcodes = [c.get('postcode', '')[:4] for c in self.customers if c.get('postcode')]
        postcode_counts = Counter(postcodes)
        print(f"\nTop Postcode Areas:")
        for postcode, count in postcode_counts.most_common(10):
            print(f"  {postcode}: {count}")
        
        # Orders analysis
        total_orders = 0
        customers_with_orders = 0
        for customer in self.customers:
            orders = customer.get('orders', [])
            if orders:
                customers_with_orders += 1
                total_orders += len(orders)
        
        print(f"\nOrder Statistics:")
        print(f"  Customers with orders: {customers_with_orders}")
        print(f"  Total orders: {total_orders}")
        if customers_with_orders > 0:
            print(f"  Average orders per customer: {total_orders/customers_with_orders:.2f}")
        
        # Loyalty analysis
        loyalty_customers = len([c for c in self.customers if c.get('loyalty', {}).get('raw_text')])
        print(f"  Customers with loyalty data: {loyalty_customers}")
        
        # Coupons analysis
        coupon_customers = len([c for c in self.customers if c.get('coupons')])
        print(f"  Customers with coupons: {coupon_customers}")
    
    def export_csv_reports(self):
        """Export various CSV reports"""
        if not self.customers:
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Basic customer info CSV
        basic_data = []
        for customer in self.customers:
            basic_data.append({
                'first_name': customer.get('first_name', ''),
                'last_name': customer.get('last_name', ''),
                'email': customer.get('email', ''),
                'mobile': customer.get('mobile', ''),
                'address': customer.get('address', ''),
                'postcode': customer.get('postcode', ''),
                'total_orders': len(customer.get('orders', [])),
                'has_loyalty': bool(customer.get('loyalty', {}).get('raw_text')),
                'has_coupons': bool(customer.get('coupons')),
                'scraped_at': customer.get('scraped_at', '')
            })
        
        df_basic = pd.DataFrame(basic_data)
        basic_csv = f"customer_data/customer_summary_{timestamp}.csv"
        df_basic.to_csv(basic_csv, index=False)
        print(f"Basic customer summary exported: {basic_csv}")
        
        # Orders CSV
        orders_data = []
        for customer in self.customers:
            for order in customer.get('orders', []):
                orders_data.append({
                    'customer_email': customer.get('email', ''),
                    'customer_name': f"{customer.get('first_name', '')} {customer.get('last_name', '')}",
                    'order_id': order.get('order_id', ''),
                    'date': order.get('date', ''),
                    'total': order.get('total', '')
                })
        
        if orders_data:
            df_orders = pd.DataFrame(orders_data)
            orders_csv = f"customer_data/orders_summary_{timestamp}.csv"
            df_orders.to_csv(orders_csv, index=False)
            print(f"Orders summary exported: {orders_csv}")

def main():
    analyzer = CustomerDataAnalyzer()
    analyzer.generate_summary_report()
    analyzer.export_csv_reports()

if __name__ == "__main__":
    main()