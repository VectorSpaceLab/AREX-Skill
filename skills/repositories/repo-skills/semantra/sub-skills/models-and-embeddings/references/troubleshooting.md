# Models and Embeddings Troubleshooting

## Purpose

Use this reference for Semantra failures involving model downloads, OpenAI,
PyTorch/CUDA, transformer memory, SVM mode, or embedding backend selection.

## `OPENAI_API_KEY` is not set

Symptom: constructing OpenAI mode raises an error asking for `OPENAI_API_KEY` or
a `.env` file.

Likely cause: `--model openai` was selected without credentials available to the
Semantra process.

Recovery:

1. Confirm the user accepts sending document windows and queries to OpenAI.
2. Set the key in the shell:
   ```sh
   export OPENAI_API_KEY=...
   semantra --model openai documents/*.txt
   ```
3. Or place the key in a `.env` file that Semantra will load from the current
   directory or Semantra application directory.
4. If privacy is not acceptable, switch to `--model mpnet`, `--model minilm`, or
   a custom local `--transformer-model`.

## `APIRemovedInV1Proxy`, `openai.Embedding`, or OpenAI SDK errors

Symptom: OpenAI mode imports but fails when embedding with an error indicating
that `openai.Embedding` or `openai.Embedding.create` was removed.

Likely cause: Semantra 0.1.12 uses the pre-1.0 OpenAI Python SDK API, while the
environment has a current `openai` SDK.

Recovery options:

- Use a Semantra environment with a compatible OpenAI SDK, for example a
  version lower than 1.0, if that satisfies the user's security policy.
- Update Semantra's OpenAI integration to the current SDK before relying on
  OpenAI mode.
- Use a local transformer model to avoid the OpenAI code path.

## Hugging Face model download hangs or fails

Likely causes:

- first use of a local transformer model needs to download tokenizer/model
  files;
- network, proxy, TLS, or Hugging Face availability issues;
- model name typo or private/gated model;
- insufficient disk space in the model cache.

Recovery:

1. Verify the model name and whether it is public.
2. Test with `--model minilm` for a smaller public model.
3. If the environment is offline, pre-populate the Hugging Face cache or choose
   a model already present.
4. Keep the document corpus tiny until the model loads successfully.
5. Do not switch to OpenAI mode for private documents without explicit user
   approval.

## CUDA is not used or `torch.cuda.is_available()` is false

Semantra can still run local transformer models on CPU. CUDA is an acceleration
path.

Likely causes:

- CPU-only PyTorch build;
- no visible NVIDIA GPU or missing container GPU passthrough;
- incompatible driver/runtime;
- unsupported hardware/wheel combination.

Recovery:

```sh
python - <<'PY'
import torch
print(torch.__version__, torch.version.cuda)
print(torch.cuda.is_available(), torch.cuda.device_count())
PY
```

If CUDA is false, either proceed on CPU for small corpora, install a compatible
GPU-enabled PyTorch build, or use OpenAI mode after accepting privacy/cost.

## CUDA out of memory or process killed

Likely causes:

- large model such as `sgpt-1.3B`;
- large `--pool-size` batching too many tokens;
- other GPU jobs consuming memory;
- long documents with overlapping windows.

Recovery:

- Switch to `minilm` or `mpnet` before trying a larger model.
- Lower `--pool-size`.
- Use smaller windows or fewer documents per run.
- Run on CPU only if runtime is acceptable.
- Avoid starting with a huge corpus until a tiny fixture has passed.

## `--svm` fails with missing `sklearn`

Symptom: a query route using SVM fails with `ModuleNotFoundError: No module named
'sklearn'` or similar.

Likely cause: Semantra imports `sklearn.svm` lazily for SVM mode, but
`scikit-learn` is not declared in Semantra's package dependencies.

Recovery:

```sh
python -m pip install scikit-learn
semantra --svm documents/*.txt
```

Only install it when SVM mode is selected; default Annoy/exact query paths do
not require it.

## `--svm` with SGPT or another asymmetric model fails

Semantra rejects SVM mode when the selected model reports asymmetric query and
document embeddings. The `sgpt` and `sgpt-1.3B` presets are asymmetric.

Recovery:

- Use a symmetric model such as `mpnet` or `minilm` for SVM.
- Or keep the SGPT model and use the default kNN/Annoy query path.

## Embeddings are slow even after the model loads

Potential mitigations:

- Use `minilm` for quick exploratory searches.
- Use fewer or larger windows if precision allows.
- Use `--no-server` to preprocess overnight and launch the UI later from cache.
- Use a GPU-enabled PyTorch environment if available.
- Consider OpenAI mode only after privacy/cost approval.

## Query results seem poor after changing models

Likely causes:

- the model is not well matched to language/domain;
- windows are too small or too large;
- the cache directory contains multiple model/config groups and the command is
  not using the intended one;
- SGPT special tokens are missing for a custom SGPT-like model.

Recovery:

1. Confirm the selected preset or `--transformer-model`.
2. Read [model-selection.md](model-selection.md) and choose a model for the
   user's language/domain.
3. Inspect cache config groups with the document-indexing cache helper.
4. Rebuild with `--force` if needed.
