# Troubleshooting

## Purpose

Use this for cross-cutting DataFlow failures that do not belong to a single sub-skill yet. If a failure is specific to a workflow family, read the matching sub-skill troubleshooting file next.

## Quick triage

| Symptom | Likely cause | Next step |
| --- | --- | --- |
| `ModuleNotFoundError: dataflow` | Package not installed or wrong environment | Reinstall with `python -m pip install -e .` or `python -m pip install open-dataflow`, then rerun `scripts/check_dataflow_env.py`. |
| `dataflow env failed: [Errno 25] Inappropriate ioctl for device` | Built-in env command is running in a non-TTY pipe/CI context | Use `python scripts/check_dataflow_env.py` instead, or run the built-in command in a real terminal. |
| `Key Matching Error` during `pipeline.compile()` | `input_*` key does not exist in prior outputs or the input dataset | Check operator order, storage step number, and column spelling; see `sub-skills/pipeline-foundations/references/troubleshooting.md`. |
| `Missing input column` or a `KeyError` in a smoke script | The fixture does not contain the expected field name | Validate the input with `scripts/validate_tabular_input.py` or the sub-skill validator that owns the workflow. |
| `Invalid prompt_template type` | `prompt_restrict` rejected a non-whitelisted prompt class | Use a `PromptABC` / `DIYPromptABC` subclass allowed by the decorated operator. |
| `ImportError` for `pyvis` | Graph rendering dependency is absent | Install the optional dependency or skip `draw_graph`; use the pipeline-foundations reference for the exact caveat. |
| `DF_API_KEY` missing or API requests fail | The selected serving backend expects an API key | Set the documented env var for the backend and retry; see `sub-skills/serving-cli/references/troubleshooting.md`. |
| `webui` downloads or starts a backend you did not expect | The command is side-effecting by design | Use `--webui-path` for an existing backend directory or consult `sub-skills/serving-cli/references/evaluation-and-webui.md`. |
| Ray / RayOrch import failure | Optional parallel-compute backend is missing | Install the `ray` / `rayorch` extras only for the acceleration route and consult `sub-skills/rayorch-acceleration/references/troubleshooting.md`. |
| PDF / OCR / VQA work fails at import time | Heavy document extras are absent | Install only the document-related extras you actually need and consult `sub-skills/document-vision-rag/references/troubleshooting.md`. |

## Cross-cutting fixes

### Install or repair the package

```bash
python -m pip install -e .
python -m pip check
```

### Inspect the public surface safely

```bash
python scripts/check_dataflow_env.py
python scripts/inspect_dataflow_surface.py
```

### Confirm CLI discovery

```bash
python -m dataflow.cli --help
python -m dataflow.cli init --help
```

## When to stop and narrow scope

- If a workflow needs a backend that is not available, do not treat a CPU import as proof of GPU/accelerator behavior.
- If a workflow needs credentials or network access, do not paper over the requirement with an offline-only answer.
- If a workflow is clearly specific to one sub-skill, stop here and jump to that sub-skill's troubleshooting file.

## Go next

- Pipeline and storage issues: `sub-skills/pipeline-foundations/references/troubleshooting.md`
- CLI and serving issues: `sub-skills/serving-cli/references/troubleshooting.md`
- Text workflow issues: `sub-skills/text-workflows/references/troubleshooting.md`
- Document / RAG / pdf2model issues: `sub-skills/document-vision-rag/references/troubleshooting.md`
- RayOrch issues: `sub-skills/rayorch-acceleration/references/troubleshooting.md`
