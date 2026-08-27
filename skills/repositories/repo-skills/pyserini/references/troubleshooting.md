# Cross-Cutting Troubleshooting

## When To Read

Read this when a Pyserini task fails before it clearly belongs to a single workflow, or when symptoms mention imports, Java/JVM, Faiss, Torch, server imports, resources, caches, downloads, or broad native tests.

## Symptom Router

| Symptom | Likely owner | First action |
| --- | --- | --- |
| `ModuleNotFoundError: pyserini`, Python version conflict, or `pip check` failure | `../sub-skills/install-and-runtime/SKILL.md` | Run `python scripts/check_pyserini_install.py --json` and inspect package metadata. |
| `Unable to find javac`, `No matching jar file found`, PyJNIus/JVM failure, Java class errors | `../sub-skills/install-and-runtime/SKILL.md` | Verify Java 21 and Pyserini package resources; source checkout builds route to `../sub-skills/repo-development/SKILL.md`. |
| `ModuleNotFoundError: No module named 'faiss'` | `../sub-skills/install-and-runtime/SKILL.md` or `../sub-skills/dense-encoding/SKILL.md` | Install a CPU or GPU Faiss package matching the runtime, then retry Faiss/server import checks. |
| Torch CUDA/device error | `../sub-skills/install-and-runtime/SKILL.md` and `../sub-skills/dense-encoding/SKILL.md` | Use CPU wheels/`--device cpu` by default; choose CUDA wheels only when the user needs GPU and the host supports it. |
| Encoder command tries to download a model or asks for API credentials | `../sub-skills/dense-encoding/SKILL.md` | Use pre-encoded queries/local models, or confirm network/credential use before running. |
| JSON/JSONL indexing input rejected | `../sub-skills/index-search-fetch/SKILL.md` | Validate with `python sub-skills/index-search-fetch/scripts/validate_jsonl_collection.py`. |
| Dense JSONL or vector shape rejected | `../sub-skills/dense-encoding/SKILL.md` | Validate with `python sub-skills/dense-encoding/scripts/validate_dense_jsonl.py`. |
| TREC/MS MARCO/qrels/fusion mismatch | `../sub-skills/evaluation-and-fusion/SKILL.md` | Validate with `python sub-skills/evaluation-and-fusion/scripts/validate_trec_run.py`. |
| REST config, API key, cache, OpenAPI, or MCP client issue | `../sub-skills/serving-and-agent-tools/SKILL.md` | Validate YAML with `python sub-skills/serving-and-agent-tools/scripts/validate_server_config.py`. |
| Native tests trigger downloads, models, broad jobs, or generated docs | `../sub-skills/repo-development/SKILL.md` | Use `python sub-skills/repo-development/scripts/select_safe_tests.py` and ask before heavyweight/network tests. |

## Runtime Checker

Use the root wrapper for a quick readout:

```bash
python scripts/check_pyserini_install.py --json
python scripts/check_pyserini_install.py --check-lucene --check-faiss --check-server
```

The checker does not download indexes or models. Lucene checks may start a JVM; run them in a fresh Python process after changing Java or classpath settings.

## Source Checkout Caveats

A source checkout can import `pyserini` while failing Java-backed workflows if package resources are missing. Common source-only needs include:

- Java 21 available before PyJNIus starts.
- An Anserini fatjar available in Pyserini package resources or through the current process classpath.
- Evaluation tool resources from the `tools` submodule for some eval/MCP paths.
- Focused tests selected before broad integration or reproduction suites.

Route source checkout remediation to `../sub-skills/repo-development/SKILL.md`; normal package users should prefer the PyPI package path unless they need unreleased code.

## Download And Cache Safety

Pyserini can automatically download prebuilt indexes and model assets for many examples. Before running commands that mention prebuilt names, Hugging Face/OpenAI encoders, two-click reproduction matrices, or experiment scripts:

1. Confirm the user wants network access and potentially large downloads.
2. Prefer `--help`, validators, and command builders first.
3. Use explicit cache locations only in the user's local environment, not in reusable skill content.
4. Record skipped downloads or hardware requirements in verification artifacts rather than pretending they passed.
