FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ /app/app/
COPY lib/ /app/lib/

# Make sure data directory exists
RUN mkdir -p /app/data/weather_cache /app/data/mta_cache

# Set Python path to include lib directory
ENV PYTHONPATH="${PYTHONPATH}:/app"

# Run the Streamlit app
CMD ["streamlit", "run", "app/main.py", "--server.port=8501", "--server.address=0.0.0.0"]