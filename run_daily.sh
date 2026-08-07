#!/bin/bash
# Hermes Social Agent - Daily Automation Script

# Navigate to the correct directory (Assumes EC2 ubuntu user)
cd /home/ubuntu/Hermes-Social-Agent || exit

# Activate virtual environment
source venv/bin/activate

echo "====================================================="
echo "Starting Hermes Social Agent Daily Pipeline..."
echo "====================================================="

echo "[1/4] Phase 1: Discovering Trends (Scraping the Web)..."
python -m hermes_social.cli discover --commit

echo "[2/4] Phase 2: Deep Research..."
python -m hermes_social.cli research --all

echo "[3/4] Phase 3: Generating Post Content..."
python -m hermes_social.cli generate --all

echo "[4/4] Phase 4: Designing & Sending to Telegram..."
python -m hermes_social.cli design --all

echo "====================================================="
echo "Daily pipeline complete! Check Telegram for the pending post."
echo "====================================================="
