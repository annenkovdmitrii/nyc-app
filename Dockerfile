FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install uv directly with pip
RUN pip install --no-cache-dir uv

# Copy requirements first for better caching
COPY requirements.txt .

# Use the --system flag with uv to install packages globally
RUN uv pip install --system --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ /app/

# Run the Streamlit app
CMD ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]