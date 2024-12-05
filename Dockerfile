# Use Python 3.12 as base image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create uploads directory
RUN mkdir -p uploads

# Create volume mount points
VOLUME ["/app/uploads", "/app/instance"]

# Expose port
EXPOSE 5000

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# Create initialization script
RUN echo '#!/usr/bin/env python3\n\
    import os\n\
    from app import app, db\n\
    \n\
    def init_db():\n\
    with app.app_context():\n\
    db.create_all()\n\
    \n\
    if __name__ == "__main__":\n\
    init_db()' > /app/init_db.py && \
    chmod +x /app/init_db.py

# Create entrypoint script
RUN echo '#!/bin/bash\n\
    python /app/init_db.py\n\
    exec python -c "from app import app; app.run(host=\"0.0.0.0\", port=5000)"' > /app/entrypoint.sh && \
    chmod +x /app/entrypoint.sh

# Run the application
ENTRYPOINT ["/app/entrypoint.sh"]