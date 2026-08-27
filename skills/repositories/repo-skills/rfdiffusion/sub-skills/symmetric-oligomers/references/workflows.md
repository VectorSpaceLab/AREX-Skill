# Symmetric Oligomer Workflows

These templates are portable RFdiffusion command patterns. Replace `/path/to/run_inference.py`, `/path/to/models`, `/path/to/*.pdb`, and output prefixes with paths from the user's environment. Do not rely on an original source checkout being present.

## Choose The Symmetry And Total Length

RFdiffusion's `contigmap.contigs` length is the total oligomer length, not the per-chain length.

| Symmetry override | Chain count | Example per-chain length | Total contig |
| --- | ---: | ---: | --- |
| `C6` or `c6` | 6 | 80 | `'contigmap.contigs=[480-480]'` |
| `D2` or `d2` | 4 | 80 | `'contigmap.contigs=[320-320]'` |
| `tetrahedral` | 12 | 50 | `'contigmap.contigs=[600-600]'` |
| `octahedral` | 24 | 40 | `'contigmap.contigs=[960-960]'` |
| `icosahedral` | 60 | 20 | `'contigmap.contigs=[1200-1200]'` |

For `C<n>`, multiply the per-chain length by `n`. For `D<n>`, multiply by `2*n`. For saved point groups, use the rotation counts above. Exact total lengths such as `'contigmap.contigs=[360-360]'` are safest. If using a range, ensure the sampler cannot choose incompatible totals or narrow the range to known compatible values.

## Minimal Symmetric Smoke Check

Use this before a large batch or after moving an installation. It keeps the run short, deterministic, and low-output.

```bash
python /path/to/run_inference.py \
  --config-name=symmetry \
  inference.symmetry="C3" \
  'contigmap.contigs=[180-180]' \
  inference.output_prefix=outputs/symmetry_smoke/C3_design \
  inference.num_designs=1 \
  inference.deterministic=True \
  inference.final_step=48 \
  inference.cautious=True \
  inference.write_trajectory=False
```

Expected outputs include `outputs/symmetry_smoke/C3_design_0.pdb` and `outputs/symmetry_smoke/C3_design_0.trb`. If cautious mode skips the design, choose a fresh prefix or set `inference.design_startnum=-1` intentionally.

## Cyclic Oligomer With Contact Potential

This mirrors the repository's C6 example while using portable paths.

```bash
python /path/to/run_inference.py \
  --config-name=symmetry \
  inference.symmetry="C6" \
  inference.num_designs=10 \
  inference.output_prefix=outputs/C6_oligo/design \
  'potentials.guiding_potentials=["type:olig_contacts,weight_intra:1,weight_inter:0.1"]' \
  potentials.olig_intra_all=True \
  potentials.olig_inter_all=True \
  potentials.guide_scale=2.0 \
  potentials.guide_decay="quadratic" \
  'contigmap.contigs=[480-480]'
```

This requests six 80-residue chains. The potential encourages both intra-chain and inter-chain contacts, with intra-chain contacts weighted more strongly.

## Dihedral Oligomer With Contact Potential

`D2` produces four chains because dihedral order doubles the numeric order.

```bash
python /path/to/run_inference.py \
  --config-name=symmetry \
  inference.symmetry="D2" \
  inference.num_designs=10 \
  inference.output_prefix=outputs/D2_oligo/design \
  'potentials.guiding_potentials=["type:olig_contacts,weight_intra:1,weight_inter:0.1"]' \
  potentials.olig_intra_all=True \
  potentials.olig_inter_all=True \
  potentials.guide_scale=2.0 \
  potentials.guide_decay="quadratic" \
  'contigmap.contigs=[320-320]'
```

Use the same divisibility check for higher orders: `D5` has ten chains, so a 70-residue chain requires total length `700-700`.

## Tetrahedral Oligomer

The named `tetrahedral` symmetry uses the saved 12-rotation point group.

```bash
python /path/to/run_inference.py \
  --config-name=symmetry \
  inference.symmetry="tetrahedral" \
  inference.num_designs=10 \
  inference.output_prefix=outputs/tetrahedral_oligo/design \
  'potentials.guiding_potentials=["type:olig_contacts,weight_intra:1,weight_inter:0.1"]' \
  potentials.olig_intra_all=True \
  potentials.olig_inter_all=True \
  potentials.guide_scale=2.0 \
  potentials.guide_decay="quadratic" \
  'contigmap.contigs=[600-600]'
```

Avoid replacing `tetrahedral` with `t3` unless the user explicitly wants the code's legacy four-rotation branch; the named point group is the documented workflow.

## Octahedral Or Icosahedral Generation

