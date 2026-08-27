---
name: linear-rna
description: "Use PaddleHelix LinearRNA for LinearFold and LinearPartition RNA
  secondary-structure analysis, including extension build/import troubleshooting
  and safe input validation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# LinearRNA

Use this sub-skill when a task mentions LinearRNA, LinearFold, LinearPartition, RNA secondary structure, RNA folding constraints, a missing `linear_rna` extension, or base-pair probability cutoffs.

## Route

- Use `references/api-reference.md` for `linear_fold_c`, `linear_fold_v`, `linear_partition_c`, `linear_partition_v`, beam size, `bp_cutoff`, constraints, return shapes, and small examples.
- Use `scripts/check_linear_rna.py` before running user-supplied inputs; it validates RNA letters, constraint length and parentheses, canonical/wobble constrained pairs, `beam_size`, `bp_cutoff`, and extension importability.
- Use `references/build-and-troubleshooting.md` when `pahelix.toolkit.linear_rna`, `c.pahelix.toolkit.linear_rna.linear_rna`, or a direct build-tree `linear_rna` module is missing, CMake fails, pybind11 is absent, Ninja/compiler tools are unavailable, or the deprecated `sklearn` dependency blocks installation.
- Route protein, compound, docking, molecular generation, and broad PaddleHelix model workflows to the sibling sub-skill that owns that domain.

## Safe Workflow

1. Normalize the requested RNA sequence to uppercase RNA semantics; `T` is accepted as `U`, but ambiguous bases are not part of the documented LinearRNA API.
2. For LinearFold constraints, require `use_constraints=True`, a constraint string with the same length as the sequence, only `?`, `.`, `(`, `)`, balanced non-crossing parentheses, and constrained pairs compatible with AU, UA, CG, GC, GU, or UG.
3. For LinearPartition, choose a `bp_cutoff` between `0.0` and `1.0`; use a positive cutoff for exploratory checks to keep the pair list small.
4. If the extension imports, run toy or user-approved inputs through `scripts/check_linear_rna.py`; use `--model c` for learned-parameter APIs and `--model v` for thermodynamic APIs. If import fails, diagnose the build route before attempting API calls.

## Bundled Entry Points

```bash
python sub-skills/linear-rna/scripts/check_linear_rna.py --sequence GGGAAACCC --model c
python sub-skills/linear-rna/scripts/check_linear_rna.py --sequence GGGAAACCC --model v
python sub-skills/linear-rna/scripts/check_linear_rna.py --sequence UGAGUUCUCGAUCUCUAAAAUCG --partition --bp-cutoff 0.2 --model c
python sub-skills/linear-rna/scripts/check_linear_rna.py --sequence UGAGUUCUCGAUCUCUAAAAUCG --partition --bp-cutoff 0.2 --model v
python sub-skills/linear-rna/scripts/check_linear_rna.py --sequence GAAAC --constraint '(...)'
```

The script prints JSON on success and clear validation/import errors on failure. It does not download data, build the extension, mutate a checkout, or run large benchmark datasets.

## Evidence Labels

This sub-skill distills the LinearRNA README, tutorial notebook examples, C++ pybind signatures, package build metadata, developer build notes, and environment-preparation caveats into self-contained references and a safe checker.
