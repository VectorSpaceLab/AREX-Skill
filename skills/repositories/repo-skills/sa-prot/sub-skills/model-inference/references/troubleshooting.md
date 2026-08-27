# Model Inference Troubleshooting

## Missing Optional Dependencies

Symptoms:

- `ModuleNotFoundError: No module named 'torch'`
- `ModuleNotFoundError: No module named 'transformers'`
- `ModuleNotFoundError: No module named 'esm'`
- `ModuleNotFoundError: No module named 'peft'`

Guidance:

- Install `torch` for all model execution paths.
- Install `transformers` for Hugging Face SaProt loading and repository model wrappers.
- Install `fair-esm` when using `utils.esm_loader.load_esm_saprot`.
- Install `peft` only when loading or creating LoRA adapters.
- Some repository model classes may also import Lightning or metrics packages even for inference helper usage.

Run the bundled checker to get dependency guidance without importing heavy model code:

```bash
python scripts/check_model_assets.py /path/to/model-or-checkpoint
```

## Model Directory vs `.pt` Confusion

Symptoms:

- Hugging Face loaders complain that a path is not a valid model directory.
- `load_esm_saprot` fails on a directory path.
- A `.pt` checkpoint exists but tokenizer loading fails.

Fix:

- Use a local Hugging Face directory for `EsmTokenizer`, `EsmForMaskedLM`, `SaprotBaseModel`, `SaprotFoldseekMutationModel`, and `SaProtIFModel`.
- Use a local `.pt` checkpoint file only with `load_esm_saprot`.
- Do not assume the repository bundles weights; the model path must point to user-provided local assets.

## CUDA and CPU Placement

Symptoms:

- `AssertionError: Torch not compiled with CUDA enabled`
- CUDA out-of-memory errors.
- Tensors are on a different device than the model.

Fix:

```python
import torch

device = "cuda" if torch.cuda.is_available() else "cpu"
model = model.to(device).eval()
inputs = {name: tensor.to(device) for name, tensor in inputs.items()}
```

Start with CPU-safe snippets when validating path and tokenization. Move to CUDA only after confirming compatible drivers, PyTorch, and available memory.

## Tokenization Mistakes

Symptoms:

- Token list length does not match expected amino-acid length.
- Mutation position appears off by one.
- Model outputs have unexpected sequence length.

Fix:

- Combined SaProt strings are two-character AA+3Di tokens concatenated together, such as `M#EvVpQpL#VyQdYaKv`.
- Validate with `tokenizer.tokenize(seq)` before inference.
- Preserve the structure half when masking a mutation position: mutation helpers replace the amino-acid half with `#` and keep the 3Di half.
- For structure conversion from PDB/mmCIF, route to `structure-sequences` and obtain the combined sequence before using model inference.

## Mutation String Errors

Symptoms:

- `ValueError` from parsing mutation positions.
- Wrong substitution position or unexpected original amino acid.
- Combinatorial mutation score does not match expected target.

Fix:

- Mutation strings are 1-indexed amino-acid positions: `V3A` means original `V`, position `3`, mutated `A`.
- Multiple substitutions use colon syntax: `V3A:Q4M`.
- `predict_mut(seq, "V3A:Q4M")` returns one combined log-ratio score.
- `predict_pos_mut(seq, 3)` returns all mutation-effect scores at position 3.
- `predict_pos_prob(seq, 3)` returns all amino-acid probabilities at position 3.
- Check that `tokenizer.tokenize(seq)[pos - 1][0]` matches the original amino acid in the mutation string.

## AA-Only Performance Caveat

Symptoms:

- AA-only frozen embeddings perform worse than expected for 35M or 650M checkpoints.
- A user expects structure-aware gains without supplying structure tokens.

Fix:

- For 35M and 650M SaProt checkpoints, use structure-aware AA+3Di tokens for frozen embeddings whenever possible.
- Use `#` as the structure token for low-confidence or masked 3Di regions, not as a blanket substitute for all structural information unless no structure is available.
- Consider the 1.3B SaProt variants for AA-only workflows.

## Inverse Folding Assertions

Symptoms:

- Assertion that amino-acid and Foldseek sequence lengths differ.
- Assertion that method must be `argmax` or `multinomial`.
- Assertion that `num_samples` must be 1 for `argmax`.

Fix:

- Pass separate strings: `aa_seq` with masked amino acids and `struc_seq` with Foldseek 3Di tokens.
- Ensure `len(aa_seq) == len(struc_seq)`.
- Use `method="argmax", num_samples=1` for deterministic prediction.
- Use `method="multinomial", num_samples=N` for multiple sampled sequences.

## No Bundled Weights

Symptoms:

- `FileNotFoundError` for model path.
- Empty `weights/PLMs` or placeholder files only.
- User expects examples to run immediately after cloning.

Fix:

- Download or copy the desired SaProt model assets into a local directory outside the runtime skill tree or into an agreed project model-assets location.
- Validate the path before running inference.
- Keep public skill content generic and do not embed local absolute paths in reusable recipes.
