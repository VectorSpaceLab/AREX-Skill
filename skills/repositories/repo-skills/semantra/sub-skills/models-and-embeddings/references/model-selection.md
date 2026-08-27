# Model Selection

## Purpose

Read this when deciding which Semantra embedding backend to use, constructing
model-related CLI flags, or explaining privacy, cost, download, memory, and GPU
tradeoffs.

## Preset registry

Semantra 0.1.12 exposes these preset names through `--model` and
`semantra --list-models`:

| Preset | Underlying model | Pool defaults | Best fit | Watch out |
| --- | --- | --- | --- | --- |
| `mpnet` | `sentence-transformers/all-mpnet-base-v2` | `pool_size=15000` | Default local quality/speed balance. | First run may download model files; CPU can be slow on large corpora. |
| `minilm` | `sentence-transformers/all-MiniLM-L6-v2` | `pool_size=50000` | Fast, lean local indexing and smoke tests. | Lower accuracy than `mpnet` for some semantic tasks. |
| `sgpt` | `Muennighoff/SGPT-125M-weightedmean-msmarco-specb-bitfit` | `pool_size=10000` | Higher-quality asymmetric search. | Uses query/document special tokens; incompatible with `--svm`. |
| `sgpt-1.3B` | `Muennighoff/SGPT-1.3B-weightedmean-msmarco-specb-bitfit` | `pool_size=1000` | Larger SGPT model when quality matters and resources allow. | Large memory/runtime footprint; may need a GPU. |
| `openai` | `text-embedding-ada-002` | `pool_size=50000`, `pool_count=2000`, `cost_per_token=0.0000004` | Offload embedding work to OpenAI when speed matters and data sharing is acceptable. | Requires API key, network, cost acceptance, and a compatible OpenAI SDK. |

Check the installed registry without instantiating models:

```sh
python scripts/inspect_model_registry.py
```

## Private local default

For sensitive local documents, start with a local transformer model so document
text stays on the user's machine:

```sh
semantra --model mpnet --semantra-dir ./semantra-cache report.pdf notes/*.txt
```

Use `minilm` for faster tests or modest hardware:

```sh
semantra --model minilm --no-server --semantra-dir ./smoke-cache tiny/*.txt
```

The first run may contact Hugging Face to download tokenizer/model files unless
those files are already cached. Avoid running this command on private or airgap
systems until the user accepts the download/cache behavior.

## Custom Hugging Face models

Use `--transformer-model` when the preset registry does not fit the language,
domain, or model family:

```sh
semantra --transformer-model intfloat/multilingual-e5-base documents/*.txt
```

Some embedding models require special query/document prefixes or suffixes. Add
these only when the model card or known recipe requires them:

```sh
semantra \
  --transformer-model Muennighoff/SGPT-1.3B-weightedmean-msmarco-specb-bitfit \
  --query-token-pre '[' --query-token-post ']' \
  --doc-token-pre '{' --doc-token-post '}' \
  documents/*.txt
```

The Semantra CLI option names use hyphens: `--query-token-pre`, not
`--query_token_pre`.

## OpenAI mode

Use OpenAI only when the user explicitly accepts:

- document windows and queries will be sent to OpenAI;
- `OPENAI_API_KEY` must be present in the shell environment or a `.env` file
  that Semantra loads;
- processing incurs a one-time embedding cost per document/settings;
- queries also call OpenAI, usually at a much smaller cost;
- Semantra 0.1.12 uses the legacy `openai.Embedding.create` API, so current
  `openai` SDK versions may require a compatibility pin such as `openai<1` or a
  Semantra code update.

Command form:

```sh
OPENAI_API_KEY=... semantra --model openai --no-confirm documents/*.txt
```

Use `--no-confirm` only when the user already accepted the cost estimate or the
workflow is automated with a known budget.

## CUDA and CPU behavior

For local transformer models, Semantra checks `torch.cuda.is_available()` when
`TransformerModel` is created. If CUDA is available, it moves the model and
input tensors to CUDA; otherwise it uses CPU. CUDA speeds up embedding but is
not required for core Semantra behavior.

Use these checks before promising GPU acceleration:

```sh
python - <<'PY'
import torch
print(torch.__version__, torch.version.cuda)
print(torch.cuda.is_available(), torch.cuda.device_count())
PY
```

If CUDA is unavailable, either proceed with CPU for small corpora, install a
compatible GPU-enabled PyTorch build, or switch to OpenAI mode if the privacy and
cost tradeoffs are acceptable.

## Pool-size and pool-count tuning

Semantra pools embedding windows before calling the model:

- `--pool-size` limits the total token count batched together.
- `--pool-count` limits the number of embeddings batched together. It is mainly
  used by the OpenAI preset.

Decrease `--pool-size` when local model inference runs out of memory. Increase
it cautiously only after confirming memory headroom. For OpenAI, keep provider
rate limits and request-size errors in mind.

## SVM and Annoy interactions

The default query path uses Annoy approximate nearest neighbors. `--annoy` is a
boolean flag with default true in this Semantra release. `--svm` switches query
ranking to a linear SVM path, but:

- SVM mode lazily imports `sklearn.svm`; install `scikit-learn` if selected.
- SVM mode is rejected for asymmetric models such as SGPT.
- SVM can be slower than kNN/Annoy because it trains per query.

For most users, keep the default Annoy path and adjust model/window choices
first.
