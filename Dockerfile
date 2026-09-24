FROM python:3.12-slim

WORKDIR /workspace

# Set environment variables to optimize Python execution
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app/ ./app/

# Expose the standard port
EXPOSE 8000

# Command to run the application (Uses the PORT environment variable for Railway compatibility)
CMD uvicorn app.main:app --host 0.0.0.0 --port $PORT
