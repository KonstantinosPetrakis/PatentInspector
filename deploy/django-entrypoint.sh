#!/bin/bash
set -e # Exit immediately if a command exits with a non-zero status.

# Wait for Postgres to start completely
echo "Waiting for postgres"
while ! nc -z postgres 5432; do sleep 1; done;

cd patentanalyzer
python3 -m gunicorn -w 8 -b 0.0.0.0:8000 --timeout 600 --capture-output --log-level debug PatentAnalyzer.wsgi 