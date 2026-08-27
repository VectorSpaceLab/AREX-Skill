# Troubleshooting

Use this root reference for package-wide FlagEmbedding setup, imports, optional
dependencies, backend, model cache, and remote-code failures. Use the nearest
sub-skill troubleshooting reference for workflow-specific data, inference,
fine-tuning, or evaluation issues.

## Import Fails

Symptoms:

- `ModuleNotFoundError: No module named 'FlagEmbedding'`
- Public imports such as `FlagAutoModel` or `FlagAutoReranker` are missing.
- `pip show FlagEmbedding` reports a different version than expected.

Checks and fixes:

```bash
python -m pip show FlagEmbedding
python - <<'PY'
from importlib.metadata import version
from FlagEmbedding import FlagAutoModel, FlagAutoReranker
print(version("FlagEmbedding"), FlagAutoModel, FlagAutoReranker)
PY
```

Install or upgrade the package in the active environment:

```bash
python -m pip install -U FlagEmbedding
```

For source checkouts, use editable install only when the task is to inspect or
modify that checkout:

```bash
python -m pip install -e .
```

Do not mix multiple editable checkouts in the same environment when validating a
repo-specific issue.

## Dependency Mismatch

Symptoms:

- `pip check` reports broken requirements.
- Transformer or PEFT imports fail after an upgrade.
- Compatibility code around `is_torch_fx_available` is involved.

Checks:

```bash
python -m pip check
python - <<'PY'
import transformers
from FlagEmbedding.utils.transformers_compat import is_torch_fx_available
print(transformers.__version__, isinstance(is_torch_fx_available(), bool))
PY
```

Fix by installing a consistent package set. FlagEmbedding 1.4.0 declares
`transformers>=4.44.2,<6.0.0` plus PyTorch, datasets, accelerate,
sentence-transformers, PEFT, IR Datasets, SentencePiece, and Protobuf.

## Evaluation Optional Dependencies Missing

Symptoms:

- `ModuleNotFoundError: No module named 'faiss'`
- `ModuleNotFoundError: No module named 'pytrec_eval'`
- `python -m FlagEmbedding.evaluation.custom --help` fails before printing help.

CPU evaluation fix:

```bash
python -m pip install faiss-cpu pytrec_eval
python -m FlagEmbedding.evaluation.custom --help
```

Use GPU FAISS only when the runtime environment is explicitly prepared for that
CUDA stack. Do not install CPU and GPU FAISS variants blindly into one prefix.

## Fine-Tuning Extras Missing

Symptoms:

- `ModuleNotFoundError: No module named 'deepspeed'`
- flash-attn build/import errors.
- Training commands parse arguments but fail during DeepSpeed initialization.

Fix:

```bash
python -m pip install -U "FlagEmbedding[finetune]"
```

Then verify the backend stack before launching training. The extra declares
DeepSpeed and flash-attn, but it cannot guarantee CUDA driver, PyTorch ABI,
compiler, or GPU compatibility.

## CUDA, CPU, And Precision

Symptoms:

- `torch.cuda.is_available()` is false unexpectedly.
- CPU smoke checks succeed but GPU runs fail.
- fp16/bf16 raises unsupported dtype or numerical errors.

Checks:

```bash
python - <<'PY'
import torch
print(torch.__version__, torch.version.cuda)
print(torch.cuda.is_available(), torch.cuda.device_count())
if torch.cuda.is_available():
    print(torch.cuda.get_device_name(0), torch.cuda.get_device_capability(0))
PY
```

Use CPU and full precision for initial smoke checks: `devices="cpu"`,
`use_fp16=False`, and `use_bf16=False`. Move to CUDA only after package imports,
model cache policy, and memory budget are clear.

## Model Downloads, Cache, And Tokens

Symptoms:

- Loading a model id downloads files unexpectedly.
- Offline runs fail although the model name is correct.
- Hugging Face authorization or gated-model errors appear.

Fixes:

- Use a complete local checkpoint directory when offline behavior is required.
- Pass `cache_dir` or standard Hugging Face cache environment variables from the
  runtime context; do not hard-code machine-specific cache paths.
- Use tokens only for models or datasets that require them.
- Ask before enabling network downloads for benchmark datasets or large model
  weights.

## Remote Code

Symptoms:

- Unknown architecture or custom class loading errors.
- A model requires `trust_remote_code=True`.

Guidance:

- Keep `trust_remote_code=False` for standard checkpoints.
- Set `trust_remote_code=True` only after reviewing or accepting the checkpoint
  code source.
- For local custom checkpoints, make sure the checkpoint directory contains the
  required config and modeling files.

## Run The Bundled Probe

From this skill directory, run:

```bash
python scripts/check_flag_embedding_env.py
```

Add optional checks when relevant:

```bash
python scripts/check_flag_embedding_env.py --check-evaluation --check-finetune --check-cuda
```

The probe performs imports and dependency checks only. It does not download
models, run training, or start benchmark evaluation.
