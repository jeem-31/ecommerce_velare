# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy entire application
COPY . .

# Create upload directories
RUN mkdir -p static/uploads/products \
             static/uploads/shop_logos \
             static/uploads/ids \
             static/uploads/profiles \
             static/uploads/rider_orcr \
             static/uploads/rider_dl \
             static/uploads/banners

# Expose port (Railway will override this)
EXPOSE 5000

# Use gunicorn for production
CMD gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 app:app
