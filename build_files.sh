#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "Build Started..."

# 1. Install Dependencies
echo "Installing Dependencies..."
python3.9 -m pip install -r requirements.txt

# 2. Collect Static Files
echo "Collecting Static Files..."
python manage.py collectstatic --noinput

# 3. Run Migrations (Optional but recommended for auto-updates)
echo "Running Migrations..."
python3.9 manage.py makemigrations
python3.9 manage.py migrate

echo "Build Completed Successfully!"