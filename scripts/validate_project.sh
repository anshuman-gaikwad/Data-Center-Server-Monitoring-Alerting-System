#!/usr/bin/env bash
set -e
echo "Checking project files..."
test -f docker-compose.yml
test -f monitoring/prometheus/prometheus.yml
test -f monitoring/prometheus/rules/server_alerts.yml
test -f backend/app.py
test -f frontend/src/main.jsx
echo "All core files are present."
echo "Run: docker compose config"
