FROM python:3.10-slim

# Install system dependencies for building some Python packages
RUN apt-get update && apt-get install -y \
    build-essential \
    libffi-dev \
    libssl-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy app code
COPY . .

# Expose the port Render provides
ENV PORT=10000
EXPOSE $PORT

# Start the app with gunicorn
CMD ["gunicorn", "app:app", "-b", "0.0.0.0:$PORT"]
