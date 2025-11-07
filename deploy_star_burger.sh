#!/bin/bash

set -e

echo "Starting Star Burger deployment..."
cd /opt/Star_burger_web
echo " Pulling latest code from GitHub..."
git pull

echo "Code updated successfully!"

echo -e "Activating virtual environment..."
source venv/bin/activate

echo -e "Installing Python dependencies..."
pip install -r requirements.txt

echo -e "Running database migrations..."
python manage.py migrate --noinput

echo -e "Collecting static files..."
python manage.py collectstatic --noinput --clear


echo -e "Installing Node.js dependencies..."
npm ci --dev

echo -e "Restarting services..."
sudo systemctl restart starburger
sudo systemctl reload nginx

echo -e "Deployment completed successfully!"
