# UltraRAG Server Backends and Config

## Purpose

Read this when you need to choose a backend, extra, or configuration block for a
server workflow.

## Retriever backends

### `backend`

- `sentence_transformers`
- `infinity`
- `openai`
- `bm25`

### `index_backend`

- `faiss`
- `milvus`

### `websearch_backend`

- `tavily`
- `exa`
- `zhipuai`

### Common retriever config keys

- `model_name_or_path`
- `corpus_path`
- `embedding_path`
- `collection_name`
- `batch_size`
- `top_k`
- `gpu_ids`
- `query_instruction`
- `is_multimodal`
- `overwrite`
- `retrieve_thread_num`
- `retriever_url`

### Retriever dependency notes

- `bm25` workflows rely on the local tokenizer helpers and the `bm25s`
  ecosystem.
- `sentence_transformers` and `infinity` need embedding model packages.
- `openai` backend needs a compatible `openai` release and API credentials.
- `faiss` and `milvus` indexes require their respective indexing backends.
- Web search requires one of the provider packages plus API keys.

## Generation backends

### `backend`

- `vllm`
- `openai`
- `hf`

### Common generation config keys

- `backend_configs`
- `sampling_params`
- `extra_params`
- `system_prompt`
- `image_tag`

### Generation dependency notes

- `vllm` is the GPU serving path and needs a CUDA-capable environment.
- `hf` needs the Hugging Face stack and model weights.
- `openai` needs a compatible OpenAI release and API credentials.
- The inspection environment verified that `openai 1.109.1` works with the
  generation server import; newer major versions may not expose the internal
  `httpx_logger` import used by the source.

## Corpus backends and extras

### `chunk_backend`

- `token`
- `sentence`
- `recursive`

### `tokenizer_or_token_counter`

- `character`
- other token counter or tokenizer implementations supported by the source
  helpers

### Corpus config keys

- `parse_file_path`
- `text_corpus_save_path`
- `image_corpus_save_path`
- `mineru_dir`
- `mineru_extra_params`
- `raw_chunk_path`
- `chunk_path`
- `use_title`
- `chunk_backend_configs`
- `chunk_size`

### Corpus dependency notes

- Text and image corpus builders use the core package plus document-processing
  helpers.
- `mineru_parse` and `build_mineru_corpus` need the `mineru[core]` extra.
- Document conversion may also depend on local Office tooling for some file
  types.

## Evaluation backends and extras

### Config keys

- `metrics`
- `save_path`
- `qrels_path`
- `run_path`
- `ks`
- `ir_metrics`
- `run_new_path`
- `run_old_path`
- `n_resamples`

### Dependency notes

- `evaluate` uses `rouge-score`.
- `evaluate_trec` and `evaluate_trec_pvalue` need a `pytrec_eval`-compatible
  install such as `pytrec-eval-terrier`.

## Prompt templates

- Prompt functions use Jinja templates under `prompt/*.jinja`.
- The prompt server parameter file maps prompt names to template paths.
- The prompt layer uses `SandboxedEnvironment` from Jinja2.

## Memory and KB behavior

- `memory` uses a `user_id` parameter and defaults to `default`.
- The UI backend stores chat, memory, and knowledge-base data under the storage
  root selected by `ULTRARAG_UI_STORAGE_ROOT` or the default `ui/storage`.
- Memory collection names and visible-user mappings are managed by the UI
  storage layer and the Milvus-backed KB helper.

## Remote server and deployment notes

- HTTP MCP server paths require Node.js 20+ and `mcp-remote`.
- The UI frontend build and the case-study viewer need Node.js 22+ and npm 10+.
- `show case` and the standalone FastAPI wrappers need `fastapi` and `uvicorn`.
- Standalone retriever deployment is source-evidenced by a JSON config; the
  relevant backend keys are distilled above. Create or approve a bundled wrapper
  before turning that deployment path into a reusable script.

## Useful parameter defaults

The source parameter files provide these notable defaults:

- Retriever: `backend=sentence_transformers`, `index_backend=faiss`,
  `websearch_backend=tavily`, `top_k=5`
- Generation: `backend=vllm`, `sampling_params.max_tokens=2048`
- Corpus: `chunk_backend=token`, `chunk_size=512`
- Evaluation: QA metrics plus retrieval metrics and significance testing
- Benchmark: NQ-style sample data with key mapping for `question` and
  `golden_answers`

## Compatibility reminders

- A core import of the generation server can fail if the OpenAI package is too
  new.
- Evaluation imports can fail if `rouge-score` is absent.
- Retriever imports from a checkout need the retriever source directory on
  `sys.path` because the module uses local helper imports.
