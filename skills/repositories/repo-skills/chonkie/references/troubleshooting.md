# Chonkie cross-cutting troubleshooting

## Purpose

Use this reference for failures that affect more than one Chonkie workflow: installation/import, optional extras, model downloads, credentials, logging, CLI/API defaults, and service safety. For workflow-specific recovery, continue to the nearest sub-skill troubleshooting reference.

## First diagnostic steps

1. Check the installed package and optional surfaces:

   ```bash
   python scripts/check_chonkie_environment.py --json
   ```

2. If a focused route exists, run that sub-skill's smoke script before trying live providers or services.
3. Confirm whether the task is local/offline, model-dependent, provider-backed, cloud-backed, or datastore-backed.
4. Do not add broad extras or run live writes until the user confirms the required resources.

## Install/import failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'chonkie'` | Package not installed in the current Python. | Install `chonkie` into the active environment, then rerun `python -c "import chonkie; print(chonkie.__version__)"`. |
| `ImportError` for `tree_sitter_language_pack`, `pandas`, `fastapi`, provider SDKs, or vector clients | Optional extra missing. | Install only the needed extra, for example `chonkie[code]`, `chonkie[table]`, `chonkie[api]`, `chonkie[openai]`, or a datastore-specific extra. |
| `pip check` reports conflicts | Mixed package versions or broad extras installed together. | Prefer a fresh environment and install the minimum extras for the current task rather than `all`/`dev`. |
| CLI command `chonkie` not found but Python import works | The console script is not on `PATH`, or the `cli` extra is absent. | Install `chonkie[cli]`, use the environment's console-script path, or run the CLI smoke with an explicit `--cli-command`. |

## Optional dependency and backend boundaries

Chonkie exposes many optional classes from the top-level namespace, but constructing them may require extras, model files, API keys, or services.

- Deterministic local chunking: prefer `TokenChunker`, `SentenceChunker`, `RecursiveChunker`, and `FastChunker`.
- Optional local model workflows: `SemanticChunker`, `LateChunker`, `NeuralChunker`, `EmbeddingsRefinery`, and `Model2VecEmbeddings`/`SentenceTransformerEmbeddings` can need `model2vec`, `tokenizers`, `sentence-transformers`, `transformers`, `torch`, model cache, or network access.
- Provider workflows: OpenAI/Azure/Gemini/Groq/Cerebras/Jina/Cohere/Voyage/LiteLLM/Catsu paths require the provider package and credentials for the provider, not just Chonkie.
- External storage workflows: vector/datastore handshakes require client packages and explicit write scope for the target service.

Use the optional dependency probes in `sub-skills/embeddings-and-generative/` and `sub-skills/integrations-and-storage/` when the failure concerns model/provider/datastore extras.

## Model download, cache, and accelerator issues

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Semantic/late/neural chunker hangs or fails while loading | Model download/cache is missing or network is blocked. | Use deterministic `RecursiveChunker` fallback, or ask the user to authorize network/model-cache use and install the relevant extra. |
| Torch/transformers import succeeds but model execution fails | Wrong device/backend, incompatible torch build, or missing model weights. | Treat accelerator/model support as unverified. Run a tiny framework/backend smoke only after the user asks for that backend. |
| `InvalidTokenizerError` for names such as `gpt2`/`cl100k_base` | Tokenizer backend/model cannot be loaded by available tokenization backend. | Use built-in `character`, `word`, `byte`, or `row` tokenizers for deterministic checks; install `tiktoken`/`tokenizers` only if needed. |

## Credentials and API keys

Keep these separate:

- `CHONKIE_API_KEY`: Chonkie Cloud client/API usage.
- Provider API keys: `OPENAI_API_KEY`, Azure OpenAI variables, `GEMINI_API_KEY`, `GROQ_API_KEY`, `CEREBRAS_API_KEY`, `JINA_API_KEY`, `COHERE_API_KEY`, `VOYAGE_API_KEY`/`VOYAGEAI_API_KEY`, or provider-specific config.
- Local OSS FastAPI server: no Chonkie Cloud key is required to import schemas or start a local server, but network binding and long-running service behavior still need user approval.

Never print, store, or copy actual credential values. It is enough to report whether required variables are present or absent.

## CLI/API defaults that surprise users

- The installed CLI help shows `semantic` as the default `chonkie chunk`/`pipeline` chunker. For offline/local examples, explicitly pass `--chunker recursive`, `--chunker token`, or `--chunker sentence`.
- `chonkie serve` starts a long-running API server. Use `--help`, imports, and OpenAPI schema inspection for diagnostics unless the user asks to run a server.
- CLI `--chunker-params`, `--chef-params`, `--refiner-params`, and `--handshaker-params` accept key/value-style strings; validate the target Python API names before constructing complex commands.

## Logging

Chonkie uses `CHONKIE_LOG` and programmatic logging helpers.

- Default: warnings/errors.
- Disable: `CHONKIE_LOG=off`, `false`, `0`, `disabled`, or `none`.
- Increase verbosity: `CHONKIE_LOG=info`, `debug`, or numeric levels `3`/`4`.
- Programmatic helpers: `chonkie.logger.configure(...)`, `disable()`, `enable(...)`, and `is_enabled()`.

Use logging to diagnose local behavior, but do not turn debug logs into a substitute for explicit dependency/credential/service checks.

## When to stop and ask

Ask before continuing when the next step would:

- install broad extras such as `all` or `dev`;
- download model weights or large datasets;
- use paid/provider credentials or Chonkie Cloud quota;
- start a long-running server or bind a public network port;
- create, update, delete, or search a live datastore/index/collection;
- require GPU/accelerator verification that was not selected by the user.
