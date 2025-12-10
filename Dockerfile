# Use Alpine Linux (Much smaller and faster)
FROM python:3.9-alpine

# Install System Dependencies
# Alpine uses 'apk' instead of 'apt', which is faster
# We install build tools (gcc, make) because some Python libs need to compile
RUN apk add --no-cache \
    spamassassin \
    perl \
    perl-net-dns \
    perl-io-socket-ssl \
    perl-libwww \
    make \
    gcc \
    musl-dev \
    linux-headers

# Initialize SpamAssassin rules
# 'spamassassin --lint' ensures the config files are created correctly
RUN sa-update && spamassassin --lint

# Set up the app directory
WORKDIR /app

# Copy your files
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port
EXPOSE 5000

# Run with 1 worker to save memory on free tier
CMD ["gunicorn", "-w", "1", "-b", "0.0.0.0:5000", "app:app"]
