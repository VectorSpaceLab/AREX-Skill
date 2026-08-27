# Motif Scaffolding Workflows

These recipes are self-contained command templates. Replace `$RFDIFFUSION_HOME`, `$MODEL_DIR`, `$INPUT_PDB`, and `$OUT_DIR` with paths in the user's environment.

## Prerequisites

- The RFdiffusion package imports in the active Python environment.
- the installed `run_inference.py` launcher is available.
- Model weights are downloaded under `$MODEL_DIR` or a checkpoint is supplied explicitly.
- The input PDB contains all referenced chain IDs, residue numbers, and any ligand/substrate for active-site potentials.
- A GPU-capable backend is strongly preferred; CPU fallback is possible but slow.

## Workflow 1: Simple Motif Scaffolding

Use when the user has an input motif span and wants RFdiffusion to build scaffold residues around it.

```bash
run_inference.py \
  inference.output_prefix="$OUT_DIR/design_motifscaffolding" \
  inference.input_pdb="$INPUT_PDB" \
  inference.model_directory_path="$MODEL_DIR" \
  inference.num_designs=10 \
  'contigmap.contigs=[10-40/A163-181/10-40]'
```

Options to adjust:

- `10-40` before and after the motif controls generated loop/scaffold length ranges.
- `A163-181` must match the input PDB motif chain and residue numbers.
- `inference.num_designs` controls independent diffusion trajectories.
- `inference.output_prefix` is a prefix, not just a directory.

Expected outputs:

- `design_motifscaffolding_0.pdb`, `design_motifscaffolding_1.pdb`, etc.
- Matching `.trb` files with sampled contig and motif mappings.
- Optional trajectory files under `traj/`.

## Workflow 2: Motif Scaffolding With Sequence Masking

Use when some motif residues are structurally useful but their amino-acid identities should be redesigned or hidden from the model.

```bash
run_inference.py \
  inference.output_prefix="$OUT_DIR/design_motifscaffolding_inpaintseq" \
  inference.input_pdb="$INPUT_PDB" \
  inference.model_directory_path="$MODEL_DIR" \
  inference.num_designs=10 \
  'contigmap.contigs=[10-40/A163-181/10-40]' \
  'contigmap.inpaint_seq=[A163-168/A170-171/A179]'
```

How to choose masked residues:

- Keep catalytic, binding, or geometry-critical identities unmasked.
- Mask support residues that may need new hydrophobic/polar identities after scaffolding.
- Use inclusive spans and slash-separated single residues or ranges.

Checkpoint note:

- RFdiffusion automatically switches to an inpaint-sequence checkpoint when `contigmap.inpaint_seq` is present unless `inference.ckpt_override_path` overrides it.

## Workflow 3: Motif Scaffolding With A Fixed Target Chain

Use when the motif comes from a complex and the target/receptor context should be included as a separate fixed chain.

```bash
run_inference.py \
  inference.output_prefix="$OUT_DIR/design_motifscaffolding_with_target" \
  inference.input_pdb="$INPUT_PDB" \
  inference.model_directory_path="$MODEL_DIR" \
  inference.num_designs=10 \
  'contigmap.contigs=[A25-109/0 0-70/B17-29/0-70]' \
  contigmap.length=70-120 \
  inference.ckpt_override_path="$MODEL_DIR/Complex_base_ckpt.pt"
```

Interpretation:

- `A25-109/0` is the fixed target chain block.
- The space after `/0` separates the target block from the designed chain.
- `0-70/B17-29/0-70` builds around motif chain `B` residues 17-29.
- `contigmap.length=70-120` constrains the designed chain length.

When to route to binder-design instead:

- The user asks for hotspot-guided binder generation using `ppi.hotspot_res`.
- The motif is not the primary constraint and interface targeting strategy is the main problem.

## Workflow 4: Active-Site Or Enzyme Motif Scaffolding

Use when the motif is very small, discontinuous, or catalytic. The active-site checkpoint is recommended for tiny motifs.

```bash
run_inference.py \
  inference.output_prefix="$OUT_DIR/design_active_site" \
  inference.input_pdb="$INPUT_PDB" \
  inference.model_directory_path="$MODEL_DIR" \
  inference.num_designs=10 \
  'contigmap.contigs=[10-100/A1083-1083/10-100/A1051-1051/10-100/A1180-1180/10-100]' \
  inference.ckpt_override_path="$MODEL_DIR/ActiveSite_ckpt.pt"
```

If the active-site geometry depends on a ligand/substrate contact potential, add substrate guidance only when the input PDB contains the ligand and the user has selected a specific potential strategy:

```bash
potentials.guide_scale=1 \
'potentials.guiding_potentials=["type:substrate_contacts,s:1,r_0:8,rep_r_0:5.0,rep_s:2,rep_r_min:1"]' \
potentials.substrate=LLK
```

Substrate potential notes:

- The input PDB must include the substrate/ligand named by `potentials.substrate`.
- This workflow uses `substrate_contacts`, not generic PPI hotspots.
- If the user mainly needs potential tuning, cross-link to the auxiliary-potentials guidance if present.

## Workflow 5: Structure Masking Around A Motif

Use when a flexible peptide or motif has sequence information but uncertain coordinates.

```bash
run_inference.py \
  inference.output_prefix="$OUT_DIR/design_motif_inpaintstr" \
  inference.input_pdb="$INPUT_PDB" \
  inference.model_directory_path="$MODEL_DIR" \
  inference.num_designs=10 \
  'contigmap.contigs=[70-100/0 B165-178]' \
  'contigmap.inpaint_str=[B165-178]'
```

Rules:

- `inpaint_str` residues should be present in the contig and input PDB.
- RFdiffusion automatically uses an inpaint-capable checkpoint unless overridden.
- If secondary structure is also specified, every secondary-structure assignment must be inside the `inpaint_str` mask.

## Workflow 6: Deterministic Smoke Test

Use one design first to catch PDB, contig, checkpoint, and Hydra errors before launching many trajectories.

```bash
run_inference.py \
  inference.output_prefix="$OUT_DIR/smoke_motif" \
  inference.input_pdb="$INPUT_PDB" \
  inference.model_directory_path="$MODEL_DIR" \
  inference.num_designs=1 \
  inference.deterministic=True \
  'contigmap.contigs=[10-20/A10-15/10-20]'
```

Smoke-test checks:

- RFdiffusion reads the intended checkpoint.
- No Hydra parse error occurs.
- The input PDB residue spans resolve.
- One `.pdb` and one `.trb` are written.
- The `.trb` sampled contig is compatible with the request.

## Review Outputs Before Downstream Design

For each accepted design:

- Align motif residues from the output to the input motif and check RMSD/geometry.
- Verify target-chain separation for `/0 ` workflows.
- Read the `.trb` mapping before splicing or scoring motif residues.
- Remember that generated residues are output as glycine backbones; downstream sequence design is required for final sequences.
- Filter failures before spending compute on sequence design or structure prediction.
