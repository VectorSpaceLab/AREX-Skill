#!/usr/bin/env bash
set -euo pipefail

# Smoke launcher for Align-Anything remote reward servers.
#
# Default behavior:
# - starts `python -m align_anything.models.remote_rm.run_reward_server`
# - waits for Flask readiness
# - probes the `/get_reward` endpoint with a known-good payload
# - leaves the server running on success

REWARD_HOST="${REWARD_HOST:-0.0.0.0}"
REWARD_PORT="${REWARD_PORT:-6000}"
REWARD_TYPE="${REWARD_TYPE:-math_verifier}"
DATASET_PATH="${DATASET_PATH:-}"
OUTPUT_DIR="${OUTPUT_DIR:-./debug_logs}"
STARTUP_WAIT_SECONDS="${STARTUP_WAIT_SECONDS:-20}"
PROBE_ENDPOINT="${PROBE_ENDPOINT:-http://127.0.0.1:${REWARD_PORT}/get_reward}"
PROBE_PROMPT="${PROBE_PROMPT:-How many vertical asymptotes does the graph of y=2/(x^2+x-6) have?}"
PROBE_GOLDEN_RESPONSE="${PROBE_GOLDEN_RESPONSE:-2}"
PROBE_RESPONSE="${PROBE_RESPONSE:-<think>Factor the denominator.</think><answer>${PROBE_GOLDEN_RESPONSE}</answer>}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p "$OUTPUT_DIR"

# If math_verifier is selected and no dataset was supplied, bootstrap a tiny
# self-contained dataset so the smoke test can run without any source checkout data.
BOOTSTRAP_DATASET_PATH="$OUTPUT_DIR/remote_rm_smoke_dataset.json"
if [[ "$REWARD_TYPE" == "math_verifier" && -z "$DATASET_PATH" ]]; then
  python - "$BOOTSTRAP_DATASET_PATH" "$PROBE_PROMPT" "$PROBE_GOLDEN_RESPONSE" <<'PY'
import json
import sys

path, prompt, answer = sys.argv[1:4]
with open(path, 'w', encoding='utf-8') as f:
    json.dump([{'question': prompt, 'answer': answer}], f, ensure_ascii=False, indent=2)
PY
  DATASET_PATH="$BOOTSTRAP_DATASET_PATH"
  echo "No DATASET_PATH supplied; using smoke dataset: $DATASET_PATH"
fi

if command -v lsof >/dev/null 2>&1; then
  existing_pid="$(lsof -ti :"$REWARD_PORT" 2>/dev/null | head -n 1 || true)"
  if [[ -n "$existing_pid" ]]; then
    echo "Port $REWARD_PORT is already in use by PID $existing_pid; stopping it first."
    kill "$existing_pid" 2>/dev/null || true
    sleep 1
  fi
fi

server_cmd=(
  python -m align_anything.models.remote_rm.run_reward_server
  --host "$REWARD_HOST"
  --port "$REWARD_PORT"
  --reward-type "$REWARD_TYPE"
)
if [[ -n "$DATASET_PATH" ]]; then
  server_cmd+=(--dataset "$DATASET_PATH")
fi

echo "Starting remote reward server..."
"${server_cmd[@]}" >"$OUTPUT_DIR/reward_server.log" 2>&1 &
SERVER_PID=$!
echo "Reward server PID: $SERVER_PID"

echo "Waiting up to ${STARTUP_WAIT_SECONDS}s for Flask readiness..."
ready=0
for _ in $(seq 1 "$STARTUP_WAIT_SECONDS"); do
  if grep -q "Running on" "$OUTPUT_DIR/reward_server.log" 2>/dev/null; then
    ready=1
    break
  fi
  sleep 1
done

if [[ "$ready" -ne 1 ]]; then
  echo "Server did not reach readiness. Log follows:"
  cat "$OUTPUT_DIR/reward_server.log"
  kill "$SERVER_PID" 2>/dev/null || true
  exit 1
fi

echo "Probing reward endpoint: $PROBE_ENDPOINT"
python "$SCRIPT_DIR/probe_remote_rm_payload.py" \
  --endpoint "$PROBE_ENDPOINT" \
  --prompt "$PROBE_PROMPT" \
  --response "$PROBE_RESPONSE" \
  --golden-response "$PROBE_GOLDEN_RESPONSE"

echo "Remote reward server is ready."
echo "Server log: $OUTPUT_DIR/reward_server.log"
echo "PPO pattern: export REMOTE_RM_URL=\"$PROBE_ENDPOINT\" and launch deepspeed --module align_anything.trainers.text_to_text.ppo_remote_rm ..."
