# 1. Use a lightweight Python base image
FROM python:3.9-slim

# 2. Install System Dependencies (SpamAssassin is key here)
# We also install 'net-tools' and 'libio-socket-ssl-perl' for SA to work properly
RUN apt-get update && apt-get install -y \
    spamassassin \
    spamc \
    net-tools \
    libio-socket-ssl-perl \
    && rm -rf /var/lib/apt/lists/*

# 3. Update SpamAssassin Rules (So it knows modern spam tricks)
RUN sa-update

# 4. Set working directory
WORKDIR /app

# 5. Copy your files into the container
COPY . /app

# 6. Install Python Dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 7. Expose the port (Render usually uses 10000 or similar, handled by env)
EXPOSE 5000

# 8. Start the App using Gunicorn (Production Server)
# We bind to 0.0.0.0 so external users can reach it
# CRITICAL CHANGE: Used '-w 1' (1 worker) instead of 4 to prevent crashing on Free Tier (512MB RAM)
CMD ["gunicorn", "-w", "1", "-b", "0.0.0.0:5000", "app:app"]
