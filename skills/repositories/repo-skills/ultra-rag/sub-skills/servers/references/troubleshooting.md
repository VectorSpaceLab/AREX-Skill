# UltraRAG Server Troubleshooting

## Purpose

Use this when a server module, backend import, or optional dependency fails.

## Failure patterns

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ImportError: cannot import name 'httpx_logger' from 'openai._utils._logs'` | The installed OpenAI package is newer than the source expects | Use a compatible OpenAI 1.x release. The inspection environment verified `openai 1.109.1`. |
| `ModuleNotFoundError: No module named 'rouge_score'` | Evaluation server imported without the metric extra | Install `rouge-score` before using `servers/evaluation`. |
| `ModuleNotFoundError: No module named 'pytrec_eval'` | `evaluate_trec` or `evaluate_trec_pvalue` is being used without the retrieval-eval package | Install `pytrec-eval-terrier` or a compatible `pytrec_eval` package. |
| `ModuleNotFoundError` for `bm25_tokenizer`, `index_backends`, or `websearch_backends` | Retriever source subdirectory is not on `sys.path` | Add `servers/retriever/src` to `sys.path` or use a checkout-aware wrapper script. |
| `ModuleNotFoundError: No module named 'fastapi'` | Case-study viewer or standalone deployment helper was imported without FastAPI | Install `fastapi`; `uvicorn` is also required to run those services. |
| `ModuleNotFoundError` for `mineru` | Corpus workflows reached `mineru_parse` or `build_mineru_corpus` without the corpus extra | Install `ultrarag[corpus]` or `mineru[core]`. |
| CUDA or GPU backend errors in generation | `vllm`/`torch` not installed, incompatible driver, or too little VRAM | Use the CPU-friendly workflows or install the matching CUDA stack before trying GPU generation. |
| Web-search failures | Missing API key, blocked network, or wrong provider package | Pick the provider configured in the parameter file and provide the corresponding key or access. |
| `Node.js not installed or version too low` | Using a remote MCP server path | Install Node.js 20+ and `mcp-remote`. |

## Recovery order

1. Fix the import problem first.
2. Check the relevant extra or provider package.
3. Re-run the smallest module import or server-specific smoke check.
4. Only then rebuild the pipeline or retry the full workflow.

## Checks worth running next

- `scripts/inspect_servers.py` to see which modules import cleanly.
- `references/backends-and-config.md` to pick the right backend or extra.
- `sub-skills/pipelines/references/troubleshooting.md` if the failure surfaces
  only when the server is wired into a pipeline.
