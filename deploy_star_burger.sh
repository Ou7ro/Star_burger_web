#!/bin/bash

set -e

echo "Starting Star Burger deployment..."
cd /opt/Star_burger_web
echo " Pulling latest code from GitHub..."
git pull

COMMIT_HASH=$(git rev-parse HEAD)
COMMIT_MESSAGE=$(git log --pretty=format:'%h' -n 1)

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

set -a  
source .env
set +a

curl -X POST "https://api.rollbar.com/api/1/deploy/" \
  -H "Content-Type: application/json" \
  -d '{
    "access_token": "'"$ROLLBAR_TOKEN"'",
    "environment": "production",
    "revision": "'"$COMMIT_HASH"'",
    "local_username": "'"$(whoami)"'",
    "comment": "Auto-deployment from script"
  }'

echo -e "Deployment completed successfully!"
