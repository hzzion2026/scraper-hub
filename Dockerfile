FROM python:3.11-slim

WORKDIR /app

# Install Playwright deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget curl ca-certificates gnupg \
    libnss3 libnspr4 libatk-bridge2.0-0 libdrm2 libxkbcommon0 \
    libgbm1 libasound2 libxshmfence1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    playwright install chromium

COPY . .

ENTRYPOINT ["python", "cli.py"]
CMD ["demo"]
