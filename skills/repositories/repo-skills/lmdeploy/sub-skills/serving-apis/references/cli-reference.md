# LMDeploy Serving CLI Reference

This reference summarizes the serving command surface used to publish LMDeploy engines as HTTP APIs.

## `lmdeploy serve api_server`

Basic form:

```bash
lmdeploy serve api_server <model_path> [options]
```

`model_path` may be a local model directory, a converted TurboMind model directory, an LMDeploy-quantized model repository id, or a Hugging Face model id. If `--model-name` is omitted, the server exposes `model_path` as the model id in `/v1/models`.

Recommended explicit command:

```bash
lmdeploy serve api_server <model-or-path> \
  --backend pytorch \
  --server-name 0.0.0.0 \
  --server-port 23333 \
  --model-name lmdeploy-model \
  --tp 1 \
  --session-len 8192 \
  --cache-max-entry-count 0.6
```

Common serving flags:

| Flag | Purpose |
| --- | --- |
| `--server-name` | Bind host for the FastAPI server; defaults to `0.0.0.0`. Use `127.0.0.1` for local-only clients. |
| `--server-port` | HTTP port; defaults to `23333`. |
| `--model-name` | Public model id returned by `/v1/models` and required in client requests. |
| `--backend` | `turbomind` or `pytorch`; default CLI choice is `turbomind` with auto selection logic for non-PyTorch paths. |
| `--tp` | Tensor-parallel GPU count. |
| `--dp`, `--ep`, `--cp` | Data/expert/context parallel controls; `--cp` is for TurboMind context parallelism. |
| `--session-len` | Maximum sequence/session length. Increase for length stops if memory allows. |
| `--cache-max-entry-count` | Fraction of free GPU memory used for KV cache; lower it to recover from OOM. |
| `--cache-block-seq-len` | KV block token length. |
| `--max-batch-size` | Maximum engine batch size; auto-selected when omitted. |
| `--max-prefill-token-num` | Prefill token budget per iteration. |
| `--enable-prefix-caching` | Enable prefix cache matching for repeated prefixes. |
| `--max-concurrent-requests` | Add server-side concurrency limit middleware. |
| `--api-keys` | Space-separated bearer tokens. When set, clients must send `Authorization: Bearer <key>`. |
| `--ssl` | Serve HTTPS using `SSL_KEYFILE` and `SSL_CERTFILE` environment variables. |
| `--disable-fastapi-docs` | Disable Swagger UI, ReDoc, and OpenAPI schema routes. |
| `--allow-origins`, `--allow-methods`, `--allow-headers`, `--allow-credentials` | CORS controls. |
| `--max-log-len` | Limit logged prompt character/token length. |
| `--trust-remote-code` | Allow remote model code when loading models that need it. |
| `--chat-template` | Use a built-in chat template name or chat-template JSON file. |
| `--revision`, `--download-dir` | Select and cache model revisions. |

Parser flags:

| Flag | When to use |
| --- | --- |
| `--tool-call-parser <name>` | Required for structured tool calls on OpenAI chat, Responses tools, and Anthropic tool-use blocks. Use a parser that matches the model family. |
| `--reasoning-parser <name>` | Required when a reasoning model emits parseable thinking text and clients expect `reasoning_content` or Anthropic `thinking` blocks. |

Documented built-in reasoning parser names include `qwen-qwq`, `qwen3`, `intern-s1`, `deepseek-r1`, `deepseek-v3`, and `gpt-oss`. Tool parser names are discovered from the installed CLI help and include model-family parsers such as InternLM, Qwen, and Llama variants.

Tool/reasoning launch examples:

```bash
lmdeploy serve api_server deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B \
  --backend pytorch \
  --reasoning-parser deepseek-r1

lmdeploy serve api_server <qwen-or-internlm-model> \
  --backend pytorch \
  --tool-call-parser qwen \
  --api-keys local-secret
```

## Proxy Server

Start a request distributor in front of multiple `api_server` nodes:

```bash
lmdeploy serve proxy \
  --server-name 0.0.0.0 \
  --server-port 8000 \
  --serving-strategy Hybrid \
  --routing-strategy min_expected_latency
```

Proxy flags:

| Flag | Purpose |
| --- | --- |
| `--server-name`, `--server-port` | Proxy bind host and port; default port is `8000`. |
| `--serving-strategy` | `Hybrid` for colocated prefill/decode; `DistServe` for prefill-decode disaggregation. |
| `--routing-strategy` | `random`, `min_expected_latency`, or `min_observed_latency`. |
| `--disable-cache-status` | Do not persist/restore prior node status. |
| `--dummy-prefill` | Dummy prefill for performance profiling. |
| `--migration-protocol` | `RDMA` or `NVLINK` for disaggregated KV migration. |
| `--link-type` | `RoCE` or `IB` for RDMA. |
| `--disable-gdr` | Disable GPU Direct RDMA. |
| `--api-keys`, `--ssl`, `--log-level` | Same auth/TLS/log controls as API serving. |

Register API nodes automatically by passing the proxy URL to each `api_server`:

```bash
lmdeploy serve api_server <model-a> \
  --server-name <real-node-ip> \
  --server-port 23333 \
  --model-name model-a \
  --proxy-url http://<proxy-real-ip>:8000
```

Use a real routable IP or DNS name for `--proxy-url` and node `--server-name` in multi-host deployments. `0.0.0.0` is a bind address, not a reachable peer address.

Proxy node management endpoints:

```bash
curl http://127.0.0.1:8000/nodes/status
curl -X POST http://127.0.0.1:8000/nodes/add \
  -H "content-type: application/json" \
  -d '{"url":"http://127.0.0.1:23333"}'
curl -X POST 'http://127.0.0.1:8000/nodes/remove?node_url=http://127.0.0.1:23333' -d ''
```

OpenAI-compatible client traffic can target the proxy root exactly as it targets a single `api_server`:

```bash
curl http://127.0.0.1:8000/v1/models
curl http://127.0.0.1:8000/v1/chat/completions \
  -H "content-type: application/json" \
  -d '{"model":"model-a","messages":[{"role":"user","content":"hello"}],"max_tokens":16}'
```

## CLI Validation

Use these low-cost checks before writing automation around a deployed environment:

```bash
lmdeploy serve api_server --help
lmdeploy serve proxy --help
lmdeploy serve api_server <model> --help
```

If parser names or flags differ across versions, prefer the installed `--help` output over examples. This skill was drafted against package `lmdeploy` version `0.13.0` evidence.
