FROM python:3.12-slim

WORKDIR /workspace

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app/ ./app/

# Start command (Python handles the PORT variable)
CMD ["python", "app/main.py"]
