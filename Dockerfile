# Use Python 3.12 slim image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=app.py

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application files
COPY . .

# Create necessary directories
RUN mkdir -p static/uploads/products \
    static/uploads/shop_logos \
    static/uploads/ids \
    static/uploads/profiles \
    static/uploads/rider_orcr \
    static/uploads/rider_dl

# Expose port
EXPOSE 5000

# Run the application
CMD ["python", "app.py"]
