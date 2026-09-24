FROM python:3.12-bookworm

WORKDIR /workspace

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DISPLAY=:99

# Install XVFB and python dependencies
COPY requirements.txt .
RUN apt-get update && apt-get install -y xvfb && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir -r requirements.txt

# Let Playwright install Chromium and all its required system dependencies automatically
RUN playwright install chrome
RUN playwright install-deps chrome

# Copy application files
COPY app/ ./app/

# Start command using xvfb-run to simulate a real monitor
CMD ["xvfb-run", "--auto-servernum", "--server-args=-screen 0 1920x1080x24", "python", "-m", "app.main"]
