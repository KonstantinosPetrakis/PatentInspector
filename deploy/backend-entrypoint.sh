#!/bin/bash
set -e # Exit immediately if a command exits with a non-zero status.

# Wait for Postgres to start completely
echo "Waiting for postgres"
while ! nc -z postgres 5432; do sleep 1; done

cd patentinspector
python3 -m gunicorn -w $GUNICORN_WORKERS -b 0.0.0.0:8000 --timeout $GUNICRON_TIMEOUT --capture-output --log-level debug PatentInspector.wsgi & python3 manage.py qcluster
