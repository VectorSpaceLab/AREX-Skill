# Inverse-Folding Troubleshooting

ESM-IF1 failures usually fall into five groups: optional dependency mismatches, model-download/runtime constraints, structure parsing, scoring input mismatch, and sampled sequence quality.

## Quick Triage

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: torch_geometric` or GVP import failures | Inverse-folding optional dependency missing. | Install a PyTorch-compatible `torch-geometric`/`pyg` stack before loading ESM-IF1. Prefer a fresh environment for CUDA compatibility. |
| `filter_backbone` import or behavior error | Incompatible `biotite` API version. | Use a `biotite` version compatible with the ESM code path that imports `biotite.structure.filter_backbone`. |
| First model load hangs or fails with network error | Weight download through torch hub is blocked or slow. | Pre-place weights and use `load_model_and_alphabet_local(...)`, or run in an environment with approved network/cache access. |
| CUDA OOM | Model or batch is too large for the GPU. | Use CPU, reduce concurrent jobs, score fewer sequences at once, or free GPU memory. |
| CPU run is very slow | ESM-IF1 inference is compute-heavy. | Use GPU when available, reduce sample count, lower workload during validation, and rely on dry-run checks before full execution. |
| `No chains found in the input file.` | Structure parser found no backbone-filtered chains. | Confirm suffix, file integrity, model records, and N/CA/C backbone atom names. |
| `Chain C not found in input file` | Requested chain ID does not match parsed chain IDs. | Inspect actual chain IDs, especially for mmCIF files, then rerun with the parsed ID. |
| `structure has multiple atoms with same name` | Duplicate atom records within a residue after filtering. | Clean alternate locations or choose a deterministic conformer before extraction. |
| NaN/inf-heavy coordinates | Missing backbone atoms or intentional masking. | Check residue coverage; use `ll_withcoord` for scoring comparisons; avoid scoring if all target residues are missing coordinates. |
| Sequence length mismatch during scoring | FASTA target sequence length differs from target-chain coordinates. | Align FASTA records to the exact target chain length or choose the correct chain. |
| High-repeat sampled sequences | Sampling failure mode, often temperature/task dependent. | Filter long homopolymer runs, try lower temperature such as `1e-6`, and compare single-chain vs multichain conditioning. |
| Output write error | Parent directory absent or not writable. | Use an explicit writable `--outpath`; create parents before execution. |

## Dependency Problems

### Missing `torch-geometric`

Inverse folding uses GVP layers that depend on the PyTorch Geometric stack. A plain ESM install can import `esm` but still fail when loading the inverse-folding model.

Check:

```bash
python - <<'PY'
import torch
import esm
import esm.inverse_folding
print(torch.__version__)
print("inverse folding imports ok")
PY
```

If import succeeds but model load fails, the missing dependency may be triggered only when the GVP modules are constructed. Install a PyTorch/CUDA-compatible `pyg` build rather than mixing arbitrary wheel versions.

### `biotite` Compatibility

The coordinate loader imports and uses `biotite.structure.filter_backbone`, `get_chains`, and residue conversion utilities. If these names moved or changed behavior in the installed `biotite`, structure loading can fail even when `esm.inverse_folding.util` imports.

Mitigation:

- Pin `biotite` to a version compatible with the ESM 2.0.1 inverse-folding code.
- Run a small `load_structure` check on a local `.pdb` or `.cif` before model loading.
- Treat parser failures separately from model failures.

## Structure And Chain Problems

### PDB/mmCIF Suffix

`load_structure` selects the parser by checking whether the path ends with `cif` or `pdb`. Use paths ending in `.cif` or `.pdb`. Rename compressed or extensionless files after decompression.

### No Chains Found

If no chains are found after backbone filtering:

1. Verify the file has atom records, not only metadata.
2. Confirm it contains protein backbone atoms named `N`, `CA`, and `C`.
3. Confirm the first model contains the intended chains.
4. Try a known-good PDB/mmCIF parser to list chains before running ESM-IF1.

### Chain Not Found

For a requested target chain:

1. List parsed chain IDs.
2. Use the exact parsed string for `--chain` or `target_chain_id`.
3. For mmCIF files, verify whether the parser exposes author chain IDs or internal asym IDs.
4. In multichain mode, confirm the target chain is present in the `coords` dictionary before calling `sample_sequence_in_complex` or `score_sequence_in_complex`.

## Missing Coordinates

`get_atom_coords_residuewise(["N", "CA", "C"], structure)` sets missing atom coordinates to `nan`. Manual masks often use `inf`. Both are non-finite and treated as absent by finite-coordinate masks.

Diagnosis:

```python
import numpy as np
finite_residue_mask = np.all(np.isfinite(coords), axis=(-1, -2))
print(finite_residue_mask.sum(), "residues with full N/CA/C coordinates")
```

Fixes:

- Repair or choose a structure with better backbone coverage.
- Compare `ll_withcoord` rather than `ll_fullseq` when missing residues are expected.
- Avoid interpreting scores when no residues have complete coordinates.

## Scoring Problems

### Sequence Length Mismatch

`score_sequence` expects the target sequence to correspond to the target coordinate length. If FASTA length differs:

1. Confirm that the FASTA sequence is for the same chain, not the full complex.
2. Remove tags, signal peptides, unresolved insertions, or alignment gaps unless they exist in the coordinate tensor.
3. Decide whether missing structural residues should be masked in coordinates or removed from the scored sequence; keep the convention consistent across variants.

### FASTA Header And CSV Issues

The source-compatible scoring output writes comma-separated rows without CSV quoting. Avoid commas and newlines in FASTA headers if the output will be read as simple CSV.

## Sampling Problems

### High Repeated Amino Acids

Long repeats such as `EEEEEEEE` are a known sampled-sequence failure mode. Diagnose and mitigate:

1. Compute the longest homopolymer run per sampled sequence.
2. Filter sequences above a chosen threshold, such as 8 repeated residues.
3. Re-sample with lower temperature when native recovery is more important than diversity.
4. Try both single-chain and multichain modes; multichain context can help some complexes but is not universally better.

### Unexpected Diversity Or Low Recovery

Temperature controls sampling sharpness:

- Higher temperature increases diversity and can reduce native-like recovery.
- Lower temperature such as `1e-6` makes sampling more deterministic and is recommended when optimizing native sequence recovery.

## Runtime And Resource Problems

### Model Download

`esm.pretrained.esm_if1_gvp4_t16_142M_UR50()` typically downloads weights through torch hub on first use. For offline or controlled environments:

- Use a pre-populated torch hub cache approved by the user.
- Use `load_model_and_alphabet_local(model_location)` with a local checkpoint.
- Validate imports and command construction without model loading when downloads are not allowed.

### GPU/CPU Choice

The original example scripts move the model to GPU when CUDA is available unless `--nogpu` is set. In constrained environments:

- Use `--nogpu` or CPU API execution for correctness smoke tests.
- Use GPU for full scoring/sampling batches when compatible.
- Reduce `--num-samples` during debugging.

## Safe Validation Before Long Runs

Use the helper dry-run mode first:

```bash
python scripts/inverse_folding_cli_helper.py score complex.cif variants.fasta \
  --chain C --outpath output/chain_c_scores.csv --multichain-backbone
```

Then execute only after the dry-run command, structure file, FASTA file, output path, dependencies, and model-weight access are confirmed:

```bash
python scripts/inverse_folding_cli_helper.py score complex.cif variants.fasta \
  --chain C --outpath output/chain_c_scores.csv --multichain-backbone --execute
```
