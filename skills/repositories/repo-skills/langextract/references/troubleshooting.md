# LangExtract Cross-cutting Troubleshooting

Use this root guide to route a LangExtract failure to the correct focused sub-skill. Then read that sub-skill's troubleshooting reference for the detailed fix.

## Route by failure surface

| Symptom / request | First place to read |
| --- | --- |
| Bad or missing extraction results, `ValueError` about examples, prompt alignment warnings/errors, `char_interval=None`, output order, resolver parsing, long-document chunking, Unicode offsets. | [extraction troubleshooting](../sub-skills/extraction/references/troubleshooting.md) |
| Missing API key, unknown model ID, wrong provider selected, Gemini/OpenAI/Ollama construction error, Vertex AI config, quota/rate limits, batch jobs. | [provider troubleshooting](../sub-skills/providers/references/troubleshooting.md) |
| JSONL save/load errors, `InvalidDatasetError`, missing JSONL path, only first JSONL document visualized, no highlights in HTML. | [visualization troubleshooting](../sub-skills/visualization/references/troubleshooting.md) |
| Custom provider plugin not discovered, entry point missing, pattern conflicts, schema lifecycle failures, wrong `infer()` output shape. | [provider-plugin troubleshooting](../sub-skills/provider-plugins/references/troubleshooting.md) |

## Install/import problems

### Package does not import

1. Confirm installation in the Python that will run the user's code:
   ```bash
   python -m pip show langextract
   python - <<'PY'
import langextract as lx
print(lx.__name__)
PY
   ```
2. If using OpenAI, install the optional extra:
   ```bash
   python -m pip install "langextract[openai]"
   ```
3. Do not rely on a source checkout being on `PYTHONPATH`. A future project should install the public package or a deliberate editable checkout.

### Provider dependency missing

- Gemini and Ollama dependencies are part of the base package dependency set.
- OpenAI requires the optional extra and an API key for live inference.
- Third-party providers require their plugin package and any backend SDK dependencies.

## Secrets and credentials

- Do not print API key values. It is enough to report which variable names are set or missing.
- Typical credential variables: `GEMINI_API_KEY`, `LANGEXTRACT_API_KEY`, `OPENAI_API_KEY`, `GOOGLE_CLOUD_PROJECT` for Vertex AI, and service-specific variables for plugins.
- If both `GEMINI_API_KEY` and `LANGEXTRACT_API_KEY` are set, provider-specific keys take precedence for matching model families.

## Security and side effects

- `fetch_urls=False` by default. Treat URL-looking strings as literal text unless the user explicitly wants trusted URL fetching in a sandbox.
- Batch APIs, cloud model calls, and Ollama inference can incur cost, use network, or depend on local services. Get explicit approval when this is not already implied by the user request.
- JSONL output filenames are joined under `output_dir` but not sanitized for untrusted hosted-service inputs. Validate user-controlled filenames before writing.
- Provider-plugin generators write scaffolds to a caller-selected directory; use `--force` only when overwrite is intentional.

## Verification helpers

Run these only from within the generated skill tree or after adapting paths to the generated tree:

```bash
python sub-skills/providers/scripts/check_provider_routes.py --skip-plugins
python sub-skills/visualization/scripts/save_and_visualize.py --output-dir ./lx-viz-demo
python sub-skills/provider-plugins/scripts/create_provider_plugin.py MyProvider --output-dir ./plugins --with-schema
```

The first two are safe/no-network. The plugin generator writes files only by default. The extraction starter scripts are dry-run by default and require `--run` before any provider call.
