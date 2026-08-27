#!/usr/bin/env bash
set -euo pipefail

DEFAULT_MODEL_ID='VLM-R1-Qwen2.5VL-3B-OVD-0321'
ENGINE='vllm'
ACTION=''
HARDWARE='a2'
MODEL_PATH="${DEFAULT_MODEL_ID}"
MODEL_ID="${DEFAULT_MODEL_ID}"
HOST='0.0.0.0'
CLIENT_HOST='localhost'
PORT='8000'
MAX_MODEL_LEN='16384'
LIMIT_IMAGES='10'
DTYPE=''
XLLM_BINARY='./build/xllm/core/server/xllm'
MAX_MEMORY_UTILIZATION='0.90'
IMAGE_URL='https://example.invalid/image.jpg'
DESCRIBE='杯子在哪个位置？请输出杯子的bbox坐标。'
EVENT='杯子'
MAX_TOKENS='512'
INCLUDE_FUNCTION_TAGS='0'

usage() {
  cat <<'USAGE'
Render VLM-R1 Ascend server/client command templates without executing them.

Usage:
  ascend_server_client_templates.sh --engine vllm --action server [options]
  ascend_server_client_templates.sh --engine vllm --action client [options]
  ascend_server_client_templates.sh --engine xllm --action server [options]
  ascend_server_client_templates.sh --engine xllm --action client [options]

Core options:
  --engine vllm|xllm              Inference engine to render for (default: vllm).
  --action server|client          Command family to render (required).
  --hardware a2|300iduo           Ascend target recipe (default: a2).
  --model-path VALUE              Local/container-visible checkpoint path.
  --model-id VALUE                Model id sent in OpenAI-compatible requests.
  --port VALUE                    Service port (default: 8000).

vllm-ascend server options:
  --host VALUE                    Server bind host (default: 0.0.0.0).
  --max-model-len VALUE           vLLM max model length (default: 16384).
  --limit-images VALUE            vLLM image limit per prompt (default: 10).
  --dtype VALUE                   Optional dtype override; 300iduo defaults to float16.

XLLM server options:
  --xllm-binary VALUE             Built XLLM executable path (default: ./build/xllm/core/server/xllm).
  --max-memory-utilization VALUE  XLLM memory cap (default: 0.90).

Client request options:
  --client-host VALUE             Client target host (default: localhost).
  --image-url VALUE               Image URL for online multimodal chat.
  --describe VALUE                Chinese object/event query.
  --event VALUE                   Object/event name inserted into yes/no prompt.
  --max-tokens VALUE              Chat completion max_tokens field (default: 512).
  --include-function-tags         Add FunctionCallBegin/FunctionCallEnd sentinels around JSON example.

Examples:
  # Atlas 300I Duo vllm-ascend server; dtype float16 is added by default.
  ascend_server_client_templates.sh --engine vllm --action server --hardware 300iduo --model-path ./VLM-R1-Qwen2.5VL-3B-OVD-0321 --port 8000

  # XLLM VLM server on Atlas 800T A2 / 910B.
  ascend_server_client_templates.sh --engine xllm --action server --xllm-binary ./build/xllm/core/server/xllm --model-path ./VLM-R1-Qwen2.5VL-3B-OVD-0321 --model-id VLM-R1-Qwen2.5VL-3B-OVD-0321 --port 8010

  # OpenAI-compatible multimodal client request.
  ascend_server_client_templates.sh --engine xllm --action client --client-host localhost --port 8010 --image-url https://example.invalid/image.jpg --describe '杯子在哪个位置？' --event '杯子'
USAGE
}

die() {
  printf 'error: %s\n' "$*" >&2
  exit 2
}

shell_quote() {
  printf '%q' "$1"
}

json_escape() {
  python3 -c 'import json, sys; print(json.dumps(sys.stdin.read(), ensure_ascii=False)[1:-1])'
}

