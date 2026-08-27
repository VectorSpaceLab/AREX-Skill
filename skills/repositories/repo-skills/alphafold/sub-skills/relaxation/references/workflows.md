# Relaxation Workflows

Use these workflows to decide how to plan, inspect, or troubleshoot AlphaFold relaxation without launching expensive OpenMM minimization by default.

## Decide Whether To Relax

| Situation | Recommendation | Rationale |
| --- | --- | --- |
| Normal local prediction and OpenMM is known to work | Keep the CLI default `--models_to_relax=best`. | Only the top-ranked model is relaxed, limiting cost while producing a cleaned final structure. |
| Need every ranked model to have relaxed coordinates | Use `--models_to_relax=all` only after the user accepts extra runtime. | Relaxation is performed once per selected model and can dominate postprocessing time. |
| OpenMM/PDBFixer/CUDA is failing | Use `--models_to_relax=none` for the prediction rerun or rerun only postprocessing after fixing the backend. | Skipping relaxation preserves unrelaxed predictions and avoids blocking the full run on Amber minimization. |
| Early exploratory run or command validation | Prefer `--models_to_relax=none`. | Data pipeline and model issues can be debugged before adding relaxation complexity. |
| User cares about local stereochemical cleanup for a selected structure | Relax the best model or run the API on the selected `Protein`. | Relaxation reduces distracting clashes/violations but does not improve confidence metrics. |

Top-level `--models_to_relax` command construction belongs to `../prediction-cli/`. Use this file to explain what the choice means internally and how to troubleshoot backend behavior.

## CLI Relaxation Flow

The public `run_alphafold` workflow creates one `AmberRelaxation` object with constants equivalent to:

```python
AmberRelaxation(
    max_iterations=0,
    tolerance=2.39,
    stiffness=10.0,
    exclude_residues=[],
    max_outer_iterations=3,
    use_gpu=FLAGS.use_gpu_relax,
)
```

After all model predictions are ranked:

1. `models_to_relax=best` selects only the first model from `ranking_debug.json` order.
2. `models_to_relax=all` selects every ranked model.
3. `models_to_relax=none` selects no models and does not write `relax_metrics.json`.
4. For each selected model, `amber_relaxer.process(prot=unrelaxed_protein)` returns a relaxed PDB string plus remaining per-residue violations.
5. The run writes `relaxed_<model>.pdb`, `relaxed_<model>.cif`, and updates ranked files so `ranked_<n>` uses the relaxed structure when available and the unrelaxed structure otherwise.
6. `relax_metrics.json` stores `remaining_violations` and `remaining_violations_count` per relaxed model.

Route interpretation of these files to `../outputs-and-confidence/`.

## Programmatic Relaxation Pattern

Use the API only when the user has a prepared `alphafold.common.protein.Protein` object and explicitly wants minimization:

```python
from alphafold.common import protein
from alphafold.relax import relax

prot = protein.from_pdb_string(pdb_text)
relaxer = relax.AmberRelaxation(
    max_iterations=0,
    tolerance=2.39,
    stiffness=10.0,
    exclude_residues=[],
    max_outer_iterations=3,
    use_gpu=False,
)
min_pdb, debug_data, violations = relaxer.process(prot=prot)
```

Checklist before suggesting this:

- The input is an AlphaFold-compatible protein structure, not an arbitrary ligand-heavy PDB complex.
- Every residue has at least one atom and the atom mask is close to AlphaFold's ideal mask.
- PDBFixer and OpenMM are installed in the user's runtime.
- If `use_gpu=True`, OpenMM CUDA platform is available and compatible with the GPU driver.
- The user accepts that relaxation can be slow and may still fail after repeated attempts.

## CPU Versus GPU Relaxation

| Choice | Use when | Tradeoff |
| --- | --- | --- |
| `use_gpu=False` / `--use_gpu_relax=false` | Debugging platform errors, GPU relaxation is unstable, no CUDA-capable OpenMM platform, or deterministic/stable postprocessing matters more than speed. | Usually slower, but avoids many CUDA platform and GPU nondeterminism failures. |
| `use_gpu=True` / `--use_gpu_relax=true` | OpenMM CUDA is already validated and the user wants faster relaxation. | Can fail if CUDA platform/plugins are missing, driver/runtime versions are incompatible, or GPU minimization is unstable. |

A practical repair for GPU relaxation failures is to leave model inference settings unchanged, set `--use_gpu_relax=false`, and keep `--models_to_relax=best` or `all` as needed. Warn that the relaxation stage may take longer on CPU.

## Safe Input Inspection

Before proposing minimization of a user-supplied PDB, run the bundled helper:

```bash
python scripts/check_relaxation_inputs.py prediction.pdb --check-imports
```

The helper checks the text-level PDB shape only. Treat warnings as triage signals, not as proof that OpenMM relaxation will succeed.

Important warning classes:

- No `ATOM` records: not a relaxable protein input.
- Residue entries without common backbone atoms such as `N`, `CA`, `C`, or `O`: likely to fail ideal atom-mask checks or require cleanup.
- Single-residue chains: AlphaFold cleanup removes these because force-field templates are not available for that path.
- `HETATM` records: PDBFixer removes heterogens and water in the relaxation path; ligand or cofactor coordinates will not be preserved by default.
- Import availability: missing OpenMM or PDBFixer blocks actual relaxation, even if the PDB text looks plausible.

## Handling Residues With No Atoms

A direct `amber_minimize.run_pipeline` failure containing:

```text
Amber minimization can only be performed on proteins with well-defined residues. This protein contains at least one residue with no atoms.
```

means the `Protein.atom_mask` has at least one residue whose atom-mask sum is zero. This is checked before PDB cleanup because `protein.to_pdb()` can silently strip such residues.

Recommended response:

1. Identify whether the no-atom residue comes from a malformed conversion, a chain break, or a manually constructed `Protein` object.
2. If the prediction itself is otherwise usable and the user only needs confidence/output inspection, skip relaxation and route output interpretation to `../outputs-and-confidence/`.
3. If relaxed coordinates are required, regenerate or clean the input so every residue has at least one valid atom before calling relaxation.
4. Do not claim PDBFixer will repair a zero-atom residue inside an AlphaFold `Protein`; the pre-cleanup check prevents that path.

## Converting GPU Relax To CPU Relax

When a command fails during relaxation with CUDA/OpenMM errors but prediction has otherwise succeeded, change only the relaxation backend flag:

```bash
run_alphafold \
  ... \
  --models_to_relax=best \
  --use_gpu_relax=false
```

Explain the expected outcome:

- Prediction still uses whatever model backend settings the original command used.
- Relaxation now asks OpenMM for the `CPU` platform instead of `CUDA`.
- The relaxation stage can be substantially slower, especially for long chains or `models_to_relax=all`.
- If the failure was due to malformed PDB/protein content rather than CUDA, switching to CPU will not fix it.

## Reading Remaining Violations

`AmberRelaxation.process()` returns `violations` as a per-residue list. In CLI output, each relaxed model gets:

```json
{
  "remaining_violations": [0.0, 1.0, 0.0],
  "remaining_violations_count": 1.0
}
```

Interpretation:

- `0` means no total structural violation was flagged for that residue.
- Nonzero entries indicate residues with remaining stereochemical issues after relaxation.
- The list length follows residue order in the relaxed `Protein` representation.
- These values do not replace pLDDT/PAE confidence metrics.
