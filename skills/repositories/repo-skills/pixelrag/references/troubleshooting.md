# PixelRAG Cross-Cutting Troubleshooting

## Install/import problems

- Verify Python satisfies PixelRAG's package metadata (`>=3.12`).
- Install only the extra needed for the chosen workflow.
- If `pixelrag <stage>` says the stage is missing, install that stage's extra.
- If using uv from a checkout, prefer `uv sync --frozen` for reproducibility.

## `pip check` reports cuDNN metadata conflicts

PixelRAG's uv configuration intentionally overrides `nvidia-cudnn-cu12` to a pinned version used by the repo's CUDA stack. If a generic checker reports a torch/cuDNN metadata mismatch, also verify the project lock/sync state and run a tiny torch CUDA allocation before declaring the environment broken.

## Chrome/render problems

Route to `sub-skills/render-capture/references/troubleshooting.md`. Common checks:

```bash
pixelshot which-chrome
pixelshot --help
```

Use `--cdp-url` for authenticated browser sessions and `--wait-network-idle` for JS-heavy pages. If local render returns no tile directories with no per-URL failure, also check for a port conflict on the renderer's default CDP worker ports starting at 9400.

## Model downloads or GPU memory

Qwen3-VL embedding, serving, eval readers, and training can download large models and require GPU memory. Always run a limited smoke first (`--limit`, small `n_docs`, or helper dry-run) and confirm device selection.

## Missing tiles or mismatched article IDs

Route to `index-build`. Do not manually relabel tile directories. Let the orchestrator stamp `source` and `article_id`, or rebuild with `--force`.

## Search endpoint returns empty results

Route to `serve-search`. Check `/status`, vector count, backend, query instruction, `nprobe`, department filter, and tile/index alignment.

## Benchmark scores are unexpectedly low

Route to `evaluation-reproduction`. Check reader model, search serve index/version, retrieval timeout, grader key/base URL, and strict-vs-LLM judge choice.

## Training/eval data paths fail

Route to `training-and-data`. Validate JSONL field shape and image paths before launching API/GPU-heavy scripts.

## Deployment safety

Deployment scripts modify live services, nginx upstreams, systemd slots, and the chat-agent service. Use [deployment-and-operations.md](deployment-and-operations.md) and confirm host context before executing anything.

## Stale skill symptoms

Refresh this skill if:

- `pyproject.toml` entry points/extras change.
- Source roots under `render/`, `embed/`, `index/`, or `serve/` change major APIs.
- Eval/training README commands or model names change.
- Native tests reveal different behavior than described here.
