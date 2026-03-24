#!/bin/bash
# Dashboard service lifecycle management.
# Usage: server.sh start|stop|status|restart [--port PORT]

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PORT="${DASHBOARD_PORT:-8888}"

# Parse --port argument (before setting PID/LOG paths)
while [[ $# -gt 0 ]]; do
    case "$1" in
        start|stop|status|restart) CMD="$1"; shift ;;
        --port) PORT="$2"; shift 2 ;;
        *) CMD="$1"; shift ;;
    esac
done

CMD="${CMD:-status}"
PID_FILE="${HOME}/.claude/dashboard-${PORT}.pid"
LOG_FILE="${HOME}/.claude/dashboard-${PORT}.log"

_is_running() {
    if [ -f "$PID_FILE" ]; then
        local pid
        pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            return 0
        fi
    fi
    return 1
}

_start() {
    if _is_running; then
        local pid
        pid=$(cat "$PID_FILE")
        echo "Dashboard already running (PID $pid) on port $PORT"
        echo "  http://127.0.0.1:$PORT"
        return 0
    fi

    mkdir -p "$(dirname "$PID_FILE")"

    echo "Starting dashboard service on port $PORT..."
    DASHBOARD_PORT="$PORT" python3 -m services.dashboard.app \
        > "$LOG_FILE" 2>&1 &
    local pid=$!
    echo "$pid" > "$PID_FILE"

    # Wait briefly for startup
    sleep 1
    if kill -0 "$pid" 2>/dev/null; then
        echo "Dashboard running (PID $pid)"
        echo "  http://127.0.0.1:$PORT"
        # Open in browser on macOS
        if command -v open &>/dev/null; then
            open "http://127.0.0.1:$PORT"
        fi
    else
        echo "Failed to start. Check $LOG_FILE"
        rm -f "$PID_FILE"
        return 1
    fi
}

_stop() {
    if ! _is_running; then
        echo "Dashboard not running."
        rm -f "$PID_FILE"
        return 0
    fi

    local pid
    pid=$(cat "$PID_FILE")
    echo "Stopping dashboard (PID $pid)..."
    kill "$pid" 2>/dev/null || true
    rm -f "$PID_FILE"
    echo "Stopped."
}

_status() {
    if _is_running; then
        local pid
        pid=$(cat "$PID_FILE")
        echo "Dashboard running (PID $pid)"
        echo "  http://127.0.0.1:$PORT"
    else
        echo "Dashboard not running."
        rm -f "$PID_FILE"
    fi
}

case "$CMD" in
    start) _start ;;
    stop) _stop ;;
    status) _status ;;
    restart) _stop; sleep 1; _start ;;
    *) echo "Usage: $(basename "$0") start|stop|status|restart [--port PORT]"; exit 1 ;;
esac
