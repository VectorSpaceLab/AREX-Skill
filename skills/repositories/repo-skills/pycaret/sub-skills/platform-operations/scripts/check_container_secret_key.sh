#!/usr/bin/env bash
# Check or create the persisted Fernet key used by the PyCaret API container.
# This script never prints key material. It mutates the target only with --create.

set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: check_container_secret_key.sh --data-dir DIR [--key-file FILE] [--create]

Validate the Fernet key persistence layout used by the PyCaret API container.
By default the key file is DIR/.secrets/fernet.key. The script checks whether
PYCARET_SECRETS_KEY is set, whether the persisted key exists, whether key
material has Fernet format, and whether file permissions are too broad. It does
not print key values.

Options:
  --data-dir DIR    Data directory or mounted volume root to inspect.
  --key-file FILE   Override key file path. Relative paths are resolved under DIR.
  --create          If the key file is missing, create it with mode 0600.
  -h, --help        Show this help.

Exit codes:
  0  checks passed
  1  check failed or key missing without --create
  2  usage error
USAGE
}

DATA_DIR=""
KEY_FILE=""
CREATE=0

while [ "$#" -gt 0 ]; do
  case "$1" in
    --data-dir)
      [ "$#" -ge 2 ] || { echo "--data-dir requires a value" >&2; exit 2; }
      DATA_DIR="$2"
      shift 2
      ;;
    --key-file)
      [ "$#" -ge 2 ] || { echo "--key-file requires a value" >&2; exit 2; }
      KEY_FILE="$2"
      shift 2
      ;;
    --create)
      CREATE=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [ -z "$DATA_DIR" ]; then
  echo "--data-dir is required" >&2
  usage >&2
  exit 2
fi

if [ -z "$KEY_FILE" ]; then
  KEY_FILE="$DATA_DIR/.secrets/fernet.key"
else
  case "$KEY_FILE" in
    /*) ;;
    *) KEY_FILE="$DATA_DIR/$KEY_FILE" ;;
  esac
fi

PYTHON_BIN="${PYTHON:-python3}"

validate_key() {
  # Reads key from stdin. Prints only OK/FAIL detail, never the key.
  "$PYTHON_BIN" -c '
import sys
try:
    from cryptography.fernet import Fernet
except Exception as exc:
    print(f"FAIL cryptography import failed: {type(exc).__name__}: {exc}")
    raise SystemExit(1)
label = sys.argv[1]
key = sys.stdin.read().strip()
if not key:
    print(f"FAIL {label} is empty")
    raise SystemExit(1)
try:
    Fernet(key.encode("utf-8"))
except Exception as exc:
    print(f"FAIL {label} is not a valid Fernet key: {type(exc).__name__}")
    raise SystemExit(1)
print(f"OK {label} has valid Fernet format")
' "$1"
}

status=0

echo "PyCaret container Fernet key check"
echo "data dir: $DATA_DIR"
echo "key file: $KEY_FILE"

if [ -n "${PYCARET_SECRETS_KEY:-}" ]; then
  printf '%s' "$PYCARET_SECRETS_KEY" | validate_key "PYCARET_SECRETS_KEY" || status=1
else
  echo "INFO PYCARET_SECRETS_KEY is not set in the current shell"
fi

if [ -f "$KEY_FILE" ]; then
  validate_key "persisted key file" < "$KEY_FILE" || status=1
  if command -v stat >/dev/null 2>&1; then
    mode="$(stat -c '%a' "$KEY_FILE" 2>/dev/null || stat -f '%Lp' "$KEY_FILE" 2>/dev/null || true)"
    if [ -n "$mode" ]; then
      case "$mode" in
        600|400) echo "OK key file mode is $mode" ;;
        *) echo "WARN key file mode is $mode; expected 0600 or stricter" ;;
      esac
    fi
  fi
  if [ -n "${PYCARET_SECRETS_KEY:-}" ]; then
    if [ "$(cat "$KEY_FILE")" = "$PYCARET_SECRETS_KEY" ]; then
      echo "OK environment key matches persisted key file"
    else
      echo "WARN environment key differs from persisted key file; container entrypoint prefers the environment key"
    fi
  fi
else
  if [ "$CREATE" -eq 1 ]; then
    umask 077
    mkdir -p "$(dirname "$KEY_FILE")"
    "$PYTHON_BIN" - <<'PY' > "$KEY_FILE"
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
PY
    chmod 600 "$KEY_FILE"
    echo "OK created persisted key file with mode 0600"
    validate_key "created key file" < "$KEY_FILE" || status=1
  else
    echo "FAIL persisted key file is missing; pass --create to create it"
    status=1
  fi
fi

exit "$status"
