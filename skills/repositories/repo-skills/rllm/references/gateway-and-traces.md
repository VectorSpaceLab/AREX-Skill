# Model Gateway and Trace Capture

The repository includes a sibling `rllm-model-gateway` package. rLLM training/evaluation uses it as an OpenAI-compatible proxy that creates sessions, forwards model calls to workers/providers, records request/response traces, and returns a session-specific base URL for agent code.

## Public package surface

Import from `rllm_model_gateway` for standalone gateway work:

```python
from rllm_model_gateway import (
    GatewayClient,
    AsyncGatewayClient,
    GatewayConfig,
    WorkerConfig,
    WorkerInfo,
    TraceRecord,
)
```

Useful signatures validated during inspection:

- `GatewayClient(gateway_url: str, timeout: float = 30.0)` and `AsyncGatewayClient(...)`.
- `GatewayConfig(host="0.0.0.0", port=9090, workers=[], db_path=None, store_worker="sqlite", add_logprobs=True, add_return_token_ids=True, strip_vllm_fields=True, routing_policy=None, health_check_interval=10.0, log_level="INFO", sync_traces=False)`.
- `WorkerConfig(url, api_path="/v1", model_name=None, weight=1)`.
- `TraceRecord(trace_id, session_id, model="", messages=[], prompt_token_ids=[], response_message={}, completion_token_ids=[], logprobs=None, finish_reason=None, latency_ms=0.0, token_counts={}, timestamp=0.0, metadata={}, raw_request=None, raw_response=None)`.

## CLI surface

`rllm-model-gateway` starts the service. Safe discovery:

```bash
rllm-model-gateway --help
```

Important options include `--host`, `--port`, `--config`, repeated `--worker`, `--db-path`, `--store {sqlite,memory}`, and `--log-level`.

## Client workflow

1. Start the gateway with one or more workers, or let rLLM's training/eval managers provision one.
2. Create a session with optional metadata and sampling params.
3. Give the agent the session base URL from `client.get_session_url(session_id)`; it ends in `/sessions/<id>/v1` and is OpenAI-compatible.
4. Retrieve traces with `get_session_traces(session_id)` or `get_trace(trace_id)`.
5. Close/delete sessions and flush before shutdown when the caller needs all traces persisted.

## Training/eval integration

- `rllm.gateway.manager.GatewayManager` owns lifecycle for training backends and returns model-facing session URLs.
- `rllm.engine.trace_converter.trace_record_to_step` converts gateway traces into rLLM `Step` objects for enrichment and training payloads.
- `EvalGatewayManager` is used by evaluation paths that need trace capture or provider routing without a full training backend.
- Remote sandbox backends may require a public tunnel so the sandbox can reach the gateway. Container reachability helpers rewrite loopback URLs where needed.

## Troubleshooting clues

- Empty or missing token IDs/logprobs usually mean the downstream provider/worker did not return the fields requested by the gateway or the gateway was not configured with `add_logprobs`/`add_return_token_ids`.
- A session URL that works on the host may fail from Docker/remote sandboxes unless it is rewritten or tunneled. Use the sandbox/backend guidance in `../sub-skills/cli-ops/references/workflows.md` and `../sub-skills/training/references/troubleshooting.md`.
- Route order matters: `/sessions/<id>/traces` and `/sessions/batch_delete` must not be shadowed by generic session routes; use the packaged server rather than hand-registering routes.
- `store=memory` is good for smoke tests; use SQLite/persistent storage when traces must survive process restart.
