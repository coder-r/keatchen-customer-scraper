#!/usr/bin/env python3
"""
Health check script for Docker container
"""

import sqlite3
import os
import sys
from datetime import datetime, timedelta

def health_check():
    """Check if the monitoring service is healthy"""
    try:
        data_dir = os.getenv("DATA_DIR", "/app/data")
        db_path = os.path.join(data_dir, "customers.db")
        
        if not os.path.exists(db_path):
            print("❌ Database not found")
            return False
        
        # Check database connectivity
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        required_tables = ['customers', 'monitoring_log', 'new_customers_today']
        for table in required_tables:
            if table not in tables:
                print(f"❌ Missing table: {table}")
                conn.close()
                return False
        
        # Check recent activity (last 2 hours)
        two_hours_ago = (datetime.now() - timedelta(hours=2)).isoformat()
        cursor.execute('''
            SELECT COUNT(*) FROM monitoring_log 
            WHERE timestamp > ?
        ''', (two_hours_ago,))
        
        recent_activity = cursor.fetchone()[0]
        
        # Check customer count
        cursor.execute("SELECT COUNT(*) FROM customers WHERE is_active = TRUE")
        customer_count = cursor.fetchone()[0]
        
        conn.close()
        
        if customer_count < 100:
            print(f"⚠️ Low customer count: {customer_count}")
            return False
        
        if recent_activity == 0:
            print("⚠️ No recent monitoring activity")
            return False
        
        print(f"✅ Health check passed: {customer_count} customers, {recent_activity} recent logs")
        return True
        
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

if __name__ == "__main__":
    if health_check():
        sys.exit(0)
    else:
        sys.exit(1)