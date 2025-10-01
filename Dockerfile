# Use Python 3.10 base image
FROM python:3.10-slim

# Set working directory
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
