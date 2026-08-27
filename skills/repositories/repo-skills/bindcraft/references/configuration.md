# BindCraft configuration map

BindCraft reads three JSON objects. Keep them separate and version them with
campaign outputs. The checked-in presets are templates, not universal defaults
for every target.

## Target settings

The target object has seven required keys:

| Key | Meaning | Validation |
|---|---|---|
| `design_path` | Writable output root for CSVs and design folders | Use a distinct directory per campaign |
| `binder_name` | Filename prefix for generated binders | Non-empty label; no path separators |
| `starting_pdb` | Input target PDB | Must be readable by the launcher |
| `chains` | Comma-separated target chains | Match PDB chain IDs; do not include a designed binder chain |
| `target_hotspot_residues` | `null`/empty for AF2 selection or explicit residue/range syntax | Check chain-qualified ranges against the PDB |
| `lengths` | Two-element inclusive binder length range | Positive integers, minimum no greater than maximum |
| `number_of_final_designs` | Stop target for accepted binders | Positive integer; difficult targets may require many trajectories |

Use the target route and its validator before launch. Replace all example paths
with host-valid paths; do not copy notebook or checkout paths.

## Advanced settings

Advanced JSON controls model choice and runtime behavior. Group changes by
purpose: design algorithm and iterations; AF2 model/recycles/template masking;
loss weights and contact geometry; MPNN model, temperature and sequence count;
acceptance/max-trajectory monitoring; and storage cleanup. The available
families are documented in the focused advanced-settings reference:
`4stage` is the extensive default family, `3stage` is a common peptide
alternative, and `2stage`, `greedy`, and `mcmc` trade memory, speed, or search
behavior differently.

Paths commonly carried in advanced settings are `af_params_dir`, `dssp_path`,
and `dalphaball_path`. Empty values are filled by BindCraft's path helper, but
verify the result on the actual installation. Do not rely on the source
checkout staying present after skill construction.

## Filter settings

Filter JSON maps metric names to `{threshold, higher}` conditions. A `null`
threshold disables that condition. `higher: true` retains values at or above
the threshold; `higher: false` retains values at or below it. The repository
supports broad AF2, MPNN, interface, Rosetta, secondary-structure, clash, RMSD,
and binder-alone metrics, including `Average_` and per-model variants.

Use the no-filter preset only for deliberate diagnostics; it is not evidence
that generated structures are acceptable. Choose filter families consistent
with binder length and target context, and record the exact filter file with
results.

## Compatibility checks

Before a long run, validate that:

- target chains and hotspot syntax match the PDB;
- all three JSON files parse and have the expected top-level object shape;
- the AF2 parameter directory and external executable paths are readable;
- the selected advanced preset's `use_multimer_design`, model counts, recycles,
  MPNN settings, and storage options fit available memory/disk;
- `design_path` is writable and is not shared by another process.

Use `scripts/validate_bindcraft_config.py` for schema-level checks, then use the
focused target validator for PDB-aware checks.
