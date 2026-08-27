# Model Assets

SaProt model inference requires user-provided local model assets. The repository examples assume models have already been downloaded or copied into a local path; this skill does not bundle weights and does not require network downloads.

## Checkpoint Catalog

| Model family | Typical use | Loading form | Notes |
| --- | --- | --- | --- |
| `SaProt_35M_AF2` | smaller structure-aware SaProt inference | local Hugging Face directory, sometimes paired with `.pt` checkpoint | Use SA-token input for best frozen embeddings. |
| `SaProt_650M_AF2` | main structure-aware SaProt inference | local Hugging Face directory; `SaProt_650M_AF2.pt` for ESM loader | README examples use this checkpoint for loading, embeddings, and mutation effects. |
| `SaProt_650M_PDB` | 650M checkpoint with PDB phase data | local Hugging Face directory | Same path distinction applies. |
| `SaProt_1.3B_AF2` | larger SaProt model | local Hugging Face directory | Documented as better for AA-only usage than 35M/650M. |
| `SaProt_1.3B_AFDB_OMG_NCBI` | larger SaProt model trained with additional sequence data | local Hugging Face directory | Also documented as suitable for AA-only usage. |
| `SaProt_650M_AF2_inverse_folding` | inverse folding | local Hugging Face directory | Use with `SaProtIFModel.predict`. |

## Directory vs `.pt` Paths

Use a local Hugging Face directory for these APIs:

- `EsmTokenizer.from_pretrained(model_dir)`
- `EsmForMaskedLM.from_pretrained(model_dir)`
- `SaprotBaseModel(config_path=model_dir, load_pretrained=True)`
- `SaprotFoldseekMutationModel(config_path=model_dir, load_pretrained=True, ...)`
- `SaProtIFModel(config_path=model_dir, load_pretrained=True)`

Use a local `.pt` checkpoint file for this API only:

- `utils.esm_loader.load_esm_saprot(pt_path)`

A common failure is passing a `.pt` file to Hugging Face loaders or passing a directory to `load_esm_saprot`.

## Expected Hugging Face Directory Assets

A local SaProt Hugging Face directory normally needs:

- Model config such as `config.json`.
- Tokenizer metadata such as `tokenizer_config.json`, `special_tokens_map.json`, `vocab.txt`, or equivalent tokenizer files.
- Weight files such as `pytorch_model.bin`, `model.safetensors`, or sharded weight indexes and shard files.

Exact filenames can vary by model export. Validate the directory with the bundled checker and, if available, `--try-tokenizer`.

## Expected `.pt` Checkpoint Assets

The ESM loader expects a single `.pt` file readable by `torch.load`. The loaded object must include:

- `model`: state-dict weights.
- `config`: model shape/settings including layer count, embedding dimension, attention heads, and token dropout.

The checker validates only file presence, extension, and optional dependency availability; it intentionally does not load heavy checkpoint tensors.

## SA-Token and AA-Only Caveat

SaProt 35M and 650M models can accept amino-acid-only sequences in some contexts, but their frozen embeddings are intended to work best with structure-aware AA+3Di input. Use combined tokens such as `M#EvVpQpL#VyQdYaKv` when structure tokens are available. The 1.3B SaProt variants are documented as handling AA-only sequences better.

## Device Placement

Use CPU-safe code by default:

```python
device = "cuda" if torch.cuda.is_available() else "cpu"
model = model.to(device).eval()
inputs = {name: tensor.to(device) for name, tensor in inputs.items()}
```

Avoid hard-coding CUDA unless the runtime has a compatible PyTorch/CUDA stack and the selected model fits GPU memory. Large checkpoints may be slow or memory-heavy on CPU.

## Asset Validation Script

Run:

```bash
python scripts/check_model_assets.py /path/to/model-or-checkpoint
```

Useful options:

- `--kind hf-dir` requires a directory-style model asset.
- `--kind esm-pt` requires a `.pt` checkpoint.
- `--kind auto` distinguishes by filesystem type and extension.
- `--try-tokenizer` attempts `EsmTokenizer.from_pretrained` only when `transformers` is installed.
- `--json` emits machine-readable output.
