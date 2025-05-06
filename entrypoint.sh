#!/bin/sh
set -e

case "$1" in
  api)
    exec uvicorn porc_api.main:app --host 0.0.0.0 --port 8000
    ;;
  worker)
    exec python -m porc_worker.main
    ;;
  shell)
    exec /bin/sh
    ;;
  *)
    exec "$@"
    ;;
esac