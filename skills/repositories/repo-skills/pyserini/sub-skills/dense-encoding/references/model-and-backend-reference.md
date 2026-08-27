# Model and Backend Reference

Use this reference to choose Pyserini dense encoder classes, query/corpus encoding modes, devices, and optional backends.

## Encoder Class Matrix

Pyserini can infer many encoder classes from model names, but explicit `--encoder-class` is safer for reproducible commands.

| Workflow | Corpus encoder class | Faiss query encoder class | Notes |
| --- | --- | --- | --- |
| DPR | `dpr` | `dpr` | Uses DPR document/question encoder families; model and tokenizer must match the index. |
| BPR | `bpr` | `bpr` | Faiss search can use `--searcher bpr`, `--binary-hits`, and `--rerank`. |
| TCT-ColBERT | `tct_colbert` | `tct_colbert` | Common for MS MARCO dense passage indexes. |
| ANCE | `ance` | `ance` | Supports ANCE PRF in Faiss search with `--prf-method ance-prf`. |
| Sentence Transformers | `sentence-transformers` | `sentence` | Defaults to mean pooling and L2 normalization in Pyserini wrappers. |
| Contriever | `contriever` | `contriever` | Defaults to mean pooling without L2 normalization. |
| Auto models | `auto` | `auto` | Use `--pooling`, `--l2-norm`, and `--prefix` explicitly. |
| Aggretriever | inferred or auto | `aggretriever` | Query side appears in Faiss search. |
| Arctic | `arctic` | `arctic` | Model-specific Hugging Face dependencies may download weights. |
| CosDPR | not typical | `cosdpr` | Query-side Faiss search class. |
| DKR-R | not typical | `dkrr` | Query-side Faiss search class. |
| SPLADE/UniCOIL sparse encoders | `splade` or related sparse classes | use impact/Lucene paths | These produce sparse vectors and usually route to impact indexing/search, not Faiss dense search. |
| OpenAI embeddings | `openai-api` with `--use-openai` | `openai-api` | Requires OpenAI credentials and network access at runtime. |
| CLIP/multimodal | `clip` inferred by model name plus `--multimodal` when needed | CLIP-like inferred path | Text/image behavior depends on fields containing paths or text. |
| UniIR | `uniir` | `uniir` | Optional package path; may require CLIP and an instruction config. |
| Qwen3 | `qwen3` | `qwen3` | Supports `--explicit-truncate`, pooling, L2 normalization, and prefixes. |
| DSE | `dse` | `dse` | Supports multimodal and pooling controls. |
| MMEB | `mmeb` | `mmeb` | Requires the VLM2Vec/MMEB optional stack. |

## Device Choices

There are two device knobs in dense workflows:

- `--device` controls Torch/query or corpus encoder inference.
- `--faiss-device` controls Faiss search for `python -m pyserini.search.faiss`.
- `python -m pyserini.index.faiss --device` controls Faiss index construction.

Safe defaults:

- Use `--device cpu` for deterministic, low-risk command templates.
- Use `--faiss-device cpu` unless a GPU Faiss build is installed.
- Do not pass `--fp16` on CPU-only Torch runs.
- Use CUDA devices such as `cuda:0` only after confirming Torch sees CUDA and the installed Faiss package supports GPU if Faiss GPU acceleration is needed.

Common mismatch patterns:

- `torch` installed as CPU-only but command uses `--device cuda:0`.
- `faiss-cpu` installed but command uses `--faiss-device cuda:0`.
- CUDA Torch installed but the driver/runtime is unavailable in the current environment.

## Encoded Queries vs Online Encoders

Use `--encoded-queries` when:

- the index has matching pre-encoded query vectors;
- the user wants to avoid model downloads or GPU requirements;
- reproducibility requires a known encoded query set;
- OpenAI or Hugging Face credentials are unavailable.

Use online `--encoder` when:

- queries are custom and no encoded query set exists;
- the model is already local or cached;
- the user accepts potential model downloads and runtime cost;
- query prefixes, instructions, or multimodal input must be generated at runtime.

Faiss search can also auto-load known encoded queries for some topic names when neither `--encoder` nor `--encoded-queries` is supplied, but explicit `--encoded-queries` is more auditable.

## OpenAI Embeddings

OpenAI document encoding uses `encoder --encoder-class openai-api --use-openai` and a model name accepted by the OpenAI embeddings API. Query search uses `--encoder-class openai-api --encoder MODEL`.

Checklist before running:

- Confirm the user authorizes network calls and external API usage.
- Confirm credentials are available in the runtime environment, commonly via `OPENAI_API_KEY`.
- Set a conservative `--rate-limit` for corpus encoding.
- Preserve user data/privacy constraints; do not send private corpora to OpenAI without explicit approval.

## Multimodal, UniIR, and MMEB

These workflows are optional and dependency-heavy.

- CLIP-style workflows may use `--multimodal` and field names that contain file paths. Pyserini resolves relative path fields against the collection file directory when the field name includes `path`.
- UniIR may require an instruction config via `--instruction-config` on Faiss search and optional packages beyond the base install.
- MMEB requires its optional vision-language stack; failures often mention missing VLM2Vec/MMEB dependencies.
- Do not use these as default examples for a new user unless their task explicitly mentions multimodal, UniIR, MMEB, image-text retrieval, or instructions.

## Sparse-Dense Boundary

Some classes live under `pyserini.encode` but produce sparse vectors or impact-style representations. Examples include SPLADE and UniCOIL. Route those to Lucene impact indexing/search unless the task explicitly asks for dense/Faiss behavior.

Dense/Faiss artifacts generally have:

- vectors as float arrays;
- Faiss `index` plus `docid`; or
- encoded JSONL with `vector: [float, ...]`.

Sparse/impact artifacts generally have:

- token-weight dictionaries in `vector`;
- Lucene impact indexes;
- `LuceneImpactSearcher` or `SlimSearcher` workflows.
