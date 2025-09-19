#!/usr/bin/env python3
"""
Web Dashboard for KEATchen Customer Monitor
Shows real-time customer data and new customer alerts
"""

from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
import sqlite3
import os
from datetime import datetime, timedelta
import json
import pandas as pd

app = FastAPI(title="KEATchen Customer Monitor Dashboard")
templates = Jinja2Templates(directory="templates")

# Configuration
DATA_DIR = os.getenv("DATA_DIR", "/app/data")
DB_PATH = os.path.join(DATA_DIR, "customers.db")

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page"""
    try:
        conn = sqlite3.connect(DB_PATH)
        
        # Get total customers
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM customers WHERE is_active = TRUE")
        total_customers = cursor.fetchone()[0]
        
        # Get new customers today
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute('''
            SELECT COUNT(*) FROM new_customers_today 
            WHERE date(detected_at) = ?
        ''', (today,))
        new_today = cursor.fetchone()[0]
        
        # Get new customers this week
        week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        cursor.execute('''
            SELECT COUNT(*) FROM new_customers_today 
            WHERE date(detected_at) >= ?
        ''', (week_ago,))
        new_week = cursor.fetchone()[0]
        
        # Get recent monitoring activity
        cursor.execute('''
            SELECT timestamp, new_customers, execution_time, errors
            FROM monitoring_log 
            ORDER BY timestamp DESC 
            LIMIT 10
        ''')
        recent_scans = cursor.fetchall()
        
        conn.close()
        
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "total_customers": total_customers,
            "new_today": new_today,
            "new_week": new_week,
            "recent_scans": recent_scans,
            "last_update": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
    except Exception as e:
        return HTMLResponse(f"<h1>Dashboard Error</h1><p>{e}</p>", status_code=500)

@app.get("/api/customers")
async def get_customers():
    """API endpoint to get all customers"""
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query("SELECT * FROM customers WHERE is_active = TRUE", conn)
        conn.close()
        
        return JSONResponse(df.to_dict('records'))
        
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/new-customers")
async def get_new_customers():
    """API endpoint to get new customers"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute('''
            SELECT email, first_name, last_name, mobile, detected_at
            FROM new_customers_today
            WHERE date(detected_at) = ?
            ORDER BY detected_at DESC
        ''', (today,))
        
        new_customers = []
        for row in cursor.fetchall():
            new_customers.append({
                'email': row[0],
                'first_name': row[1],
                'last_name': row[2],
                'mobile': row[3],
                'detected_at': row[4]
            })
        
        conn.close()
        return JSONResponse(new_customers)
        
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/stats")
async def get_stats():
    """API endpoint for dashboard statistics"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Total customers
        cursor.execute("SELECT COUNT(*) FROM customers WHERE is_active = TRUE")
        total = cursor.fetchone()[0]
        
        # New today
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute('''
            SELECT COUNT(*) FROM new_customers_today 
            WHERE date(detected_at) = ?
        ''', (today,))
        new_today = cursor.fetchone()[0]
        
        # Geographic distribution
        cursor.execute('''
            SELECT 
                CASE 
                    WHEN address LIKE '%East Kilbride%' THEN 'East Kilbride'
                    WHEN address LIKE '%Blantyre%' THEN 'Blantyre'
                    WHEN address LIKE '%Cambuslang%' THEN 'Cambuslang'
                    ELSE 'Other'
                END as location,
                COUNT(*) as count
            FROM customers 
            WHERE is_active = TRUE
            GROUP BY location
        ''')
        
        geo_data = {row[0]: row[1] for row in cursor.fetchall()}
        
        conn.close()
        
        return JSONResponse({
            "total_customers": total,
            "new_today": new_today,
            "geographic_distribution": geo_data
        })
        
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8081)