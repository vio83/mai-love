#!/usr/bin/env bash
# GIU-L_IA Launcher — VIO83 AI Orchestra
# Manage multi-instance deployment: DEMO (9443), PROTOTIPO (9444), or both

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEMO_PORT=9443
PROTO_PORT=9444
MODE="${1:-both}"
VERBOSE="${VERBOSE:-}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $*"; }
log_ok() { echo -e "${GREEN}[OK]${NC} $*"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_err() { echo -e "${RED}[ERR]${NC} $*"; }

usage() {
  cat >&2 <<EOF
Usage: $0 [OPTIONS]

Options:
  --mode demo      Start only DEMO instance (port 9443)
  --mode proto     Start only PROTOTIPO instance (port 9444)
  --mode both      Start both instances (default)
  --kill           Kill all GIU-L_IA instances gracefully
  --status         Show status of instances
  --verbose        Show additional debug info
  --help           Show this help

Examples:
  $0 --mode demo              # Start DEMO on 9443
  $0 --mode proto             # Start PROTOTIPO on 9444
  $0 --mode both              # Start both (default)
  $0 --status                 # Check instance status
  $0 --kill                   # Kill all instances
EOF
  exit 1
}

# Parse arguments
ACTION="start"
if [[ $# -gt 0 ]]; then
  case "${1:-}" in
    --help) usage ;;
    --kill) ACTION="kill" ;;
    --status) ACTION="status" ;;
    --verbose) VERBOSE=1 ;;
    --mode)
      if [[ $# -lt 2 ]]; then
        log_err "Missing mode value"
        usage
      fi
      MODE="$2"
      shift 2
      ;;
    *)
      log_err "Unknown option: $1"
      usage
      ;;
  esac
fi

[ "$VERBOSE" = "1" ] && log_info "ACTION=$ACTION MODE=$MODE"

# Helper: check if port is in use
port_in_use() {
  local port=$1
  lsof -ti:$port >/dev/null 2>&1
}

# Helper: get PID on port
get_pid_on_port() {
  local port=$1
  lsof -ti:$port 2>/dev/null || echo ""
}

# Helper: wait for port to be ready
wait_port_ready() {
  local port=$1
  local name=$2
  local attempt=0
  while [[ $attempt -lt 15 ]]; do
    if curl -s --max-time 2 http://127.0.0.1:$port/ >/dev/null 2>&1; then
      log_ok "$name ready on port $port"
      return 0
    fi
    sleep 1
    ((attempt++))
  done
  log_warn "$name on port $port not responding after 15s"
  return 1
}

##############################
# STATUS
##############################
show_status() {
  log_info "=== GIU-L_IA Instance Status ==="

  local demo_pid=$(get_pid_on_port $DEMO_PORT)
  local proto_pid=$(get_pid_on_port $PROTO_PORT)

  if [[ -n "$demo_pid" ]]; then
    log_ok "DEMO (port $DEMO_PORT): PID $demo_pid"
  else
    log_warn "DEMO (port $DEMO_PORT): NOT RUNNING"
  fi

  if [[ -n "$proto_pid" ]]; then
    log_ok "PROTOTIPO (port $PROTO_PORT): PID $proto_pid"
  else
    log_warn "PROTOTIPO (port $PROTO_PORT): NOT RUNNING"
  fi

  echo ""
  log_info "=== Quick Health Checks ==="
  curl -s -o /dev/null -w "  DEMO (9443): %{http_code}\n" --max-time 2 http://127.0.0.1:$DEMO_PORT/ || echo "  DEMO (9443): UNREACHABLE"
  curl -s -o /dev/null -w "  PROTOTIPO (9444): %{http_code}\n" --max-time 2 http://127.0.0.1:$PROTO_PORT/ || echo "  PROTOTIPO (9444): UNREACHABLE"
}

##############################
# KILL
##############################
kill_instances() {
  log_info "Stopping GIU-L_IA instances..."

  local demo_pid=$(get_pid_on_port $DEMO_PORT)
  local proto_pid=$(get_pid_on_port $PROTO_PORT)

  if [[ -n "$demo_pid" ]]; then
    log_info "Stopping DEMO (PID $demo_pid)..."
    kill $demo_pid 2>/dev/null || true
    sleep 1
    if port_in_use $DEMO_PORT; then
      log_warn "Port $DEMO_PORT still in use, force killing..."
      kill -9 $demo_pid 2>/dev/null || true
    fi
  fi

  if [[ -n "$proto_pid" ]]; then
    log_info "Stopping PROTOTIPO (PID $proto_pid)..."
    kill $proto_pid 2>/dev/null || true
    sleep 1
    if port_in_use $PROTO_PORT; then
      log_warn "Port $PROTO_PORT still in use, force killing..."
      kill -9 $proto_pid 2>/dev/null || true
    fi
  fi

  sleep 1

  if port_in_use $DEMO_PORT || port_in_use $PROTO_PORT; then
    log_err "Failed to stop instances"
    return 1
  fi

  log_ok "All instances stopped"
  return 0
}

##############################
# START
##############################
start_instance() {
  local port=$1
  local name=$2

  if port_in_use $port; then
    local pid=$(get_pid_on_port $port)
    log_warn "$name (port $port) already running (PID $pid)"
    return 0
  fi

  log_info "Starting $name on port $port..."

  cd "$SCRIPT_DIR"
  PORT=$port python3 brace-v3/webui.py >/tmp/giu_${name}_${port}.log 2>&1 &
  local pid=$!

  [ "$VERBOSE" = "1" ] && log_info "Spawned PID $pid, waiting for readiness..."

  sleep 2

  if ! wait_port_ready $port "$name"; then
    log_err "$name failed to start. Check log: /tmp/giu_${name}_${port}.log"
    return 1
  fi

  log_ok "$name running (PID $pid)"
  return 0
}

start_mode() {
  case "$MODE" in
    demo)
      start_instance $DEMO_PORT "DEMO" || return 1
      ;;
    proto)
      start_instance $PROTO_PORT "PROTOTIPO" || return 1
      ;;
    both)
      start_instance $DEMO_PORT "DEMO" || return 1
      start_instance $PROTO_PORT "PROTOTIPO" || return 1
      ;;
    *)
      log_err "Invalid mode: $MODE (valid: demo, proto, both)"
      return 1
      ;;
  esac

  echo ""
  show_status
}

##############################
# MAIN
##############################
main() {
  case "$ACTION" in
    start) start_mode ;;
    kill) kill_instances ;;
    status) show_status ;;
    *)
      log_err "Unknown action: $ACTION"
      return 1
      ;;
  esac
}

main "$@"
