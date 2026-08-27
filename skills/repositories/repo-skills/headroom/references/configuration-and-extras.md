# Headroom configuration, extras, and paths

## Package extras

Use the smallest extra set that covers the requested workflow:

- Base package: lightweight compression, CLI framework, config, core models.
- `proxy`: FastAPI/Uvicorn, HTTP clients, MCP, Magika, zstandard, WebSockets, ONNX runtime, Transformers tokenizer, watchdog, and proxy support.
- `memory`: local memory store dependencies and sentence-transformers on supported platforms.
- `code`: tree-sitter language pack for AST-aware code compression.
- `relevance`: fastembed and NumPy for embedding relevance scoring.
- `image`: Pillow, OCR, sentencepiece, and ONNX-backed image helpers.
- `spreadsheet`: `openpyxl` and `xlrd` for `.xlsx`/`.xls` ingestion.
- `html`: HTML extraction.
- `reports`: report templates.
- `otel`: OpenTelemetry SDK/exporter.
- `evals`: datasets, scoring, and provider SDKs for benchmark/evaluation commands.
- `vector`: optional HNSW backend; requires a C++ toolchain and is deliberately not part of `all`.
- `pytorch-mps`: Apple Silicon memory-embedder offload; not a Linux/CUDA substitute.
- `bedrock`, `anyllm`, `langchain`, `agno`, `strands`, `crewai`, and `autogen`: provider/framework adapters that should be installed only for those integrations.

The README's `[all]` extra is convenient but intentionally broad. Do not install it just to run `headroom --help` or a basic `compress` smoke.

## Important environment variables

### Filesystem roots

- `HEADROOM_CONFIG_DIR`: read-mostly config root, default `~/.headroom/config`.
- `HEADROOM_WORKSPACE_DIR`: read-write state root, default `~/.headroom`.
- Per-resource overrides include `HEADROOM_SETTINGS_PATH`, `HEADROOM_SAVINGS_PATH`, `HEADROOM_SAVINGS_EVENTS_PATH`, `HEADROOM_TOIN_PATH`, and `HEADROOM_SUBSCRIPTION_STATE_PATH`.
- `HEADROOM_STATELESS=1` prevents workspace writes for supported runtime paths.

### Proxy and model runtime

- `HEADROOM_HOST`, `HEADROOM_PORT`, `HEADROOM_WORKERS`, `HEADROOM_HTTP2`, `HEADROOM_HTTP_PROXY`.
- `HEADROOM_TLS_STRICT=0` narrowly relaxes Python TLS strict CA-constraint checking for supported Headroom-controlled TLS contexts.
- `HEADROOM_OUTPUT_SHAPER=1` enables output-token shaping; `HEADROOM_OUTPUT_HOLDOUT` reserves an unshaped control fraction for measured savings.
- `HEADROOM_EMBEDDER_RUNTIME=pytorch_mps` selects Apple MPS memory embedder offload.
- `ORT_DYLIB_PATH`, `ORT_STRATEGY`, and `ORT_LIB_LOCATION` control ONNX Runtime loading when native asset discovery needs help.
- `HF_HUB_OFFLINE=1` forces Hugging Face model use to the local cache.

### Provider routing

- `ANTHROPIC_BASE_URL` and `OPENAI_BASE_URL` point clients at the proxy.
- `HEADROOM_PROXY_URL` points MCP/plugin clients at the proxy.
- Bedrock/Vertex also require the provider's normal credential chain and region/profile settings.

## Platform and backend notes

- Main selected workflows are CPU-capable; no CUDA/ROCm/MPS backend is required for basic package/CLI/proxy/memory/SDK use.
- x86 hosts without AVX2 should use Headroom's guarded non-ONNX fallbacks where available; a CPU import alone does not prove a model-backed path.
- Image/OCR, embedding relevance, and ML compression can download or load model assets on first use. Treat those as optional, explicit operations.
- Node/TypeScript workflows need Node `>=18` and a running proxy for proxy-backed client calls.
- Cloud examples and provider backends need credentials and network access; local health/help checks are not live-provider verification.
