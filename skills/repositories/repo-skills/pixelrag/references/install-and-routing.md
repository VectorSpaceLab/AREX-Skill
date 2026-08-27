# Install and Routing

## Package and extras

PixelRAG distribution name: `pixelrag`.

Base install:

```bash
pip install pixelrag
```

Base includes the light capture CLI (`pixelshot`) plus shared utilities. Heavy stages are opt-in:

| Extra | Use when |
| --- | --- |
| `pixelrag[index]` | Build end-to-end visual indexes and use the embed/index stage dependencies. |
| `pixelrag[serve]` | Run the FastAPI search API and query encoder. |
| `pixelrag[qdrant]` | Build or serve Qdrant-backed indexes. |
| `pixelrag[pdf]` | Render PDFs through `pdf2image`/Poppler. |
| `pixelrag[dev]` | Run repository tests. |
| `pixelrag[eval]` | Use evaluation helper dependencies. |
| `pixelrag[distributed]`, `pixelrag[kiwix]` | Distributed/Kiwix workflows only when explicitly needed. |

Avoid `pixelrag[all]` unless the task truly needs every optional surface.

## Console scripts

- `pixelshot`: standalone capture command for URLs, PDFs, HTML, and images.
- `pixelrag`: umbrella dispatcher for pipeline stages.

`pixelrag --help` lists stages:

- `chunk`
- `embed`
- `build-index`
- `index`
- `monitor`
- `serve`

If a stage is missing, install the narrow extra rather than broad dev/all dependencies.

## Public import checks

```bash
python - <<'PY'
import pixelrag
import pixelrag_render
print('PixelRAG imports ok')
PY
```

Optional stage imports:

```python
import pixelrag_embed
import pixelrag_index
import pixelrag_serve
```

## Workflow selection

1. **Capture only**: use `sub-skills/render-capture/`.
2. **Make a searchable corpus**: use `render-capture` if needed, then `sub-skills/index-build/`.
3. **Query an existing index/API**: use `sub-skills/serve-search/`.
4. **Benchmark/paper reproduction**: use `sub-skills/evaluation-reproduction/`.
5. **LoRA training/data**: use `sub-skills/training-and-data/`.

## Backend notes

- Linux CUDA wheels are selected through PixelRAG's uv/PyTorch CUDA 12.9 configuration when using the repo lockfile.
- `device: auto` in local embedding chooses CUDA, then MPS, then CPU.
- CPU is valid for small smoke checks, but Qwen3-VL embedding and serving are slow without accelerators.
- MPS is documented for macOS Apple Silicon, not available on Linux.

## Safe validation order

1. `pixelshot --help` and `pixelrag --help`.
2. `pixelshot which-chrome` for render workflows.
3. Generate a tiny config with `sub-skills/index-build/scripts/pixelrag_tiny_index_config.py`.
4. Check `/health` and `/status` with `sub-skills/serve-search/scripts/pixelrag_search_smoke.py` before queries.
5. Use eval/training preflight/checker scripts before large benchmarks or training jobs.