The symmetry config documents `octahedral` and `icosahedral`, and `rfdiffusion.inference.symmetry` loads saved rotations for both. Use them without `olig_contacts` first unless the installed potential manager has been extended for those chain-count symbols.

```bash
python /path/to/run_inference.py \
  --config-name=symmetry \
  inference.symmetry="octahedral" \
  inference.num_designs=3 \
  inference.output_prefix=outputs/octahedral_oligo/design \
  'contigmap.contigs=[960-960]'
```

```bash
python /path/to/run_inference.py \
  --config-name=symmetry \
  inference.symmetry="icosahedral" \
  inference.num_designs=3 \
  inference.output_prefix=outputs/icosahedral_oligo/design \
  'contigmap.contigs=[1200-1200]'
```

For memory-sensitive trials, start with fewer designs and shorter chains first. Treat `inference.model_only_neighbors=True` as an advanced/version-dependent flag rather than a guaranteed memory fix.

## Neighbor-Only Modeling Flag

`config/inference/symmetry.yaml` exposes `inference.model_only_neighbors=False`, and the sampler passes that value into the symmetry helper. In this inspected checkout, `rfdiffusion.inference.symmetry.SymGen` accepts the argument but does not visibly use it to reduce rotations, so treat `inference.model_only_neighbors=True` as version-dependent rather than a guaranteed memory fix.

```bash
python /path/to/run_inference.py \
  --config-name=symmetry \
  inference.symmetry="C12" \
  inference.model_only_neighbors=True \
  inference.num_designs=1 \
  inference.output_prefix=outputs/C12_neighbors/design \
  'contigmap.contigs=[720-720]'
```

Use this only after checking the user's installed RFdiffusion code or logs. For reliable memory reduction, first lower chain length, reduce `inference.num_designs`, disable trajectories, or test a smaller symmetry order.

## Symmetric Motif Scaffolding

Use a symmetrized motif PDB that already contains all motif copies in their intended symmetric arrangement. The contig must be precisely symmetric across the copies.

```bash
python /path/to/run_inference.py \
  inference.symmetry="C4" \
  inference.num_designs=15 \
  inference.output_prefix=outputs/design_nickel/design \
  inference.input_pdb=/path/to/nickel_symmetric_motif.pdb \
  'contigmap.contigs=[50/A2-4/50/0 50/A7-9/50/0 50/A12-14/50/0 50/A17-19/50/0]' \
  inference.ckpt_override_path=/path/to/Base_epoch8_ckpt.pt \
  'potentials.guiding_potentials=["type:olig_contacts,weight_intra:1,weight_inter:0.06"]' \
  potentials.olig_intra_all=True \
  potentials.olig_inter_all=True \
  potentials.guide_scale=2 \
  potentials.guide_decay="quadratic"
```

The repeated motif spans must exist in `inference.input_pdb`. For the C4 example, each of four chains has `50 + 3 + 50 = 103` residues, and the total sequence length is symmetric across all copies. The `/0` chain breaks are retained for clarity even though symmetry mode already creates chain separation.

## Add Model Directory Or Checkpoint Overrides

When the installation cannot find weights, add a model directory:

```bash
python /path/to/run_inference.py \
  --config-name=symmetry \
  inference.symmetry="C6" \
  inference.model_directory_path=/path/to/models \
  'contigmap.contigs=[480-480]' \
  inference.output_prefix=outputs/C6_with_models/design \
  inference.num_designs=1
```

Use `inference.ckpt_override_path=/path/to/checkpoint.pt` only for a documented checkpoint-specific workflow such as the nickel-style example or user-provided experimental checkpoint.

## Output Validation

After a successful symmetric run, check:

- Final PDB files follow the output prefix pattern, such as `design_0.pdb`.
- `.trb` files exist and contain the resolved config and contig mappings.
- The PDB has the expected number of chains for the symmetry order.
- Each chain has equal residue count for unconditional oligomers.
- Motif-scaffold outputs preserve the intended motif copies and chain layout.
- Trajectory files appear under `traj/` only when `inference.write_trajectory=True`.

Use a structure viewer or downstream geometry script to verify the expected point-group arrangement; RFdiffusion command success alone does not guarantee that the biological interface is acceptable.

## Quoting Rules

- Keep list overrides in single quotes: `'contigmap.contigs=[480-480]'`.
- Keep nested potential lists single-quoted outside and double-quoted inside: `'potentials.guiding_potentials=["type:olig_contacts,weight_intra:1,weight_inter:0.1"]'`.
- Quote symmetry names with shell metacharacter risk or uppercase values: `inference.symmetry="C6"`.
- Keep the space inside motif contig chain breaks exactly when separating chains: `'...[50/A2-4/50/0 50/A7-9/50/0]...'`.
