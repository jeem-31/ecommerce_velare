# Use Python 3.11 slim image (matching runtime.txt)
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=app.py

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app.py .
COPY blueprints/ ./blueprints/
COPY database/ ./database/
COPY templates/ ./templates/
COPY static/ ./static/
COPY .env .

# Create necessary directories with proper permissions
RUN mkdir -p static/uploads/products \
    static/uploads/shop_logos \
    static/uploads/ids \
    static/uploads/profiles \
    static/uploads/rider_orcr \
    static/uploads/rider_dl \
    static/uploads/banners && \
    chmod -R 755 static/uploads

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Run the application with gunicorn for production
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "app:app"]
