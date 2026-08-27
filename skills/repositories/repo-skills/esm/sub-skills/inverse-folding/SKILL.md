---
name: inverse-folding
description: "Use ESM-IF1 for fixed-backbone protein inverse design, sequence
  log-likelihood scoring, multichain conditioning, coordinate extraction, and
  structure encoder representations."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Inverse Folding

Use this sub-skill when a task needs ESM-IF1 to design or score protein sequences from known backbone coordinates. It covers fixed-backbone sequence sampling, single-chain and multichain complex conditioning, PDB/mmCIF coordinate extraction, missing-coordinate handling, conditional log-likelihood scoring, and encoder representations.

## When To Use

- Sample candidate amino-acid sequences for a PDB or mmCIF backbone with `esm.pretrained.esm_if1_gvp4_t16_142M_UR50()` and `model.sample(...)`.
- Score one or more sequences against a structure with `score_sequence(...)` or `score_sequence_in_complex(...)`.
- Condition target-chain design on all chains in a complex with `--multichain-backbone` or `multichain_util` APIs.
- Extract N/CA/C backbone coordinates and native sequences from PDB/mmCIF files.
- Obtain structure-conditioned encoder representations from ESM-IF1.

## Route Elsewhere

- Use the sibling [`structure-prediction`](../structure-prediction/SKILL.md) sub-skill for ESMFold forward folding from sequence to structure.
- Use the sibling [`model-embeddings`](../model-embeddings/SKILL.md) sub-skill for generic protein language-model embeddings that do not use backbone coordinates.
- Use the sibling [`variant-effect-prediction`](../variant-effect-prediction/SKILL.md) sub-skill for mutation scoring without a structure-conditioned inverse-folding model.

## Start Here

1. Confirm the environment has PyTorch plus inverse-folding optional dependencies, especially `torch-geometric` and a compatible `biotite` API.
2. Validate the structure suffix is `.pdb` or `.cif`, choose the target chain ID, and decide whether to condition on only the target chain or the whole complex.
3. For CLI-style work, use the bundled dry-run helper in `scripts/inverse_folding_cli_helper.py` to construct safe commands before running downloads or GPU jobs.
4. For API work, load `model, alphabet = esm.pretrained.esm_if1_gvp4_t16_142M_UR50()` and call `model.eval()` before sampling or scoring.
5. Inspect sampled FASTA output for long amino-acid repeats and inspect scoring CSV output for sequence length mismatches or missing-coordinate effects.

## References

- `references/workflows.md` gives task recipes for sampling, scoring, multichain conditioning, encoder outputs, and diagnostic workflows.
- `references/api-reference.md` lists the supported ESM-IF1 loader and inverse-folding APIs.
- `references/data-formats.md` describes coordinate tensors, PDB/mmCIF requirements, FASTA input/output, CSV scoring output, and missing-coordinate conventions.
- `references/troubleshooting.md` maps common dependency, data, runtime, and biological-quality failures to fixes.

## Bundled Helper

Use `scripts/inverse_folding_cli_helper.py` for self-contained command construction and input validation:

```bash
python scripts/inverse_folding_cli_helper.py sample structure.pdb --chain C --outpath designs.fasta
python scripts/inverse_folding_cli_helper.py score structure.pdb variants.fasta --chain C --outpath scores.csv --multichain-backbone
```

The helper prints a dry-run command by default. Add `--execute` only when the environment is ready for model loading, potential torch hub downloads, and a long CPU/GPU run.
