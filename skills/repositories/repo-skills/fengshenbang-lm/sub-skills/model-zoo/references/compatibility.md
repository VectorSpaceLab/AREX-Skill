# Compatibility

This reference covers dependency and backend compatibility for Fengshen model imports. For symptom-driven fixes, also read [troubleshooting.md](troubleshooting.md).

## Verified import-oriented stack

Construction evidence verified import and CLI/parser inspection with an older Transformers-compatible stack. The important public lesson is the version relationship, not a machine-specific environment.

| Package | Compatible value observed for import checks | Why it matters |
|---|---:|---|
| Python | 3.10 | Old enough for this 2022-era stack, modern enough for current package tooling. |
| `fengshen` | 0.0.1 | Package distribution name used by this repository. |
| PyTorch | 2.0.1 CPU build for import checks | CPU is enough for import/config/parser checks; CUDA is optional for large examples. |
| Transformers | 4.20.1 | Provides `transformers.cached_path` and `transformers.pytorch_utils.softmax_backward_data`, both used by Fengshen modules. |
| Datasets | 2.0.0 | Aligns with the package-era data APIs. |
| PyTorch Lightning | 1.9.x | Import-compatible with the checked pipeline/training modules. |
| TorchMetrics | 0.11.x | Avoids newer metric API incompatibilities in training/pipeline code. |
| DeepSpeed | 0.9.x importable with optional ops disabled | Some model/training utilities import DeepSpeed classes, but CUDA op builds are not needed for import-only checks. |
| NumPy | `<2` | Avoids older dependency breakage around removed compatibility symbols. |
| Setuptools | `<81` | Keeps legacy `pkg_resources` behavior available. |
| PyArrow/FSSpec | pyarrow 10.x, fsspec 2022.x | Avoids data-stack breakage with older `datasets`. |
| SentencePiece | installed when using DeltaLM/Transformer-XL/ZEN tokenizers that need it | Tokenizer imports and local tokenizer loading can fail without it. |
| `jsonlines` | optional for DAVAE/GAVAE/PPVAE imports | Some VAE modules import it even for class import; install only when VAE work is selected. |

A useful installation strategy is: install a compatible base stack first, install `fengshen` without forcing broad dependency upgrades, then run import checks. Add optional dependencies such as `sentencepiece` or `jsonlines` only when the selected family needs them. Do not upgrade Transformers casually; too-new versions are a known break source for this checkout.

## Transformers compatibility traps

| Error or signal | Likely cause | Recovery |
|---|---|---|
| `ImportError: cannot import name 'cached_path' from 'transformers'` | Transformers is too new for modules that import `cached_path` directly. ZEN tokenization/ngram utilities and Fengshen auto/dynamic helpers need the old symbol. | Use an isolated environment and pin Transformers to a compatible 4.20-era release. Re-run `scripts/check_model_imports.py`. |
| `ImportError: cannot import name 'softmax_backward_data' from 'transformers.pytorch_utils'` | Transformers is too new for Fengshen DeBERTa-v2's custom `XSoftmax` implementation. | Pin Transformers to a compatible 4.20-era release. Do not edit the model code unless you are intentionally porting the package. |
| Auto factory raises `KeyError` for a valid-looking family | Fengshen custom auto mappings are narrow and do not cover every package family. | Use direct family imports, or register a mapping in local task code only. See [auto-and-tokenizers.md](auto-and-tokenizers.md). |
| `Unrecognized model ... should have a model_type key` | Local config has no standard `model_type`, or the model type is not registered in Fengshen's custom auto mapping. | Inspect `config.json`; for Longformer/RoFormer use `model_type: "longformer"` or `"roformer"`. For other families use direct imports. |
| Tokenizer auto route cannot instantiate | Missing `tokenizer_class`, missing SentencePiece, or custom `fengshen_tokenizer_type` is not wired into the current pipeline. | Directly import the family tokenizer and verify local tokenizer files. |

## CPU vs CUDA expectations

Import checks do not require CUDA. Loading real checkpoints may require significant memory:

| Path | CPU suitability | CUDA/GPU notes |
|---|---|---|
| Top-level imports and configs | Fully suitable on CPU. | CUDA not needed. |
| Longformer/RoFormer/Megatron-T5/DeltaLM/BART/ALBERT small local configs | Config-only suitable on CPU. | Loading large weights may require GPU or high RAM. |
| ZEN n-gram/tokenizer local checks | Suitable on CPU if files exist. | CUDA not needed for tokenizer/config checks. |
| LLaMA/Ziya checkpoints | Usually impractical on small CPU-only hosts. | Often needs large RAM/VRAM, quantization, sharding, or tensor-parallel planning. Route conversion/runtime recipes to `../examples-conversion/SKILL.md`. |
| Megatron fused kernels | Not a CPU substitute. | Requires compatible CUDA/PyTorch/toolchain and compiled extensions. Route training/backend details to `../data-training/SKILL.md`. |
| DeepSpeed optimizer/runtime paths | Import may work on CPU with optional ops disabled. | Real training/ZeRO/fused optimizer paths need CUDA/runtime verification. |
| Taiyi CLIP inference | Small checks may run on CPU. | Full image/text embedding or diffusion-style recipes can require vision dependencies, large model downloads, and GPU for speed/VRAM. |

## Model download and cache compatibility

- `from_pretrained("remote/model-id")` may download config, tokenizer, and weights.
- Use `local_files_only=True` when diagnosing a local cache or offline issue.
- A config-only call can still query/download config files if the path is a remote ID and the cache is empty.
- Generation helper files include example model IDs; do not execute those helpers as smoke tests.
- If the user is offline, ask for local checkpoint directories containing at least `config.json` and tokenizer files.

## SentencePiece and tokenizer-file compatibility

Families most likely to need SentencePiece or extra local files:

| Family | Needs |
|---|---|
| DeltaLM | `sentencepiece` package and a SentencePiece model file. |
| Transformer-XL denoise tokenizer | `sentencepiece` package and a SentencePiece model file. |
| ZEN1/ZEN2 | BERT vocabulary plus n-gram dictionary files; `cached_path` must exist in Transformers. |
| Megatron-T5 | BERT-style vocabulary accepted by `BertTokenizer`; not a standard SentencePiece T5 tokenizer. |
| Longformer/RoFormer | BERT-style vocabulary. |

When a tokenizer fails, first inspect local files and metadata; do not assume the model class is wrong.

## DeepSpeed optional imports

Some Fengshen model/training utilities import DeepSpeed even when the immediate task is not distributed training. For model-zoo work:

- An importable DeepSpeed package can satisfy import checks.
- CUDA extension builds, fused optimizers, ZeRO runtime, and Megatron fused kernels are not proven by import success.
- If DeepSpeed import itself fails and the task only needs direct model family imports, narrow the check to the target family instead of installing every training extra.
- If the task explicitly requires DeepSpeed/Megatron runtime behavior, route to `../data-training/SKILL.md` and require backend verification.

## Safe validation command

From this sub-skill directory:

```bash
python scripts/check_model_imports.py --json
```

Look for:

- `required_ok: true` for top-level exports and compatibility symbols.
- Optional family failures that match missing optional dependencies rather than core package breakage.
- Transformers version recorded in the output. If it is much newer than 4.20.x and `cached_path` or `softmax_backward_data` fails, pin the stack before continuing.
