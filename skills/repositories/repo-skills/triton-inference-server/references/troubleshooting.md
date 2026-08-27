# Cross-cutting Troubleshooting

Use this root reference when the failure layer is unclear. Then route to the nearest focused sub-skill.

## First split the layer

| Symptom | Likely layer | Route |
| --- | --- | --- |
| `tritonserver` command not found, container cannot start, ports unavailable, readiness stays non-200 | Runtime/container | `server-runtime-and-deployment` |
| Model shows `UNAVAILABLE`, config parse error, wrong model name/version, missing model artifact | Model repository/config | `model-repository-and-config` |
| HTTP/gRPC request returns 400/404/503, tensor shape/type mismatch, shared-memory or binary body issue | KServe protocol/client | `client-protocols` |
| Python import fails for `tritonserver` or `tritonfrontend`, or embedded frontend service lifecycle is confusing | In-process Python | `in-process-frontends` |
| `/v1/chat/completions` fails, tokenizer or LLM backend mismatch, restricted API 401, request too large | OpenAI-compatible frontend | `openai-llm-frontend` |

## High-value first checks

```bash
curl -v http://localhost:8000/v2/health/ready
curl -s http://localhost:8000/v2 | python3 -m json.tool
curl -s http://localhost:8000/v2/repository/index | python3 -m json.tool
curl -s http://localhost:8002/metrics | head
```

For gRPC, use a Triton client library or a known-good gRPC health/model-metadata call instead of guessing protobuf payloads by hand.

## Common root causes

- **Version mismatch**: native wheels, containers, backend libraries, or model artifacts come from different Triton/CUDA/backend releases.
- **Wrong repository mount**: the server sees an empty or parent directory rather than the repository containing model subdirectories.
- **CPU/GPU mismatch**: CPU-only launch cannot load model configs or backends requiring GPU instances.
- **Strict readiness**: a single failed model can keep the server not-ready unless strict readiness is relaxed intentionally.
- **Protocol mismatch**: OpenAI `/v1/*` requests are not KServe `/v2/*` requests; route them to different sub-skills.
- **Security surface**: repository-control, statistics, trace, logging, shared memory, and model-config endpoints should be restricted for untrusted clients.

## Escalation checklist

When escalating or filing a bug, collect the exact command, container tag/package versions, model repository layout, `config.pbtxt`, backend type, protocol request, response/error, and relevant Triton logs. If a live service is involved, record whether the issue reproduces with HTTP and gRPC, and whether it reproduces in the latest release container.
