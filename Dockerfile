FROM python:3.12-bookworm

WORKDIR /workspace

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install the proprietary Google Chrome instead of open-source Chromium
RUN playwright install chrome
RUN playwright install-deps chrome

# Copy application files
COPY app/ ./app/

# Start command
CMD ["python", "-m", "app.main"]
