#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: start_server.sh --model-cls MODEL_CLS --task TASK --model-path PATH --config-json PATH [--host HOST] [--port PORT]

Starts the LightX2V FastAPI server with explicit arguments.
EOF
}

model_cls=""
task=""
model_path=""
config_json=""
host="0.0.0.0"
port="8000"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --model-cls)
      model_cls="$2"
      shift 2
      ;;
    --task)
      task="$2"
      shift 2
      ;;
    --model-path)
      model_path="$2"
      shift 2
      ;;
    --config-json)
      config_json="$2"
      shift 2
      ;;
    --host)
      host="$2"
      shift 2
      ;;
    --port)
      port="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 2
      ;;
  esac
done

if [[ -z "$model_cls" || -z "$task" || -z "$model_path" || -z "$config_json" ]]; then
  usage
  exit 2
fi

python -m lightx2v.server \
  --model_cls "$model_cls" \
  --task "$task" \
  --model_path "$model_path" \
  --config_json "$config_json" \
  --host "$host" \
  --port "$port"
