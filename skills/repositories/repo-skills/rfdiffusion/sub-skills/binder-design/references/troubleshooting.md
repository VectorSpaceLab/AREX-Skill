# Binder-Design Troubleshooting

Use this reference when a binder-design command fails, produces no useful binders, or mixes incompatible RFdiffusion modes.

## Quick Diagnosis Order

1. Confirm RFdiffusion is installed and `run_inference.py` is callable.
2. Confirm model weights/checkpoints exist for the selected mode.
3. Confirm input PDB, scaffold, target tensor, and output directories are runtime paths visible to the user.
4. Confirm Hydra list overrides are single-quoted in shells.
5. Confirm contig spans and hotspot residues exist in the input PDB numbering.
6. Confirm scaffold-guided options are not mutually exclusive.
7. Reduce to a one-design pilot with a short output prefix.

## Install, Backend, and Model Weights

Symptoms:

- Import errors for `torch`, `se3-transformer`, or `rfdiffusion`.
- `run_inference.py: command not found`.
- Checkpoint file missing or incompatible with requested inputs.
- CUDA/backend failures or CPU/GPU mismatch.

Actions:

- Verify the user's RFdiffusion environment, not the source checkout path.
- Confirm the package metadata exposes `run_inference.py` as an installed script.
- Confirm model weights are downloaded before inference.
- If using `inference.ckpt_override_path`, warn that the checkpoint must understand the selected inputs.
- Do not use `inference.trb_save_ckpt_path` as the model override; RFdiffusion asserts this is not the checkpoint selection field.

Automatic checkpoint selection behavior:

- Hotspots with non-scaffold-guided PPI select the complex checkpoint.
- `contigmap.inpaint_str`, `contigmap.inpaint_seq`, or `contigmap.provide_seq` select inpainting-capable checkpoints.
- Scaffold-guided mode selects a complex fold-conditioning checkpoint.

## Hydra Quoting Problems

Symptoms:

- Shell expands brackets or commas.
- Hydra cannot parse `contigmap.contigs` or `ppi.hotspot_res`.
- Values are split into multiple shell arguments unexpectedly.

Fix:

```bash
'contigmap.contigs=[A1-150/0 70-100]'
'ppi.hotspot_res=[A59,A83,A91]'
'contigmap.inpaint_str=[B10-35]'
'potentials.guiding_potentials=["type:binder_ROG,min_dist:5,weight:10"]'
```

Rules:

- Quote the entire Hydra override containing brackets.
- Keep contigs as a single-item list.
- Do not add spaces after commas in `ppi.hotspot_res` unless the shell/Hydra command is tested.
- For potentials, quote nested strings carefully.

## Invalid Contigs

Symptoms:

- Contig construction errors.
- Length mismatch errors.
- Binder fused to the target unexpectedly.
- Hotspots not mapped to target residues.

Checks:

- Use `/0` for a chain break between target and binder.
- Ensure target spans exist in the PDB and use correct chain IDs.
- Ensure binder length ranges are numeric, such as `70-100` or `100-100`.
- If using partial diffusion, the contig length must exactly match the input structure length.
- If using scaffold-guided contig mode, adjacency and secondary-structure tensors must match the contig length.

Common fixes:

```text
Wrong: contigmap.contigs=[A1-150 70-100]
Right: 'contigmap.contigs=[A1-150/0 70-100]'

Wrong: hotspot A159 after target was renumbered to A59
Right: use the residue number present in the exact runtime PDB
```

## Hotspot Misuse

Symptoms:

- Binder ignores the intended site.
- Hotspot tensor has no effect because residues are not included.
- Command runs but results bind crop artifacts.

Checks:

- Every hotspot must be included in the retained target contig.
- Hotspots use input-PDB chain and residue numbering.
- Cropped targets should preserve numbering or the hotspot list must be updated.
- Use 3-6 interface-defining residues as a starting point.
- Avoid choosing every possible contact; the model was trained to receive only a subset of true contacting residues.

If a target is large, crop it around the intended site but preserve enough surrounding structure to avoid artificial hydrophobic patches.

## Missing PDB, Checkpoint, or Output Files

Symptoms:

- File-not-found errors for `inference.input_pdb`, `scaffoldguided.target_path`, tensors, scaffolds, or checkpoints.
- No `.pdb`/`.trb` pairs produced.

Actions:

- Replace example placeholders with user runtime paths.
- Ensure output parent directories are writable or create them before running.
- For scaffold-guided PPI, verify all of these if used:
  - `scaffoldguided.target_path`
  - `scaffoldguided.target_ss`
  - `scaffoldguided.target_adj`
  - `scaffoldguided.scaffold_dir` or `scaffoldguided.scaffold_list`
- Keep `.trb` files; they are needed for sampled contigs and residue mappings.

## Flexible Peptide Failures

Symptoms:

- Peptide remains fixed when it should be flexible.
- Secondary-structure specification is ignored or asserts.
- Inpainting checkpoint selected unexpectedly.

Checks:

- Add `contigmap.inpaint_str=[chainStart-chainEnd]` to diffuse peptide structure.
- Use `contigmap.inpaint_str_helix`, `contigmap.inpaint_str_strand`, or `contigmap.inpaint_str_loop` only with `scaffoldguided.scaffoldguided=True`.
- Do not use a scaffold directory and per-residue secondary-structure specification in the same command.
- Confirm the peptide span appears in the contig.

## Scaffold-Guided PPI Failures

Symptoms:

- Assertion about `scaffold_dir` and per-residue secondary structure.
- Target tensor shape mismatch.
- Confusion between `inference.input_pdb` and `scaffoldguided.target_path`.

Rules:

- Prepared scaffold-directory mode uses `scaffoldguided.scaffold_dir=...`.
- Per-residue secondary-structure mode uses `contigmap.inpaint_str_helix/strand/loop` and no scaffold directory.
- Target PDB mode uses `scaffoldguided.target_pdb=True` plus `scaffoldguided.target_path=...`.
- If a specific contig is also supplied in scaffold-guided mode, do not provide target via the scaffold target object in ways that conflict with the runner assertion.

Route scaffold tensor creation and detailed scaffold preprocessing to `scaffold-guided-design`.

## Poor Binder Quality

Symptoms:

- Binders are far from hotspots.
- Binders collapse into unrealistic compact shapes.
- Low diversity or repeated topologies.
- Designs target crop artifacts instead of intended surface.

Actions:

- Run a pilot batch and inspect results before scaling.
- Revisit target crop and hotspot choice.
- Try noise scales `0`, `0.5`, and default `1` as a controlled comparison.
- Start without guiding potentials; add compactness potentials only after a baseline.
- Increase design count only after the command produces plausible placements.
- Use downstream sequence design and complex prediction before calling a design successful.

## Downstream Assessment Problems

Symptoms:

- User lacks STRIDE.
- Metrics CSV has missing columns or `NA` values.
- ProteinMPNN or AF2-style tools are unavailable.

Actions:

- Use geometry-only triage when STRIDE is missing.
- Treat missing secondary-structure percentages as skipped, not failed, unless the user explicitly requires them.
- Explain that sequence design and complex prediction are external boundaries.
- Preserve PDB/TRB outputs so downstream pipelines can run later.