build_prompt() {
  local begin=''
  local end=''
  if [[ "${INCLUDE_FUNCTION_TAGS}" == '1' ]]; then
    begin='<|FunctionCallBegin|>\n'
    end='\n<|FunctionCallEnd|>'
  fi
  cat <<EOF
请分析图像并回答以下问题。您的回答应包含对图像内容的简要描述和最终答案。描述使用 \`<description></description>\` 标签包裹。答案必须以 JSON 格式输出，包含 "answer"（"yes" 或 "no"），并提供相关物体的边界框坐标作为解释。如果没有涉及具体物体，则将 "explanations" 设为 "None"。输出格式如下：

<description>对图像内容的简要描述写在这里</description>

${begin}\`\`\`json
{"answer": "yes or no", "explanations": [{"bbox_2d": [xx, xx, xx, xx], "label": "xxx"}]}
\`\`\`${end}

具体问题:根据规则或识别要求，${DESCRIBE}。图中是否出现${EVENT}？
EOF
}

render_vllm_server() {
  local dtype="${DTYPE}"
  if [[ -z "${dtype}" && "${HARDWARE}" == '300iduo' ]]; then
    dtype='float16'
  fi

  printf 'vllm serve %s \\\n' "$(shell_quote "${MODEL_PATH}")"
  printf '  --max-model-len %s \\\n' "$(shell_quote "${MAX_MODEL_LEN}")"
  printf '  --limit-mm-per-prompt '\''{"image": %s}'\'' \\\n' "${LIMIT_IMAGES}"
  if [[ -n "${dtype}" ]]; then
    printf '  --dtype %s \\\n' "$(shell_quote "${dtype}")"
  fi
  printf '  --enforce-eager \\\n'
  printf '  --port %s \\\n' "$(shell_quote "${PORT}")"
  printf '  --host %s \\\n' "$(shell_quote "${HOST}")"
  printf '  --trust-remote-code\n'
}

render_xllm_server() {
  printf '%s \\\n' "$(shell_quote "${XLLM_BINARY}")"
  printf '  --model=%s \\\n' "$(shell_quote "${MODEL_PATH}")"
  printf '  --backend=vlm \\\n'
  printf '  --port=%s \\\n' "$(shell_quote "${PORT}")"
  printf '  --max_memory_utilization %s \\\n' "$(shell_quote "${MAX_MEMORY_UTILIZATION}")"
  printf '  --model_id=%s\n' "$(shell_quote "${MODEL_ID}")"
}

render_client() {
  local prompt escaped_prompt escaped_image_url escaped_model_id
  prompt="$(build_prompt)"
  escaped_prompt="$(printf '%s' "${prompt}" | json_escape)"
  escaped_image_url="$(printf '%s' "${IMAGE_URL}" | json_escape)"
  escaped_model_id="$(printf '%s' "${MODEL_ID}" | json_escape)"

  cat <<EOF
curl -X POST "http://${CLIENT_HOST}:${PORT}/v1/chat/completions" \\
  -H "Content-Type: application/json" \\
  -d '{
    "model": "${escaped_model_id}",
    "max_tokens": ${MAX_TOKENS},
    "messages": [
      {
        "role": "user",
        "content": [
          {
            "type": "image_url",
            "image_url": {"url": "${escaped_image_url}"}
          },
          {
            "type": "text",
            "text": "${escaped_prompt}"
          }
        ]
      }
    ]
  }'
EOF
}

if [[ $# -eq 0 ]]; then
  usage
  exit 0
fi

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help)
      usage
      exit 0
      ;;
    --engine)
      ENGINE="${2:-}"
      shift 2
      ;;
    --action)
      ACTION="${2:-}"
      shift 2
      ;;
    --hardware)
      HARDWARE="${2:-}"
      shift 2
      ;;
    --model-path)
      MODEL_PATH="${2:-}"
      shift 2
      ;;
    --model-id)
      MODEL_ID="${2:-}"
      shift 2
      ;;
    --host)
      HOST="${2:-}"
      shift 2
      ;;
    --client-host)
      CLIENT_HOST="${2:-}"
      shift 2
      ;;
    --port)
      PORT="${2:-}"
      shift 2
      ;;
    --max-model-len)
      MAX_MODEL_LEN="${2:-}"
      shift 2
      ;;
    --limit-images)
      LIMIT_IMAGES="${2:-}"
      shift 2
      ;;
    --dtype)
      DTYPE="${2:-}"
      shift 2
      ;;
    --xllm-binary)
      XLLM_BINARY="${2:-}"
      shift 2
      ;;
    --max-memory-utilization)
      MAX_MEMORY_UTILIZATION="${2:-}"
      shift 2
      ;;
    --image-url)
      IMAGE_URL="${2:-}"
      shift 2
      ;;
    --describe)
      DESCRIBE="${2:-}"
      shift 2
      ;;
    --event)
      EVENT="${2:-}"
      shift 2
      ;;
    --max-tokens)
      MAX_TOKENS="${2:-}"
      shift 2
      ;;
    --include-function-tags)
      INCLUDE_FUNCTION_TAGS='1'
      shift
      ;;
    *)
      die "unknown option: $1"
      ;;
  esac
done

case "${ENGINE}" in
  vllm|xllm) ;;
  *) die "--engine must be vllm or xllm" ;;
esac

case "${ACTION}" in
  server|client) ;;
  '') die "--action server|client is required" ;;
  *) die "--action must be server or client" ;;
esac

case "${HARDWARE}" in
  a2|300iduo) ;;
  *) die "--hardware must be a2 or 300iduo" ;;
esac

if [[ "${ACTION}" == 'server' ]]; then
  if [[ "${ENGINE}" == 'vllm' ]]; then
    render_vllm_server
  else
    render_xllm_server
  fi
else
  render_client
fi
