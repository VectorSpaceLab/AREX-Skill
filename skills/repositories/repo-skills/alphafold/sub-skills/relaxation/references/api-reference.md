# Relaxation API Reference

This reference summarizes the AlphaFold 2.3.2 relaxation APIs needed for safe agent guidance. The APIs can run expensive OpenMM minimization; inspect and plan first, and run only when the user explicitly wants relaxation.

## Public Entry Point: `AmberRelaxation`

```python
from alphafold.relax import relax

relaxer = relax.AmberRelaxation(
    max_iterations=0,
    tolerance=2.39,
    stiffness=10.0,
    exclude_residues=[],
    max_outer_iterations=3,
    use_gpu=False,
)
min_pdb, debug_data, violations = relaxer.process(prot=protein_instance)
```

### Constructor

```python
AmberRelaxation.__init__(
    *,
    max_iterations: int,
    tolerance: float,
    stiffness: float,
    exclude_residues: Sequence[int],
    max_outer_iterations: int,
    use_gpu: bool,
)
```

| Argument | Meaning | Practical guidance |
| --- | --- | --- |
| `max_iterations` | Maximum L-BFGS minimization iterations; `0` means no explicit maximum. | The public CLI uses `0`; set a finite value only for bounded experiments. |
| `tolerance` | L-BFGS energy/force tolerance converted to OpenMM units. | The public CLI uses `2.39`. |
| `stiffness` | Heavy-atom restraint spring constant in `kcal/mol/A**2`. | The public CLI uses `10.0`; larger values keep minimized coordinates closer to the prediction. |
| `exclude_residues` | Zero-indexed residues excluded from restraints. | Start empty unless targeting known violating residues. Iterative relaxation adds violating residues to this set. |
| `max_outer_iterations` | Maximum violation-informed relaxation iterations. | Public `run_alphafold` uses `3`; the relax docstring notes larger values such as `20` catch more hard cases but can cost more. |
| `use_gpu` | Selects OpenMM `CUDA` platform when true and `CPU` platform when false. | Use CPU for stability triage; use GPU only when OpenMM CUDA is known to work. |

### `process(prot)`

```python
AmberRelaxation.process(
    *, prot: alphafold.common.protein.Protein
) -> tuple[str, dict[str, object], Sequence[float]]
```

Input is an AlphaFold `Protein` object, usually created by `protein.from_prediction()` or `protein.from_pdb_string()`. The method returns:

| Return value | Meaning |
| --- | --- |
| `min_pdb` | Minimized PDB string with B-factors overwritten from the original `Protein.b_factors`. |
| `debug_data` | Dict with `initial_energy`, `final_energy`, `attempts`, and coordinate `rmsd`. |
| `violations` | Per-residue total violation mask from `structural_violations['total_per_residue_violations_mask']`, converted to a Python list. |

Important postconditions:

- Nonterminal atom types in the relaxed PDB are checked against the original atom mask, ignoring possible terminal `OXT` additions.
- B-factors continue to carry original confidence-style values; relaxation does not recompute pLDDT or PAE.
- Remaining violations are a stereochemical signal, not a model confidence replacement.

## Lower-Level Pipeline: `amber_minimize.run_pipeline`

```python
from alphafold.relax import amber_minimize

out = amber_minimize.run_pipeline(
    prot=protein_instance,
    stiffness=10.0,
    use_gpu=False,
    max_outer_iterations=3,
    place_hydrogens_every_iteration=True,
    max_iterations=0,
    tolerance=2.39,
    restraint_set="non_hydrogen",
    max_attempts=100,
    checks=True,
    exclude_residues=None,
)
```

### Parameters

