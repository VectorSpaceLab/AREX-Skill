# CLI troubleshooting

## `omegafold` command not found

Symptoms:

```text
omegafold: command not found
```

Actions:

1. Confirm the package is installed in the active environment:
   ```bash
   python -m pip show OmegaFold
   ```
2. Confirm the console script is on `PATH`:
   ```bash
   python -c "import shutil; print(shutil.which('omegafold'))"
   ```
3. If the package imports but the console script wrapper is missing, test the installed module fallback:
   ```bash
   python -m omegafold --help
   ```
4. Keep reusable commands environment-based: activate the correct environment, repair the console script, or use the installed module fallback.

## Import or install failures

OmegaFold declares Python `>=3.8`, but its setup logic has explicit Torch wheel URL handling only for Python 3.8, 3.9, and 3.10. On newer Python versions, source installation can fail with an unsupported-Python exception.

Recommended environment constraints for legacy installs:

- Python 3.8, 3.9, or 3.10.
- `biopython` installed.
- Torch compatible with the target device; the bundled requirements pin `torch==1.12.0+cu113`.
- `numpy<2` when using Torch 1.12, because Torch 1.12 was built against NumPy 1.x and NumPy 2.x can cause ABI warnings or failures.

## Torch, CUDA, and TF32 problems

Symptoms include import errors, CUDA runtime errors, or slow CPU fallback.

Actions:

1. Check what Torch sees:
   ```bash
   python - <<'PY'
   import torch
   print('torch', torch.__version__)
   print('cuda', torch.cuda.is_available())
   print('mps', getattr(torch.backends, 'mps', None) and torch.backends.mps.is_available())
   PY
   ```
2. Match `--device` to available hardware: `cuda`, `cuda:0`, `mps`, or `cpu`.
3. If numeric reproducibility is more important than speed on CUDA, set `--allow_tf32 False`.
4. If using MPS, ensure the installed Torch build supports MPS and prefer `python -m omegafold` only when the console script wrapper is unavailable.

## Missing weights, network, or cache

Symptoms:

- A run hangs or fails while downloading from the release checkpoint URL.
- A no-network task unexpectedly tries to access the network.
- `torch.load` fails because a checkpoint file is missing or corrupt.

Actions:

1. Decide model first: model 1 uses the release-1 checkpoint; model 2 uses release-2.
2. For no-network runs, require an existing local checkpoint and pass it explicitly:
   ```bash
   omegafold input.fasta outputs/ --model 2 --weights_file /path/to/model2.pt
   ```
3. Verify the path exists before running:
   ```bash
   test -f /path/to/model2.pt
   ```
4. If a previous download was interrupted, remove or replace the partial checkpoint before retrying.

## Invalid model id

Symptoms:

```text
ValueError: Model 3 is not available, we only support model 1 and 2
```

Actions:

- Use `--model 1` or `--model 2` only.
- If using the Python API, `make_config` also accepts only `1` or `2` and raises `ValueError('model_idx must be 1 or 2')` otherwise.

## Invalid or unavailable device

Symptoms:

```text
ValueError: Device cuda is not available
ValueError: Device mps is not available
ValueError: Device type ... is not available
```

Actions:

1. Omit `--device` to let OmegaFold auto-select CUDA, then MPS, then CPU.
2. Use `--device cpu` only for tiny examples or when the user accepts slow runtime.
3. Use `--device cuda:0` only when CUDA is available and the GPU index exists.
4. Use `--device mps` only with a Torch build that supports Apple Silicon MPS.

## GPU OOM or long-sequence failure

Symptoms:

- CUDA out-of-memory exceptions.
- Runtime failure for one chain followed by `Skipping...`.
- Very slow inference after lowering memory usage.

Actions:

1. Lower `--subbatch_size`; smaller means less memory and more time.
2. For A100 80 GB and around 4096 residues, the README reports `--subbatch_size 448` as a working example.
3. If OOM persists, halve the subbatch size and retry.
4. Consider reducing `--num_cycle` only when the user accepts a quality/runtime trade-off.
5. Confirm output PDBs were produced for all expected chains; OmegaFold can skip failed chains and continue.

## FASTA and output mistakes

Symptoms:

- No PDBs appear.
- Fewer PDBs than expected appear.
- Output names are surprising.
- Invalid amino-acid assertion appears.

Actions:

1. Confirm each record starts with `>` or `:` and contains sequence lines.
2. Remember that OmegaFold sorts records by sequence length before processing.
3. Header text becomes the PDB basename, with path separators replaced by `-`; overly long headers may be replaced by an indexed name.
4. `Z`, `B`, and `U` are normalized to `E`, `D`, and `C`; `-` is treated as mask token 21; other unsupported characters can fail assertions.
5. Route detailed FASTA/PDB semantics to `../data-and-outputs/SKILL.md`.
