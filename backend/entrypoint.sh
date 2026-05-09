#!/bin/sh
# Apply any pending database migrations before starting the API.
# Idempotent: a no-op once the DB is at head.
set -e

alembic upgrade head

exec "$@"