| Parameter | Meaning | Notes |
| --- | --- | --- |
| `prot` | `alphafold.common.protein.Protein` to relax. | Must contain at least one atom for every residue. |
| `stiffness` | Restraint stiffness in `kcal/mol/A**2`. | Set `0` for no restraint, but AlphaFold's wrapper uses restrained relaxation. |
| `use_gpu` | Select OpenMM `CUDA` or `CPU` platform. | CUDA can be faster but is the common platform-failure source. |
| `max_outer_iterations` | Number of violation-informed relax rounds. | Loop stops early once violations are zero. |
| `place_hydrogens_every_iteration` | Re-run cleanup/hydrogen placement before each iteration. | Default true. |
| `max_iterations` | L-BFGS iteration cap; `0` means unlimited. | Passed to `Simulation.minimizeEnergy`. |
| `tolerance` | L-BFGS tolerance. | Converted to OpenMM energy/length units. |
| `restraint_set` | Which atoms receive harmonic restraints. | Supported internal values are `non_hydrogen` and `c_alpha`. |
| `max_attempts` | Attempts per minimization iteration before raising. | Repeated OpenMM failures end with `Minimization failed after ... attempts.` |
| `checks` | Enable cleaning coordinate consistency checks. | Disable only for controlled debugging. |
| `exclude_residues` | Initial zero-indexed residues excluded from restraints. | Iterative relaxation unions this with current violating residues. |

### Output dictionary

Common keys in the result include:

| Key | Meaning |
| --- | --- |
| `einit`, `efinal` | Potential energy before and after the successful minimization attempt. |
| `posinit`, `pos` | Initial and minimized positions as arrays in Angstrom units. |
| `min_pdb` | Minimized PDB string. |
| `opt_time` | Wall time spent in the minimization attempt loop. |
| `min_attempts` | Number of attempts needed for the final successful iteration. |
| `violations_per_residue` | Aggregate per-residue violation metric. |
| `residue_violations` | Zero-indexed residue positions with total structural violations. |
| `num_residue_violations` | Count of violating residues in the current iteration result. |
| `structural_violations` | Nested structural violation masks and losses from the model folding code. |
| `num_exclusions`, `iteration` | Iterative relaxation bookkeeping. |

## Cleanup APIs

### `clean_protein(prot, checks=True)`

Performs the preparation before minimization:

1. Checks the atom mask is ideal, allowing only terminal `OXT` differences.
2. Converts the `Protein` to PDB text.
3. Uses PDBFixer to replace nonstandard residues, remove heterogens and water, fill missing residues/atoms, and add hydrogens.
4. Applies AlphaFold cleanup helpers for edge cases.
5. Writes an OpenMM PDB string and optionally checks that coordinates of atoms that survived cleanup were not altered during cleaning.

The pipeline checks for residues with no atoms before cleanup because converting a `Protein` to PDB can strip poorly defined residues.

### `cleanup.fix_pdb(pdbfile, alterations_info)`

Uses PDBFixer and records alteration details:

| Alteration key | Meaning |
| --- | --- |
| `nonstandard_residues` | Nonstandard residues replaced with standard equivalents. |
| `removed_heterogens` | Heterogens removed, including water in AlphaFold's relax path. |
| `missing_residues` | Missing residues detected and filled. |
| `missing_heavy_atoms` | Heavy atoms added within existing residues. |
| `missing_terminals` | Terminal atoms such as `OXT` added. |

### `cleanup.clean_structure(pdb_structure, alterations_info)`

Applies additional AlphaFold fixes:

- Replace selenium in unmodified MET `SD` atoms with sulfur.
- Remove chains of length one because a single amino-acid chain is both N and C terminus and has no force-field template in this path.

## Structural Violation Metrics

### `find_violations(prot)` and `get_violation_metrics(prot)`

`find_violations()` converts an AlphaFold `Protein` into atom14 tensors and calls the model folding violation code with:

- `violation_tolerance_factor = 12`
- `clash_overlap_tolerance = 1.5`

`get_violation_metrics()` adds:

- `residue_violations`: zero-indexed residues where `total_per_residue_violations_mask` is true.
- `num_residue_violations`: count of those residues.
- `structural_violations`: the nested raw violation data.

During `run_pipeline`, violation calculation is forced onto the local JAX CPU device because some JAX/CUDA combinations can fail while computing violations.

## Utility APIs

### `utils.overwrite_b_factors(pdb_str, bfactors)`

Rewrites the B-factor column in a PDB string using the `CA` B-factor value for each residue from a `[num_res, 37]`-style array. It raises if the final dimension is not the AlphaFold atom-type count.

### `utils.assert_equal_nonterminal_atom_types(atom_mask, ref_atom_mask)`

Compares atom masks while ignoring terminal `OXT`. This is why a final `OXT` addition is not treated as a relaxation failure.
