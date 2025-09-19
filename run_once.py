#!/usr/bin/env python3
"""
One-time customer extraction script
Perfect for initial database population or manual runs
"""

import os
import sys
from customer_monitor import KEATchenCustomerMonitor

def main():
    """Run one-time customer extraction"""
    print("🚀 KEATchen Customer Monitor - One-Time Extraction")
    print("=" * 50)
    
    # Set environment for one-time run
    os.environ["RUN_ONCE"] = "true"
    os.environ["HEADLESS"] = "false"  # Show browser for debugging
    
    # Initialize monitor
    monitor = KEATchenCustomerMonitor()
    
    print("🔍 Starting comprehensive customer scan...")
    print("📋 This will extract all customers and update the database")
    
    try:
        # Run one monitoring cycle
        monitor.run_monitoring_cycle()
        
        # Generate final report
        report = monitor.generate_new_customer_report()
        print(f"\n📢 FINAL REPORT:")
        print(report)
        
        # Export current database
        json_file, csv_file, summary_file = monitor.export_current_database()
        
        print(f"\n✅ EXTRACTION COMPLETE!")
        print(f"📄 JSON: {json_file}")
        print(f"📊 CSV: {csv_file}")
        print(f"📋 Summary: {summary_file}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()