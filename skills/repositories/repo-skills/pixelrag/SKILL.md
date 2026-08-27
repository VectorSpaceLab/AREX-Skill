---
name: pixelrag
description: "Use PixelRAG for visual document RAG: screenshot capture, visual
  index building, FAISS/Qdrant serving, evaluation reproduction, and LoRA
  training/data workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# PixelRAG

Use this skill when a task names PixelRAG, `pixelshot`, `pixelrag`, visual RAG over screenshots, document screenshot tiles, Qwen3-VL visual embeddings, FAISS/Qdrant visual indexes, PixelRAG search APIs, paper reproduction, or the PixelRAG LoRA training data pipeline.

## First Checks

- **Check staleness**: Read [repo-provenance.md](references/repo-provenance.md) before using this skill with a checkout; refresh if the commit, package version, or evidence paths changed.
- **Install minimally**: Base capture is `pip install pixelrag`. Add only the needed extra: `pixelrag[index]`, `pixelrag[serve]`, `pixelrag[qdrant]`, `pixelrag[pdf]`, or `pixelrag[dev]`.
- **Verify commands**:
  ```bash
  python -c "import pixelrag, pixelrag_render; print('ok')"
  pixelshot --help
  pixelrag --help
  ```
- **Run diagnostics**: Use [pixelrag_doctor.py](scripts/pixelrag_doctor.py) before deeper debugging.
- **Read troubleshooting**: Use [troubleshooting.md](references/troubleshooting.md) for install, optional dependency, CUDA, Chrome, model-download, data/config, and stale-skill failures.

## Route by Task

| User request | Use this route |
| --- | --- |
| Capture URLs, authenticated browser pages, PDFs, HTML, text, or images into screenshot tiles | [render-capture](sub-skills/render-capture/SKILL.md) |
| Build a local visual index from documents, debug `pixelrag.yaml`, chunk/embed/build FAISS or Qdrant indexes | [index-build](sub-skills/index-build/SKILL.md) |
| Start or query `pixelrag serve`, call `/search`, use FAISS/Qdrant backends, fetch tile images, debug departments | [serve-search](sub-skills/serve-search/SKILL.md) |
| Reproduce paper benchmark cells, configure reader/search serves, run eval graders, debug low scores | [evaluation-reproduction](sub-skills/evaluation-reproduction/SKILL.md) |
| Use the released LoRA adapter, prepare synthetic data, run or debug the separate training project | [training-and-data](sub-skills/training-and-data/SKILL.md) |

## Minimal Patterns

Render a page or local file:

```bash
pixelshot https://example.org --output ./tiles
pixelshot paper.pdf --output ./tiles --dpi 200
```

Build an index from local documents:

```yaml
source:
  type: local
  path: ./my_docs
embed:
  model: Qwen/Qwen3-VL-Embedding-2B
  device: auto
output: ./my_index
```

```bash
pixelrag index build --config pixelrag.yaml --limit 10
```

Serve and search:

```bash
pixelrag serve --index-dir ./my_index --articles-json ./my_index/articles.json --tiles-dir ./my_index/tiles --port 30001
curl -s -X POST http://localhost:30001/search \
  -H "Content-Type: application/json" \
  -d '{"queries":[{"text":"overview diagram"}],"n_docs":5}'
```

## References

- [install-and-routing.md](references/install-and-routing.md) covers package extras, CLI dispatch, and workflow selection.
- [agent-integration.md](references/agent-integration.md) covers hosted API use, pixelbrowse, and agent/tool integration boundaries.
- [deployment-and-operations.md](references/deployment-and-operations.md) covers production topology and safe blue-green deployment concepts.
- [repo-routing-metadata.json](references/repo-routing-metadata.json) is structured router metadata for managed repo-skill import.

## Important Boundaries

- Do not treat full embedding, benchmark reproduction, or training as cheap: they may download large Qwen/HF assets, load huge FAISS indexes, start long-running services, require GPUs, and consume paid API keys.
- The `train/` workflow is a separate uv project. Do not install it into the root PixelRAG package environment unless the task explicitly asks for training.
- Do not run deploy scripts, systemd units, or nginx switch scripts unless the user confirms they are on the deploy host and wants operational changes.
- Do not depend on original repo examples, docs, or tests at runtime; this skill bundles distilled references and safe helper scripts.
