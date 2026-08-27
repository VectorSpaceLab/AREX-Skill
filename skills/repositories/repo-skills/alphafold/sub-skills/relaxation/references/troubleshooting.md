# Relaxation Troubleshooting

Use this guide for failures in AlphaFold's Amber/OpenMM relaxation and PDB cleanup path. For command construction, output interpretation, or broad dependency repair, follow the routing boundaries in `SKILL.md`.

## Fast Diagnosis Table

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `No module named 'openmm'` or OpenMM import failure | OpenMM is not installed in the runtime environment. | Install a compatible OpenMM package for the user's platform, or run prediction with `--models_to_relax=none` until the environment is fixed. |
| `No module named 'pdbfixer'` or PDBFixer import failure | PDBFixer is missing; cleanup cannot add atoms/hydrogens. | Install PDBFixer from a compatible channel/source, or skip relaxation. |
| OpenMM `CUDA` platform not found | `use_gpu=True` but CUDA OpenMM plugins are unavailable. | Set `--use_gpu_relax=false` or `use_gpu=False` to use CPU relaxation. |
| CUDA driver/runtime/plugin error during relaxation | OpenMM CUDA stack mismatch or unstable GPU minimization. | Retry on CPU; keep GPU model inference diagnosis separate from OpenMM relaxation. |
| `Amber minimization can only be performed on proteins with well-defined residues` | At least one residue has zero atoms in `Protein.atom_mask`. | Skip relaxation or regenerate/clean the `Protein` so every residue has atoms before calling relax. |
| Atom-mask assertion failure before or after cleanup | Input atom set is not AlphaFold-ideal, beyond terminal `OXT` differences. | Use an AlphaFold-generated structure or repair the input; do not expect arbitrary PDB atom sets to pass. |
| `Minimization failed after ... attempts` | Repeated OpenMM minimization exceptions for the cleaned structure/platform. | Try CPU, reduce selected models, inspect PDB content, or skip relaxation; preserve the unrelaxed output for analysis. |
| Relaxation removes ligands, water, or short chains | PDBFixer/cleanup removes heterogens and chains of length one in AlphaFold's path. | Do not use this relax path to preserve ligand/cofactor/water geometry; handle those structures outside AlphaFold relaxation. |
| No `relax_metrics.json` | `models_to_relax=none` selected no models. | Expected behavior; use `../prediction-cli/` for top-level flag choice and `../outputs-and-confidence/` for output inspection. |
| Remaining violations after relaxation | Iterative relaxation hit its limit or hard geometry remains. | Report remaining residues; consider more outer iterations only if the user accepts extra runtime and backend risk. |

## OpenMM Platform Failures

AlphaFold's minimizer explicitly requests an OpenMM platform by name:

- `CUDA` when `use_gpu=True`.
- `CPU` when `use_gpu=False`.

For CUDA failures, a safe first repair is not a package reinstall; it is to rerun relaxation on CPU:

```bash
run_alphafold \
  ... \
  --models_to_relax=best \
  --use_gpu_relax=false
```

Use this explanation:

- The change affects only Amber/OpenMM relaxation, not the semantics of pLDDT/PAE.
- CPU relaxation is typically slower but avoids CUDA platform/plugin failures.
- If the error is malformed protein content, CPU will fail too.
- If prediction already completed and unrelaxed files exist, route output triage to `../outputs-and-confidence/` before deciding whether a rerun is worth it.

## Missing PDBFixer

`alphafold.relax.cleanup.fix_pdb()` imports and uses PDBFixer. Without it, relaxation cannot perform AlphaFold's cleanup sequence:

1. Replace nonstandard residues.
2. Remove heterogens and water.
3. Find and add missing residues and heavy atoms.
4. Add missing hydrogens.
5. Write a cleaned OpenMM PDB while preserving IDs where possible.

If PDBFixer is unavailable, either install it in the user runtime or set `--models_to_relax=none`. Do not claim the API can relax normally without PDBFixer.

## Poorly Defined Residues With No Atoms

The lower-level pipeline checks:

```text
prot.atom_mask.sum(axis=-1) == 0
```

If any residue is empty, relaxation raises before cleanup. This usually happens when a `Protein` object was built from malformed data or when residue metadata survived but all atom positions/masks were absent.

