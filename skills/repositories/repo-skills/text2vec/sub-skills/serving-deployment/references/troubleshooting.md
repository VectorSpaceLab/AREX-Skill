# Troubleshooting serving deployments

## Quick symptom map

| Symptom | Likely cause | Fix |
|---|---|---|
| `ModuleNotFoundError` for FastAPI, Uvicorn, Jina, Gradio, or DocArray | Optional serving dependency is missing | Install the dependency set for the chosen deployment pattern. Keep the FastAPI template import-safe so `--help` still works. |
| Service starts, but model files download only when the first request arrives | Lazy model loading is working as designed | Use a local model directory if you want offline startup. Call `/warmup` after deployment if you want to fail fast before traffic. |
| `GET /healthz` works but `GET /readyz` says not ready | The model has not been loaded yet | Call `/warmup`, then re-check readiness. |
| `POST /emb` returns 422 | Bad JSON body or wrong schema | Send `Content-Type: application/json` and use `{"input": "..."}` or `{"input": ["...", "..."]}`. |
| `POST /emb` returns a huge payload | Embedding arrays are large | Batch less, compress responses, or return IDs and store embeddings in a vector database instead of echoing them back. |
| CUDA OOM or very slow GPU service | Model too large, batch too large, or too many workers | Use `device="cpu"` for smaller traffic, reduce request batch size, or run one worker per GPU. Avoid spawning several Uvicorn workers unless you really want one model copy per worker. |
| Browser frontend cannot call the service | Host binding or CORS mismatch | Bind to `0.0.0.0` only when needed, expose the correct port, and add CORS middleware for the exact frontend origins you trust. |
| Tests hang forever | The code launched a long-running server (`uvicorn.run`, `Flow.block()`, or `gr.Interface.launch()`) | Test the app factory or client logic instead of starting an indefinite process. Use a short smoke request against a controlled subprocess if you must exercise the transport. |
| Jina hub executor fails behind a firewall | `jinahub://...` needs network access or cached artifacts | Use a vendored local Jina executor or switch to the FastAPI template for offline deployment. |
| FastAPI works locally but not in a container | Wrong host binding or port exposure | Bind to `0.0.0.0` inside the container, map the port explicitly, and keep the health endpoint available. |

## Optional dependency problems

### FastAPI / Uvicorn missing

If `python scripts/fastapi_app_template.py --help` works but launching the server
fails, the environment probably lacks the runtime extras. Install the optional
HTTP stack before calling `main()` or `create_app()` in production.

### Jina / DocArray missing

Jina examples require the Jina runtime and its document containers. The service
pattern here is intentionally separated from the embedding logic so that an HTTP
service can still work without the Jina stack.

### Gradio missing

Gradio is for demo UIs. If it is absent, the service layer is still usable.

## Model loading and downloads

### Remote model IDs

When `model_name_or_path` is a remote model ID, the first load may download
weights, tokenizer assets, or config files. This can happen on `/warmup` or the
first `/emb` request because the template loads the model lazily.

If you need a no-network startup:

1. Put the model files into a local directory.
2. Pass that directory as `model_name_or_path`.
3. Use `/healthz` for liveness and `/warmup` only when you intentionally want
   the load to occur.

### Local model directory

If the local directory is incomplete, missing files usually show up as a clear
failure on `/warmup` or `/emb`. Re-check the directory contents, the model name,
and the device setting.

## Binding, ports, and CORS

- Use `127.0.0.1` for a local-only service.
- Use `0.0.0.0` only when the host or container networking requires it.
- Pick an unused port; `8001` is common in examples, but any open port works.
- If a browser app or another origin calls the service, add CORS middleware for
  the exact allowed origins. Avoid a permissive wildcard on public services.

## JSON body and schema issues

The FastAPI template accepts:

- `{"input": "single sentence"}`
- `{"input": ["sentence A", "sentence B"]}`
- a raw JSON list of strings for convenience

Common mistakes:

- sending form data instead of JSON;
- using the wrong key name, such as `text` instead of `input`;
- sending a list that contains non-string items;
- posting an empty list.

If a client needs a stricter schema, define it explicitly at the application
boundary and keep the model invocation separate.

## Response size and downstream storage

Embedding responses can become large quickly:

- a single 768-dim float vector is already sizable in JSON;
- a batch of hundreds of items can be expensive to serialize;
- returning full vectors to every downstream client is often unnecessary.

Prefer these patterns when the traffic grows:

1. return only IDs or top-k matches;
2. store vectors in a vector database or cache;
3. compress network traffic if the stack supports it;
4. expose a separate search endpoint rather than echoing all embeddings back.

## GPU memory and worker count

If the service uses CUDA and runs out of memory:

- lower the request batch size;
- switch the template to CPU for small traffic;
- choose a smaller embedding model;
- keep one model copy per process or GPU.

Be careful with multiple Uvicorn workers: each worker loads its own model copy,
which multiplies memory use and can defeat the point of using a single GPU.

## Forever-server checks

Do not make CI or local verification wait on a forever server:

- `uvicorn.run(...)` blocks by design;
- `flow.block()` blocks by design;
- `gr.Interface.launch()` blocks by design.

For verification, prefer one of these patterns:

- import the app factory and check that it creates an app without side effects;
- call the FastAPI app through a test client in a short-lived process;
- run a one-request smoke check, then shut the process down.

## JinaHub and network incompatibility

The Jina pattern shown in the workflow reference depends on the `jinahub://`
executor being reachable. Failures here are usually environment issues rather
than text2vec model issues.

Use FastAPI when:

- the environment is offline or firewalled;
- you want direct control over request and response schemas;
- you only need one model or one API surface.

Use Jina when:

- you need Flow composition or service graphs;
- you need multiple models or devices handled as separate executors;
- your deployment already standardizes on Jina/JinaHub.

## When to ask for help

Escalate the deployment design if you need all of the following at once:

- multiple models with different devices,
- shared request routing and pre/post-processing,
- custom health/readiness behavior,
- and a deployment platform with strict network or GPU constraints.

That is usually the point where a single FastAPI template becomes a thin edge
service around a more structured Jina or multi-service architecture.
