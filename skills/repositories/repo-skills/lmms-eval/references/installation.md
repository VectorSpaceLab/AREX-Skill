# Installation and smoke checks

`lmms-eval` is the distribution name from `pyproject.toml` and the import root is `lmms_eval`.

## Recommended install choices

Use the smallest install that matches the workflow you want:

| Workflow | Suggested install |
| --- | --- |
| Core package inspection, CLI browsing, task/model registry, task authoring, and direct eval routing | `pip install -e '.'` |
| HTTP server, evaluation API, and FastAPI client usage | `pip install -e '.[server]'` |
| MCP tooling | `pip install -e '.[mcp]'` |
| Web UI backend | `pip install -e '.[tui]'` plus Node.js 18+ for the frontend build |
| Broad local-model experimentation | `pip install -e '.[all]'` only when you really need every optional stack |

The repo docs also describe `uv`-based workflows. Use whichever manager is already standard in the environment, but keep the install targeted; do not add extras you will not use.

## Optional extras and when they matter

- `audio` — audio tasks and audio model helpers.
- `metrics` — additional metric packages and scoring helpers.
- `gemini`, `litellm`, `reka` — API-provider integrations.
- `mmsearch`, `prismmbench` — special benchmark families.
- `video`, `video-legacy` — video runtime helpers and alternate decoders.
- `server`, `mcp`, `tui` — service and tooling layers.

## Safe smoke checks

After install, the most useful checks are:

```bash
python -m pip check
python -I -c "import lmms_eval; print(lmms_eval.__file__)"
lmms-eval --help
lmms-eval version
lmms-eval tasks list
lmms-eval models --aliases
```

For a quick registry check without downloads:

```bash
python -I -c "from lmms_eval.tasks import TaskManager; print(len(TaskManager('ERROR').all_subtasks))"
python -I -c "from lmms_eval.models import list_available_models; print(len(list_available_models()))"
```

For a CUDA smoke on a compatible host, a tiny tensor allocation is enough:

```bash
python - <<'PY'
import torch
print(torch.cuda.is_available())
if torch.cuda.is_available():
    x = torch.empty((1,), device='cuda')
    print(x.device)
PY
```

## Common environment variables

Only set the variables that match the workflow you are using:

| Variable | Used for |
| --- | --- |
| `HF_HOME`, `HF_TOKEN`, `HF_HUB_ENABLE_HF_TRANSFER` | Hugging Face datasets and models |
| `OPENAI_API_KEY`, `OPENAI_API_BASE` | OpenAI-compatible providers |
| `REKA_API_KEY` | Reka provider |
| `LMMS_EVAL_USE_CACHE` | JSONL response cache |
| `LMMS_EVAL_DATASETS_CACHE` | Datasets cache location |
| `LMMS_VIDEO_DECODE_BACKEND`, `LMMS_VIDEO_TORCHCODEC_THREADS`, `LMMS_VIDEO_DALI_DEVICE` | Video decode selection |
| `LMMS_SERVER_PORT` | Web UI port selection |
| `CUDA_VISIBLE_DEVICES` | GPU visibility |

## Version and compatibility notes

- The package currently exposes `lmms-eval`, `lmms-eval-mcp`, and `lmms-eval-ui` console scripts.
- If `import lmms_eval.mcp.server` fails because `mcp.server.fastmcp` is missing, reinstall the MCP extra with a compatible `mcp` release.
- If you only need to inspect the package, do not pull in the full `.[all]` stack unless a selected workflow actually depends on it.
