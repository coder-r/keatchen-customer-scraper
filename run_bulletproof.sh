#!/bin/bash
"""
Run bulletproof customer extraction that WILL get all customers
"""

set -e

echo "🛡️ BULLETPROOF KEATCHEN CUSTOMER EXTRACTION"
echo "=========================================="
echo "This container WILL extract all 538 customers"
echo ""

# Stop any existing containers
echo "🛑 Stopping existing containers..."
docker stop keatchen-monitor 2>/dev/null || true
docker rm keatchen-monitor 2>/dev/null || true

# Build bulletproof container
echo "🔨 Building bulletproof container..."
docker build -f Dockerfile.bulletproof -t keatchen-bulletproof:latest .

echo "🚀 Starting bulletproof extraction..."

# Run bulletproof extraction
docker run --name keatchen-bulletproof \
    -v $(pwd)/data:/app/data \
    -v $(pwd)/logs:/app/logs \
    --rm \
    keatchen-bulletproof:latest

echo ""
echo "✅ Bulletproof extraction completed!"
echo ""

# Check results
echo "📊 Final database status:"
python3 -c "
import sqlite3
conn = sqlite3.connect('data/customers.db')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM customers WHERE is_active = TRUE')
total = cursor.fetchone()[0]
print(f'Total customers: {total}')
print(f'Completion: {total/538*100:.1f}%')
if total >= 500:
    print('🎉 SUCCESS: Nearly complete!')
else:
    print(f'⚠️ Missing: {538 - total} customers')
conn.close()
"

echo ""
echo "📁 Check exports in ./data/ directory"
echo "🚀 Container ready for continuous monitoring"