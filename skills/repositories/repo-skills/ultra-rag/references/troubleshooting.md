# UltraRAG Troubleshooting

## Purpose

Use this when a task fails before a workflow-specific sub-skill can help.
This file covers package installation, import problems, CLI startup issues, and
shared backend or environment failures.

## Fast checks

1. Verify the package imports:
   ```bash
   python -c "from importlib.metadata import version; print(version('ultrarag'))"
   ```
2. Run `ultrarag --help`.
3. Run `python -m pip check` in the active environment.
4. If you are using a checkout, confirm the repo root is on `sys.path` only
   through an explicit `--repo-root` or an equivalent script option.

## Common failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'ultrarag'` | Package not installed in the active environment | Re-run the install command from the root skill; then repeat `pip check` and the import check. |
| `ultrarag: command not found` | Console script not on PATH | Use the environment Python plus `python -m` style checks, or activate the env that owns the install. |
| `Node.js not installed or version too low` | `ultrarag build` or `run` reached an HTTP MCP path and needs `mcp-remote` | Install Node.js 20+ for remote MCP paths, or convert the server path to a local Python file. |
| Server subprocess reports `ModuleNotFoundError: No module named 'ultrarag'` | The client launches local server scripts with command `python`, and PATH points to a different interpreter than the parent command | Prepend the intended environment's executable directory to PATH before build/run. |
| `ImportError: cannot import name 'httpx_logger' from 'openai._utils._logs'` | OpenAI package is too new for the generation server source | Use an OpenAI 1.x release. The inspection environment verified `openai 1.109.1`. |
| `ModuleNotFoundError: No module named 'rouge_score'` | Evaluation server imported without the metric extra | Install `rouge-score` or the evaluation extra before using `servers/evaluation`. |
| `ModuleNotFoundError` for `fastapi` in `show case` or standalone FastAPI wrappers | Case-study / deployment helper path needs FastAPI | Install `fastapi` alongside the core package. |
| `ModuleNotFoundError: No module named 'bm25_tokenizer'` or similar inside retriever import | Source checkout path not added correctly | Add the checkout root and `servers/retriever/src` to `sys.path`, or run the helper from a checkout-aware script. |
| `pytrec_eval` import failure | You reached `evaluate_trec` / `evaluate_trec_pvalue` without the retrieval-eval dependency | Install `pytrec-eval-terrier` or `pytrec_eval` before running the trec metrics workflows. |
| `show ui` starts but assets 404 | Frontend dist path missing or overridden incorrectly | Confirm `ui/frontend/dist` exists or set `ULTRARAG_FRONTEND_DIR` to a built asset directory. |
| `show case` cannot find data | No `output/memory_*.json` or the supplied case file is malformed | Provide a memory JSON/JSONL file with the expected structure; see the UI sub-skill for the accepted case format. |

## Environment and backend notes

- Generation backend code imports OpenAI internals and is known to require an
  older OpenAI release than the latest major line.
- Retrieval workflows may need optional packages such as `sentence-transformers`,
  `bm25s`, `faiss-gpu-cu12`, `tavily-python`, `exa_py`, or `pymilvus`, but the
  core package import does not require all of them.
- Corpus workflows may need `mineru[core]` and document conversion tooling.
- UI/frontend build and asset regeneration need Node.js 22+ and npm.
- Remote MCP servers need Node.js 20+ and `mcp-remote`.

## When to stop

Stop and hand off to the relevant sub-skill when the issue is clearly one of:

- pipeline YAML structure or build/run semantics,
- server tool or prompt signatures,
- UI/backend route or storage behavior.

Those are owned by the sub-skills and have more specific recovery guidance.
