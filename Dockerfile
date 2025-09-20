# KEATchen Customer Monitor - Production Docker Container
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    curl \
    && wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/googlechrome-linux-keyring.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/googlechrome-linux-keyring.gpg] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements-docker.txt .
RUN pip install --no-cache-dir -r requirements-docker.txt

# Install Playwright browsers
RUN playwright install chromium

# Copy application code
COPY . .

# Create data directory
RUN mkdir -p /app/data /app/logs

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV HEADLESS=true
ENV DATA_DIR=/app/data
ENV LOG_LEVEL=INFO

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python health_check.py || exit 1

# Run the monitoring service
CMD ["python", "customer_monitor.py"]