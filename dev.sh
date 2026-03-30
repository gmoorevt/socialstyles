#!/bin/bash
set -e

# Local dev environment: PostgreSQL + Flask in Docker
# Usage:
#   ./dev.sh          - start (build + migrate + seed)
#   ./dev.sh stop     - stop
#   ./dev.sh logs     - tail logs
#   ./dev.sh reset    - wipe DB and start fresh

DC="docker compose -f docker-compose.dev.yml"

case "${1:-start}" in
  start)
    echo "==> Starting local dev environment..."
    $DC up -d --build

    echo "==> Waiting for database..."
    sleep 3

    echo "==> Running migrations..."
    $DC exec web flask db upgrade

    echo "==> Initializing assessment questions..."
    $DC exec web python manage.py init-assessment || true

    echo "==> Ready at http://localhost:5001"
    ;;
  stop)
    $DC down
    echo "==> Stopped."
    ;;
  logs)
    $DC logs -f web
    ;;
  reset)
    $DC down -v
    echo "==> Database wiped. Run ./dev.sh to start fresh."
    ;;
  *)
    echo "Usage: ./dev.sh [start|stop|logs|reset]"
    ;;
esac
