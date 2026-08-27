# Binder-Design Workflows

This reference gives self-contained RFdiffusion binder-design command patterns. Replace placeholder paths with files available in the user's runtime environment. Commands assume the RFdiffusion console script `run_inference.py` is on `PATH`; if it is not, use the installed script path from the user's environment.

## 1. De Novo Binder to a Fixed Target

Use when the target backbone is fixed and the binder length is sampled.

```bash
run_inference.py \
  inference.output_prefix=outputs/binder_pilot/design \
  inference.input_pdb=inputs/target_crop.pdb \
  'contigmap.contigs=[A1-150/0 70-100]' \
  'ppi.hotspot_res=[A59,A83,A91]' \
  inference.num_designs=10 \
  denoiser.noise_scale_ca=0 \
  denoiser.noise_scale_frame=0
```

Inputs and outputs:

- `inputs/target_crop.pdb`: target PDB containing chain `A` residues `1-150` and hotspot residues `A59`, `A83`, `A91`.
- `outputs/binder_pilot/design_*.pdb`: generated complex backbones.
- `outputs/binder_pilot/design_*.trb`: run metadata including sampled contig and config.

Checks before running:

- Confirm `A1-150` exactly matches residues in the PDB after any cleaning or cropping.
- Confirm hotspots refer to input-PDB numbering, not renumbered output residues.
- Keep the target before `/0` and the binder range after `/0` for target-first PPI examples.
- Use a small pilot batch before thousands of designs.

## 2. Command Assembly Helper

Use the bundled helper to draft commands and catch simple formatting errors:

```bash
python sub-skills/binder-design/scripts/make_binder_command.py \
  --input-pdb inputs/target_crop.pdb \
  --output-prefix outputs/binder_pilot/design \
  --target-contig A1-150 \
  --binder-length 70-100 \
  --hotspots A59,A83,A91 \
  --num-designs 10 \
  --noise-scale 0
```

For binder-first contig order, pass `--binder-first`. Binder-first is useful for peptide examples where the designed chain should appear before the target segment in the output:

```bash
python sub-skills/binder-design/scripts/make_binder_command.py \
  --input-pdb inputs/peptide.pdb \
  --output-prefix outputs/peptide_helix/design \
  --target-contig B165-178 \
  --binder-length 70-100 \
  --hotspots B170,B174 \
  --num-designs 10 \
  --binder-first \
  --inpaint-str B165-178 \
  --secondary-structure helix
```

## 3. Flexible Peptide Binder

Use when the target peptide's 3D coordinates should not remain fixed during binder generation.

```bash
run_inference.py \
  inference.output_prefix=outputs/flexible_peptide/design \
  inference.input_pdb=inputs/peptide_target.pdb \
  'contigmap.contigs=[B10-35/0 70-100]' \
  'ppi.hotspot_res=[B28,B29]' \
  inference.num_designs=10 \
  'contigmap.inpaint_str=[B10-35]'
```

Key behavior:

- `contigmap.inpaint_str=[B10-35]` masks the peptide structure while preserving the target residue identity context.
- This mode selects an inpainting-capable checkpoint automatically.
- Use hotspots on the peptide chain to bias the interface.

Validation:

- The inpainted span should be present in the contig.
- The peptide span should be long enough to represent the intended epitope.
- If the peptide sequence should be fixed while structure moves, do not add `contigmap.inpaint_seq` unless sequence masking is intended.

## 4. Flexible Peptide with Secondary Structure

Use when the peptide should be modeled as helix, strand, or loop while designing the binder.

```bash
run_inference.py \
  inference.output_prefix=outputs/flexible_peptide_helix/design \
  inference.input_pdb=inputs/peptide_target.pdb \
  'contigmap.contigs=[70-100/0 B165-178]' \
  inference.num_designs=10 \
  'contigmap.inpaint_str=[B165-178]' \
  scaffoldguided.scaffoldguided=True \
  'contigmap.inpaint_str_helix=[B165-178]'
```

Choose one of:

- `contigmap.inpaint_str_helix=[B165-178]`
- `contigmap.inpaint_str_strand=[B165-178]`
- `contigmap.inpaint_str_loop=[B165-178]`

Important constraints:

- Do not combine per-residue secondary-structure flags with `scaffoldguided.scaffold_dir`; RFdiffusion asserts these inputs are mutually exclusive.
- If specifying loop secondary structure directly, `scaffoldguided.mask_loops` should not contradict that choice.
- The secondary-structure span should match the flexible peptide span unless the user intentionally constrains only part of the peptide.

## 5. Scaffold-Guided PPI

Use when the binder topology is selected from prepared scaffold files and a target PDB is supplied separately.

```bash
run_inference.py \
  scaffoldguided.target_path=inputs/target_crop.pdb \
  inference.output_prefix=outputs/scaffolded_ppi/design \
  scaffoldguided.scaffoldguided=True \
  scaffoldguided.target_pdb=True \
  'ppi.hotspot_res=[A59,A83,A91]' \
  scaffoldguided.target_ss=inputs/target_ss.pt \
  scaffoldguided.target_adj=inputs/target_adj.pt \
  scaffoldguided.scaffold_dir=inputs/scaffolds/ \
  inference.num_designs=10 \
  denoiser.noise_scale_ca=0 \
  denoiser.noise_scale_frame=0
```

Inputs and ownership:

- `scaffoldguided.scaffold_dir`: directory of prepared scaffold secondary-structure/adjacency inputs.
- `scaffoldguided.target_ss` and `scaffoldguided.target_adj`: precomputed tensors for the target when supplied.
- This sub-skill covers the PPI command wiring; route tensor generation details to `scaffold-guided-design`.

Recommended PPI options:

- Lower noise often improves PPI quality: `denoiser.noise_scale_ca=0` and `denoiser.noise_scale_frame=0`, or `0.5` for more diversity.
- `scaffoldguided.mask_loops=False` can be useful in scaffold-guided PPI when using prepared scaffold sets.
- Use `scaffoldguided.scaffold_list=...` when selecting a subset of scaffolds from a larger directory.

## 6. Potentials as Optional Biases

Start without potentials for PPI unless the user requests a specific bias. If compactness is desired, a pilot command can add a binder radius-of-gyration potential:

```bash
run_inference.py \
  inference.output_prefix=outputs/binder_potential/design \
  inference.input_pdb=inputs/target_crop.pdb \
  'contigmap.contigs=[A1-150/0 70-100]' \
  'ppi.hotspot_res=[A59,A83,A91]' \
  'potentials.guiding_potentials=["type:binder_ROG,min_dist:5,weight:10"]' \
  potentials.guide_scale=10 \
  potentials.guide_decay=quadratic \
  inference.num_designs=10 \
  denoiser.noise_scale_ca=0.5 \
  denoiser.noise_scale_frame=0.5
```

Caution:

- Potentials can interact unexpectedly with hotspot-guided PPI.
- Compare potential-guided runs against a no-potential baseline.
- Treat compactness as a design bias, not a binding validation metric.

## 7. Production Scaling

After a pilot succeeds:

1. Inspect output PDBs for binder placement near hotspots and obvious clashes.
2. Confirm `.trb` metadata records the expected contig and checkpoint.
3. Increase `inference.num_designs` or launch multiple prefixes/jobs.
4. Sequence promising backbones with the user's chosen sequence-design method.
5. Filter sequence-designed complexes with the user's structure-prediction and interface metrics.

Avoid promising experimental success from RFdiffusion backbone generation alone.
