#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: presidio_cli_smoke.sh [--presidio-bin PATH] [--skip-scan]

Checks the Presidio CLI help output and, by default, runs a tiny scan against a
temporary file and temporary YAML config.

Options:
  --presidio-bin PATH  Presidio CLI executable to run (default: presidio)
  --skip-scan          Only run the help check
  -h, --help           Show this help
EOF
}

presidio_bin="${PRESIDIO_BIN:-presidio}"
skip_scan=0

while (($#)); do
  case "$1" in
    --presidio-bin)
      shift
      if (($# == 0)); then
        echo "--presidio-bin expects a value" >&2
        exit 2
      fi
      presidio_bin="$1"
      ;;
    --skip-scan)
      skip_scan=1
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
  shift
done

if ! command -v "$presidio_bin" >/dev/null 2>&1; then
  echo "Presidio CLI not found: $presidio_bin" >&2
  exit 1
fi

"$presidio_bin" --help >/dev/null

if (( skip_scan )); then
  printf 'Presidio CLI help check passed.\n'
  exit 0
fi

tmpdir="$(mktemp -d)"
cleanup() {
  rm -rf "$tmpdir"
}
trap cleanup EXIT

cat > "$tmpdir/sample_presidiocli.yaml" <<'YAML'
language: en
entities:
  - PERSON
  - EMAIL_ADDRESS
threshold: 0.0
YAML

cat > "$tmpdir/sample.txt" <<'EOF'
John Smith
jane.doe@example.com
EOF

"$presidio_bin" -c "$tmpdir/sample_presidiocli.yaml" --format parsable "$tmpdir/sample.txt" > "$tmpdir/output.jsonl"
grep -q '"entity_type":' "$tmpdir/output.jsonl"

printf 'Presidio CLI smoke checks passed.\n'