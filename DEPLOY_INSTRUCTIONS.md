# 🚀 Deploy KEATchen Customer Monitor on Your Docker Host

## Quick Deployment (2 commands)

### 1. On your Docker host, run:
```bash
git clone https://github.com/coder-r/keatchen-customer-scraper.git
cd keatchen-customer-scraper
```

### 2. Deploy with one command:
```bash
./docker-run.sh
```

**That's it!** The system will:
- ✅ Build Docker containers
- ✅ Initialize database with 331 existing customers
- ✅ Start monitoring for new customers every hour
- ✅ Extract the missing 200+ customers from pages 14-19, 21-24
- ✅ Show dashboard at http://your-host:8081

## What Happens After Deployment

### Immediate Actions:
1. **Database initialized** with 331 existing customers
2. **First scan starts** - extracts missing customers from pages 14-19, 21-24
3. **Dashboard available** at http://localhost:8081
4. **Continuous monitoring** begins (every hour)

### Ongoing Operations:
- **Hourly scans** detect new customers automatically
- **Real-time alerts** when new customers register
- **No duplicates** - only genuinely new customers added
- **Complete data extraction** including Contact Details, Orders, Loyalty
- **Automatic exports** to JSON/CSV formats

## Monitor the Deployment

### Check container status:
```bash
docker-compose ps
```

### View logs:
```bash
# Monitor logs
docker-compose logs -f keatchen-monitor

# Dashboard logs  
docker-compose logs -f keatchen-dashboard
```

### Access dashboard:
```bash
# Open in browser
http://localhost:8081
```

### Check database:
```bash
# View customer count
docker exec keatchen-customer-monitor python -c "
import sqlite3
conn = sqlite3.connect('/app/data/customers.db')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM customers WHERE is_active = TRUE')
print(f'Total customers: {cursor.fetchone()[0]}')
conn.close()
"
```

## Expected Timeline

### Initial Deployment (First Run):
- **0-2 minutes**: Container build and startup
- **2-5 minutes**: Database initialization with 331 customers
- **5-45 minutes**: First complete scan extracts missing ~200 customers
- **45+ minutes**: Continuous hourly monitoring begins

### After First Complete Scan:
- **~530+ customers** in database (complete extraction)
- **New customer detection** every hour
- **Real-time alerts** via dashboard
- **Automatic exports** and reporting

## Troubleshooting

### If containers don't start:
```bash
# Check Docker is running
docker --version
docker-compose --version

# Check ports are available
netstat -tulpn | grep :808
```

### If login fails:
```bash
# Edit credentials in .env file
nano .env

# Update with correct KEATchen admin credentials
KEATCHEN_USERNAME=your-email
KEATCHEN_PASSWORD=your-password
```

### If extraction seems slow:
```bash
# This is normal - extracting customer details takes time
# Monitor progress in logs:
docker-compose logs -f keatchen-monitor
```

## Success Indicators

### ✅ Successful Deployment:
- Containers show "healthy" status
- Dashboard accessible at port 8081
- Logs show "Login successful" messages
- Customer count increases over time

### ✅ Complete Extraction:
- Database reaches 530+ customers
- All pages 1-27 show activity in logs
- No more "new customers" detected in subsequent scans
- Dashboard shows stable customer count

## Data Access

### Real-time API:
- `http://localhost:8081/api/customers` - All customers JSON
- `http://localhost:8081/api/new-customers` - New customers today
- `http://localhost:8081/api/stats` - Dashboard statistics

### File Exports:
- `./data/customers_export_*.json` - Complete database exports
- `./data/customers_export_*.csv` - Spreadsheet format
- `./data/database_summary_*.txt` - Analysis reports

The system is designed to be 100% reliable and will complete the extraction automatically once deployed on your Docker host!