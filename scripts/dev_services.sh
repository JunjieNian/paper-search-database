#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_DIR="$ROOT_DIR/.run"
LOG_DIR="$ROOT_DIR/logs/dev-services"
PID_FILE="$RUN_DIR/pids.env"

ALGO_HOST="${ALGO_HOST:-0.0.0.0}"
ALGO_PORT="${ALGO_PORT:-8003}"
BACKEND_HOST="${BACKEND_HOST:-0.0.0.0}"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_HOST="${FRONTEND_HOST:-0.0.0.0}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
NPM_BIN="${NPM_BIN:-npm}"

mkdir -p "$RUN_DIR" "$LOG_DIR"

is_pid_running() {
  local pid="$1"
  [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null
}

find_pid_by_pattern() {
  local pattern="$1"
  pgrep -f "$pattern" | tail -n 1 || true
}

start_detached() {
  local workdir="$1"
  local log_file="$2"
  shift 2
  (
    cd "$workdir"
    setsid "$@" > "$log_file" 2>&1 < /dev/null &
  )
}

wait_for_url() {
  local name="$1"
  local url="$2"
  local timeout="${3:-60}"
  local started_at
  started_at="$(date +%s)"

  while true; do
    if curl -fsS "$url" >/dev/null 2>&1; then
      echo "[ok] $name ready: $url"
      return 0
    fi
    if (( $(date +%s) - started_at >= timeout )); then
      echo "[fail] timed out waiting for $name: $url"
      return 1
    fi
    sleep 1
  done
}

write_pid_file() {
  cat > "$PID_FILE" <<EOF_PIDS
ALGO_PID=$1
BACKEND_PID=$2
FRONTEND_PID=$3
EOF_PIDS
}

load_pid_file() {
  if [[ -f "$PID_FILE" ]]; then
    # shellcheck disable=SC1090
    source "$PID_FILE"
  else
    ALGO_PID=""
    BACKEND_PID=""
    FRONTEND_PID=""
  fi
}

start_services() {
  load_pid_file
  if is_pid_running "${ALGO_PID:-}" || is_pid_running "${BACKEND_PID:-}" || is_pid_running "${FRONTEND_PID:-}"; then
    echo "[info] existing service pids detected, stopping them first"
    stop_services
  fi

  echo "[info] starting backend_algo on :$ALGO_PORT"
  start_detached "$ROOT_DIR/backend_algo" "$LOG_DIR/backend_algo.log" "$PYTHON_BIN" -m uvicorn main:app --host "$ALGO_HOST" --port "$ALGO_PORT"

  echo "[info] starting backend on :$BACKEND_PORT"
  start_detached "$ROOT_DIR/backend" "$LOG_DIR/backend.log" "$PYTHON_BIN" -m uvicorn main:app --host "$BACKEND_HOST" --port "$BACKEND_PORT"

  echo "[info] starting frontend on :$FRONTEND_PORT"
  start_detached "$ROOT_DIR/frontend" "$LOG_DIR/frontend.log" "$NPM_BIN" run dev -- --host "$FRONTEND_HOST" --port "$FRONTEND_PORT"

  wait_for_url "backend_algo" "http://127.0.0.1:${ALGO_PORT}/docs" 90
  wait_for_url "backend" "http://127.0.0.1:${BACKEND_PORT}/docs" 90
  wait_for_url "frontend" "http://127.0.0.1:${FRONTEND_PORT}" 90

  local algo_pid backend_pid frontend_pid
  algo_pid="$(find_pid_by_pattern "uvicorn main:app --host $ALGO_HOST --port $ALGO_PORT")"
  backend_pid="$(find_pid_by_pattern "uvicorn main:app --host $BACKEND_HOST --port $BACKEND_PORT")"
  frontend_pid="$(find_pid_by_pattern "vite --host $FRONTEND_HOST --port $FRONTEND_PORT")"

  write_pid_file "$algo_pid" "$backend_pid" "$frontend_pid"

  echo "[done] all services started"
  status_services
}

stop_pid() {
  local name="$1"
  local pid="$2"
  if is_pid_running "$pid"; then
    kill "$pid" 2>/dev/null || true
    for _ in {1..20}; do
      if ! is_pid_running "$pid"; then
        echo "[ok] stopped $name ($pid)"
        return 0
      fi
      sleep 0.5
    done
    kill -9 "$pid" 2>/dev/null || true
    echo "[warn] force killed $name ($pid)"
  else
    echo "[info] $name not running"
  fi
}

stop_services() {
  load_pid_file
  stop_pid "frontend" "${FRONTEND_PID:-}"
  stop_pid "backend" "${BACKEND_PID:-}"
  stop_pid "backend_algo" "${ALGO_PID:-}"
  rm -f "$PID_FILE" "$RUN_DIR"/*.pid
}

status_services() {
  load_pid_file
  echo "backend_algo : pid=${ALGO_PID:-none} status=$([[ -n "${ALGO_PID:-}" ]] && is_pid_running "$ALGO_PID" && echo running || echo stopped) url=http://127.0.0.1:${ALGO_PORT}/docs"
  echo "backend      : pid=${BACKEND_PID:-none} status=$([[ -n "${BACKEND_PID:-}" ]] && is_pid_running "$BACKEND_PID" && echo running || echo stopped) url=http://127.0.0.1:${BACKEND_PORT}/docs"
  echo "frontend     : pid=${FRONTEND_PID:-none} status=$([[ -n "${FRONTEND_PID:-}" ]] && is_pid_running "$FRONTEND_PID" && echo running || echo stopped) url=http://127.0.0.1:${FRONTEND_PORT}"
}

check_services() {
  wait_for_url "backend_algo" "http://127.0.0.1:${ALGO_PORT}/docs" 10
  wait_for_url "backend" "http://127.0.0.1:${BACKEND_PORT}/docs" 10
  wait_for_url "frontend" "http://127.0.0.1:${FRONTEND_PORT}" 10
}

case "${1:-start}" in
  start)
    start_services
    ;;
  stop)
    stop_services
    ;;
  restart)
    stop_services
    start_services
    ;;
  status)
    status_services
    ;;
  check)
    check_services
    ;;
  *)
    echo "usage: $0 {start|stop|restart|status|check}"
    exit 1
    ;;
esac
