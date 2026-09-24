FROM python:3.12-bookworm

WORKDIR /workspace

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Let Playwright install Chromium and all its required system dependencies automatically
RUN playwright install chromium
RUN playwright install-deps chromium

# Copy application files
COPY app/ ./app/

# Start command
CMD ["python", "-m", "app.main"]
