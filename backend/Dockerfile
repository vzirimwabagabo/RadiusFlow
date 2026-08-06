FROM python:3.12-slim

# Create a non-privileged user and group for running the container
RUN groupadd -g 10001 radiusflow && \
    useradd -u 10001 -g radiusflow -s /bin/false -m radiusflow

WORKDIR /app

# Install system dependencies (radclient ships with freeradius-utils)
RUN apt-get update && apt-get install -y --no-install-recommends \
    freeradius-utils \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Ensure app directory is owned by non-privileged user
RUN chown -R radiusflow:radiusflow /app

USER radiusflow:radiusflow

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=20s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health', timeout=5)"

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
