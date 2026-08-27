# Example Dependency and Capability Matrix

| Example family | Typical dependencies | Credential / network needs | Backend notes | Verification posture |
| --- | --- | --- | --- | --- |
| Quickstart / basic chat | core package, provider SDKs | provider API keys for live runs | CPU-only | docs-backed recipe; safe to inspect, not to run blindly |
| Multimodal / PDF | vision-capable provider SDKs, `instructor`, sample images or PDFs | usually a provider key | CPU-only | recipe with optional live run |
| Memory / FastAPI / persistent state | FastAPI, state store or persistence backend, provider SDKs | provider keys for live runs | CPU-only | recipe; safe with mocks or local state |
| Search / RAG / deep research | web/search backends, vector store, provider SDKs | usually network and one or more keys | CPU-only | recipe; do not assume offline execution |
| Orchestration / hooks | provider SDKs and example tool dependencies | sometimes a provider key | CPU-only | recipe; mostly mocked or local |
| MCP / progressive disclosure | MCP runtime, example server/client dependencies | often network or local subprocesses | CPU-only | recipe; use native mocked or local server flows only when authorized |
| DSPy integration | DSPy plus provider SDKs | provider key for live calls | CPU-only | recipe; optional live run |
| YouTube workflows | YouTube transcript support + provider SDKs | public video URL, sometimes provider key | CPU-only | recipe; safe with public video URLs only |
