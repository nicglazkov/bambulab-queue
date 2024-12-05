#!/bin/bash
set -e

# Initialize the database
python /app/scripts/init_db.py

# Start the Flask application
exec flask run --host=0.0.0.0 --port=5000 --reload
