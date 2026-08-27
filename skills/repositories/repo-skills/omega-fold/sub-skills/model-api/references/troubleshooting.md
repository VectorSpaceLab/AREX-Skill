# OmegaFold Model API Troubleshooting

Use this guide for programmatic OmegaFold failures. For command-line-only problems, route to the inference CLI sub-skill. For FASTA parsing and PDB output problems, route to the data/output sub-skill.

## Invalid Model Id

Symptom:

```text
ValueError: model_idx must be 1 or 2
```

Cause: `omegafold.make_config` only accepts `1` or `2`.

Fix:

```python
cfg = omegafold.make_config(1)  # or 2
```

If the error comes from CLI argument parsing, use `--model 1` or `--model 2`. Keep the selected config aligned with the selected weights.

## State Dict Key Errors

Symptoms:

```text
Missing key(s) in state_dict
Unexpected key(s) in state_dict
```

Common causes:

- The checkpoint is wrapped as `{"model": state_dict}` and was loaded directly.
- Model 1 weights were loaded into `make_config(2)`, or model 2 weights into `make_config(1)`.
- The file is not an OmegaFold checkpoint.

Fix pattern:

```python
state_dict = torch.load(weights_file, map_location="cpu")
state_dict = state_dict.get("model", state_dict)
model.load_state_dict(state_dict)
```

If keys still mismatch, verify the model id and checkpoint family before relaxing strict loading. Avoid `strict=False` unless the user explicitly accepts incomplete or experimental inference.

## Missing `model` Key

Symptom:

```text
KeyError: 'model'
```

Cause: some code assumes the checkpoint always has a top-level `model` key. OmegaFold's own flow accepts either a raw state dict or a wrapped one after parsing.

Fix:

```python
state_dict = torch.load(weights_file, map_location="cpu")
state_dict = state_dict.get("model", state_dict)
```

## Shape or Device Errors in `forward`

Symptoms include tensor shape assertions, device mismatch errors, or failures in PLM/GeoFormer/structure modules.

Checklist:

- Use `pipeline.fasta2inputs` to create `inputs` instead of hand-assembling tensors.
- Confirm each cycle dictionary has `p_msa` and `p_msa_mask` with matching `[num_pseudo_msa + 1, num_res]` shapes.
- Move model and inputs to the same device: `model.to(device)` and `pipeline.fasta2inputs(..., device=torch.device(device))`.
- Keep `fwd_cfg` as an `argparse.Namespace` or object with at least `subbatch_size` and `num_recycle` attributes when using the release path.
- Keep `num_recycle` consistent with the number of prepared cycles from `fasta2inputs(..., num_cycle=...)`.

## Out of Memory From API Calls

Symptoms:

```text
CUDA out of memory
MPS backend out of memory
Killed
```

Fixes:

- Lower `fwd_cfg.subbatch_size`, for example from `None` to half the residue count, then smaller values if needed.
- Lower `num_cycle` / `num_recycle` for faster, lower-memory exploratory runs.
- Use `torch.no_grad()` and `model.eval()`.
- Predict one sequence at a time; `fasta2inputs` already yields entries sequentially and sorted by sequence length.
- Fall back to CPU for small debugging runs if accelerator memory is not enough, but expect slow inference.

## No-Weight Inference Warning

Symptom:

```text
Inferencing without loading weight
```

Cause: `state_dict` was `None` or loading was skipped. The model will contain randomly initialized weights and predictions are not meaningful.

Fix: provide a real OmegaFold model 1 or model 2 checkpoint, load it onto CPU, unwrap a top-level `model` key if present, then call `model.load_state_dict(state_dict)` before inference.

## Torch, CUDA, MPS, and NumPy Compatibility

Known package facts:

- The release dependency pins `torch==1.12.0+cu113` from PyTorch CUDA 11.3 wheels.
- The setup logic only knows Python 3.8, 3.9, and 3.10 wheel tags for the bundled Torch URL, although package metadata says Python `>=3.8`.
- Torch 1.12 was built against NumPy 1.x. NumPy 2.x can trigger ABI warnings or import/runtime failures.

Fixes:

```bash
python -m pip install "numpy<2"
python -m pip install biopython
```

Install a PyTorch build that matches the Python version, operating system, accelerator, and driver. For CUDA, verify `torch.cuda.is_available()` before choosing `cuda`. For Apple Silicon MPS, use a PyTorch version that supports `torch.backends.mps.is_available()` and choose `mps` only when it returns true.

## Explicit Device Not Available

Symptoms:

```text
ValueError: Device cuda is not available
ValueError: Device mps is not available
ValueError: Device type ... is not available
```

Cause: `pipeline._get_device` validates explicit accelerators. `None` auto-selects CUDA, then MPS, then CPU.

Fix:

```python
device = pipeline._get_device(None)      # auto
# or
assert torch.cuda.is_available()
device = pipeline._get_device("cuda")
```

For portable scripts, probe availability first and keep a CPU fallback for inspection-only tasks.

## Safe API Inspection Fails

If `scripts/inspect_model_api.py` cannot import `omegafold`, install the package in the current Python environment before using the sub-skill. If import fails with NumPy/Torch ABI warnings or errors, constrain NumPy below 2 and install a compatible Torch wheel before debugging OmegaFold itself.
