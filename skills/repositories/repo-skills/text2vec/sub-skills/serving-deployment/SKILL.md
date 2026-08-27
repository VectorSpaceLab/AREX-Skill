---
name: serving-deployment
description: "Serve text2vec embeddings and similarity workflows through
  FastAPI, Jina, or Gradio with explicit request, response, and lifecycle
  guidance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# serving-deployment

Use this sub-skill when you need to expose text2vec inference as a service,
integration endpoint, or lightweight UI.

## Covers
- FastAPI embedding endpoints with `POST /emb`.
- Jina server/client patterns and hub/network caveats.
- Gradio demo UIs for manual inspection, not production defaults.
- Service-layer composition around embeddings and similarity-search.

## Route elsewhere
- Batch CLI encoding from files -> `embeddings`.
- Pair scoring, vector search, or BM25 ranking -> `similarity-search`.
- Training or fine-tuning a serving model -> `training-finetuning`.
- Benchmarking model quality -> `evaluation-benchmarks`.

## Bundled assets
- [serving workflows](references/serving-workflows.md)
- [troubleshooting](references/troubleshooting.md)
- [FastAPI app template](scripts/fastapi_app_template.py)

## Quick use
1. Read `references/serving-workflows.md` for endpoint shapes and deployment choices.
2. Use `scripts/fastapi_app_template.py` as the safe FastAPI scaffold.
3. Check `references/troubleshooting.md` for optional deps, lazy model loading,
   host/port binding, CORS, GPU memory, and forever-server issues.

## What this sub-skill does not do
- It does not define model training commands.
- It does not implement batch embedding file pipelines.
- It does not evaluate benchmarks or compare leaderboard scores.