Recommended answer for this case:

- If the user only needs model ranking, confidence, or downstream coarse inspection, skip relaxation and keep unrelaxed outputs.
- If a relaxed PDB is mandatory, reconstruct the `Protein` from a valid PDB/mmCIF or regenerate the prediction so every residue has atoms.
- Do not recommend `exclude_residues` as the fix for a zero-atom residue; the well-defined residue check runs before restraint exclusions matter.

## Atom Mask Is Not Ideal

`clean_protein()` checks that the atom mask matches AlphaFold's ideal residue atom mask, except for possible terminal `OXT`. Failure means the input is not shaped like an AlphaFold protein representation.

Common causes:

- Arbitrary PDB files with missing backbone atoms.
- Structures containing unsupported residue or atom naming conventions.
- Manual edits to `Protein.atom_mask` or residue types.
- Ligand/cofactor-heavy structures routed through the protein-only relax path.

Use `scripts/check_relaxation_inputs.py` to identify obvious text-level gaps, then advise regenerating or repairing the input rather than forcing minimization.

## Cleanup Changes That Surprise Users

PDBFixer and AlphaFold cleanup intentionally modify the structure before minimization:

| Cleanup behavior | Consequence |
| --- | --- |
| Replaces nonstandard residues | Input residue names can change to standard amino acids. |
| Removes heterogens and water | Ligands, cofactors, ions, and waters are not preserved by this path. |
| Adds missing residues and atoms | The relaxed PDB may contain atoms not present in the input. |
| Adds hydrogens | Atom count increases before minimization. |
| Replaces selenium in unmodified MET | `Se` in MET `SD` is converted to sulfur. |
| Removes single-residue chains | Very short chains can disappear because the force-field template path cannot handle them. |

If preserving non-protein context matters, AlphaFold's bundled relaxation is usually the wrong tool.

## Repeated Minimization Failure

`_run_one_iteration()` catches broad OpenMM exceptions and retries until `max_attempts`. If every attempt fails, it raises:

```text
Minimization failed after <N> attempts.
```

Triage order:

1. Switch GPU relaxation to CPU if `use_gpu=True`.
2. Run the bundled input checker for no ATOM records, short chains, heterogens, and missing backbone atoms.
3. Confirm PDBFixer and OpenMM imports are available.
4. Reduce scope from `models_to_relax=all` to `best`, or skip with `none` if prediction artifacts are sufficient.
5. Only tune API parameters such as `max_attempts`, `max_iterations`, `stiffness`, or `max_outer_iterations` when the user intentionally wants a relaxation experiment.

## GPU Relaxation Is Unstable

Symptoms include CUDA illegal memory access, plugin errors, nondeterministic minimization failures, or relaxation failing while the rest of prediction succeeds. Use CPU relaxation as the conservative fallback and communicate expected slowdown.

Suggested wording:

```text
The prediction outputs can still be useful. Switch only relaxation to CPU with --use_gpu_relax=false, keep --models_to_relax=best unless every ranked model must be relaxed, and expect the relaxation stage to take longer.
```

## `models_to_relax=none` Tradeoff

Skipping relaxation is not a silent correctness failure. It means:

- `unrelaxed_<model>.pdb` and ranked files based on unrelaxed structures may still be written.
- `relaxed_<model>.pdb`, `relaxed_<model>.cif`, and `relax_metrics.json` are not expected.
- Structures can retain stereochemical clashes or distracting violations.
- Confidence metrics such as pLDDT and PAE remain available when the model produced them.

Use this option when the user values successful prediction artifacts more than Amber cleanup, or when backend repair is outside the current task.

## Synthetic Hard Cases For Review

1. A user reports the exact well-defined-residue error after constructing a `Protein` object with one residue whose atom mask is all zeros. Expected guidance: identify the pre-cleanup check, reject `exclude_residues` as a fix, and recommend skipping relaxation or reconstructing the input.
2. A GPU relaxation run fails with OpenMM CUDA platform errors after writing unrelaxed models. Expected guidance: switch to `--use_gpu_relax=false`, preserve `--models_to_relax=best` unless all models are required, warn about slowdown, and route existing output confidence interpretation to `../outputs-and-confidence/`.
