# ESM Troubleshooting

Use this reference for failures that cut across multiple ESM workflows. Workflow-specific details live in the nearest sub-skill troubleshooting file.

## Base Install and Import Failures

Symptoms:

- `ModuleNotFoundError: No module named 'esm'`.
- `import esm` fails because PyTorch is missing.
- A package named `esm` imports but does not expose `esm.pretrained` or `esm.Alphabet`.

Responses:

1. Install the public distribution name `fair-esm`; the import package is `esm`.
2. Install a PyTorch build that matches the target Python/platform before using model APIs.
3. Run `python scripts/check_esm_install.py` from this skill to verify base import and public symbols without downloading weights.
4. If another package shadows `esm`, inspect `python -c "import esm; print(esm.__file__)"` in the active environment and remove the conflict.

## Model Download and Cache Failures

Symptoms:

- HTTP errors from model names.
- Slow or blocked downloads through Torch Hub.
- Local `.pt` checkpoint loads but contact predictions warn about missing regression weights.

Responses:

1. Confirm the model name exactly matches a public loader such as `esm2_t6_8M_UR50D`, `esm2_t33_650M_UR50D`, `esm_msa1b_t12_100M_UR50S`, `esm1v_t33_650M_UR90S_1`, `esm_if1_gvp4_t16_142M_UR50`, or `esmfold_v1`.
2. If using a local checkpoint path, provide the sibling `-contact-regression.pt` file when contact maps matter.
3. Use a stable Torch Hub cache/model directory for repeated runs; ESMFold CLI accepts `--model-dir`.
4. If network access is not allowed, restrict work to command construction, input validation, cached checkpoints, or user-provided local `.pt` files.

## Optional Dependency Boundaries

Base embeddings usually need only `fair-esm` plus PyTorch. Other workflows need more:

- ESMFold: optional `fair-esm[esmfold]` stack plus OpenFold-style dependencies; the original setup notes use older Python/CUDA constraints.
- Inverse folding: PyTorch Geometric and a `biotite` version compatible with the repository's `filter_backbone` import.
- Variant scoring: `pandas`, Biopython-style FASTA/MSA handling in the original example; this skill bundles a runner that avoids Biopython for MSA parsing but still needs `torch` and `esm`.

Use isolated environments for optional stacks. Do not upgrade a working base ESM environment just to satisfy ESMFold or IF1 unless the user approves the risk.

## GPU, CUDA, and Memory Issues

Symptoms:

- CUDA OOM during embeddings or folding.
- `torch.cuda.is_available()` is false on a GPU host.
- CPU-only runs are extremely slow.
- CPU offload fails with distributed/NCCL errors.

Responses:

1. Check `python -c "import torch; print(torch.__version__, torch.version.cuda, torch.cuda.is_available())"` in the target environment.
2. For embeddings, lower batch size/tokens per batch or choose a smaller model.
3. For ESMFold, lower `--max-tokens-per-batch`, set `--chunk-size 128` or smaller, reduce recycles, or use `--cpu-offload` only when CUDA/NCCL works.
4. For CPU-only ESMFold, expect slow inference; tiny sequences are appropriate for smoke tests, not large production folding.
5. Do not interpret `--cpu-offload` as CPU-only; it still requires a CUDA-capable setup.

## CLI and Data Misuse

Symptoms:

- `esm-extract` rejects MSA Transformer models.
- FASTA labels collide and output `.pt` files overwrite or assertion fails.
- `esm-fold` cannot find a FASTA or cannot write output.
- Variant DMS mutations fail wild-type checks.
- IF1 structure parsing reports no chain or missing chain.

Responses:

1. Route MSA Transformer embeddings through Python `MSABatchConverter`, not `esm-extract`.
2. Ensure FASTA record labels are unique and filesystem-safe before bulk extraction or folding.
3. Use bundled helper scripts in sub-skills to validate paths and print commands before running model inference.
4. For DMS, align mutation numbering with `--offset-idx`; a mutation `A24D` maps to sequence index `0` when `offset_idx=24`.
5. For PDB/mmCIF files, inspect chain IDs and backbone atom completeness before IF1 sampling/scoring.

## When To Stop and Ask

Ask for user confirmation before:

- Downloading large model weights when network policy is unclear.
- Installing or changing CUDA/OpenFold/PyTorch Geometric dependencies in a user-provided environment.
- Running GPU-heavy or long CPU inference on large FASTA/DMS/structure inputs.
- Overwriting existing prediction, embedding, PDB, or DMS output directories/files.
