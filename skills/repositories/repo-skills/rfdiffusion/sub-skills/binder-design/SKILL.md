---
name: binder-design
description: "Design protein-protein binders with RFdiffusion, including
  target/binder contig ordering, hotspot residues, flexible peptide targets,
  scaffold-guided PPI runs, and downstream backbone assessment boundaries."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# RFdiffusion Binder Design

Use this sub-skill when the user wants RFdiffusion commands or debugging help for protein-protein binder generation against a target PDB, including hotspot-guided interface design, flexible peptide targets, or fold/scaffold-conditioned binders.

## Route Here

Route to `binder-design` for:

- De novo binders to a fixed target chain or target crop.
- `ppi.hotspot_res` selection, formatting, and failure checks.
- Target-plus-binder contigs separated by `/0` chain breaks.
- Flexible peptide targets where target coordinates are masked with `contigmap.inpaint_str`.
- Secondary-structure constraints for flexible peptides with `contigmap.inpaint_str_helix`, `contigmap.inpaint_str_strand`, or `contigmap.inpaint_str_loop`.
- Scaffold-guided PPI using `scaffoldguided.scaffoldguided=True`, target tensors, and scaffold directories.
- Downstream assessment boundaries for RFdiffusion backbones before sequence design or structure prediction.

Route elsewhere when:

- The task is generic motif scaffolding, motif preservation, or active-site scaffolding; use the sibling `motif-scaffolding` sub-skill.
- The task is creating scaffold secondary-structure/block-adjacency tensors; use the sibling `scaffold-guided-design` sub-skill.
- The task is pure monomer generation, oligomer symmetry, or diffusion internals; start from the root `rfdiffusion` skill and its matching sub-skill.

## Required Inputs

Collect these before drafting a command:

- Target PDB path visible to the user runtime, not a path from the source checkout.
- Output prefix for generated `.pdb` and `.trb` files.
- Target residue span(s) to include in the contig, such as `A1-150` or `B10-35`.
- Binder length range, commonly `70-100` for examples, or a fixed range like `100-100`.
- Hotspot residues as chain-qualified PDB residue IDs, such as `A59,A83,A91`.
- Number of designs for pilot versus production runs.
- Optional target crop strategy, flexible-peptide masking, scaffold directory, or target tensor files.

## Command Builder

Use the bundled helper for safe command assembly when the user gives the needed fields:

```bash
python sub-skills/binder-design/scripts/make_binder_command.py \
  --input-pdb target.pdb \
  --output-prefix outputs/binder \
  --target-contig A1-150 \
  --binder-length 70-100 \
  --hotspots A59,A83,A91 \
  --num-designs 10 \
  --noise-scale 0
```

The helper prints a `run_inference.py` command and performs lightweight validation for hotspot and contig formatting. It does not require RFdiffusion model weights and is safe to run for command drafting.

## Core Binder Pattern

For a fixed target with a sampled binder length, put target residues first, then a `/0` chain break, then the binder length range:

```bash
run_inference.py \
  inference.output_prefix=outputs/design_ppi \
  inference.input_pdb=target.pdb \
  'contigmap.contigs=[A1-150/0 70-100]' \
  'ppi.hotspot_res=[A59,A83,A91]' \
  inference.num_designs=10 \
  denoiser.noise_scale_ca=0 \
  denoiser.noise_scale_frame=0
```

This pattern selects RFdiffusion's complex checkpoint automatically when hotspots are supplied and scaffold-guided mode is off. The generated binder region is sequence-masked; output backbones may contain poly-glycine or placeholder sequence and need downstream sequence design.

## Hotspot Rules

Hotspots guide where the binder should contact the target:

- Format hotspots as a Hydra list: `'ppi.hotspot_res=[A30,A33,A34]'`.
- Each hotspot must be present in the residues retained by the contig and input PDB.
- Use target chain IDs and input-PDB residue numbers, not output indices.
- Prefer a small interface-defining set, often 3-6 residues, rather than every desired contact.
- Avoid sites that are entirely charged/polar, glycan-blocked, buried by target truncation artifacts, or far from the intended target crop.

If hotspots are omitted while a complex model is selected, RFdiffusion can warn that a hotspot-trained model is being used without hotspots. For binder design, treat that as a sign to add hotspots or reconsider the task.

## Target Cropping

RFdiffusion runtime scales with system size, so large receptors should usually be cropped before binder design. Preserve enough target context around the intended site, avoid artificial hydrophobic patches, and keep residue numbering consistent with the hotspot list and contig. If the user supplies a cropped PDB, always ask whether hotspot residue numbers refer to the cropped file.

## Noise Scales

Binder examples often lower denoiser noise to improve design quality:

- `denoiser.noise_scale_ca=0 denoiser.noise_scale_frame=0` for deterministic low-noise example-style PPI runs.
- `denoiser.noise_scale_ca=0.5 denoiser.noise_scale_frame=0.5` for a compromise that keeps more diversity.
- Default values are `1` and can be used for exploration, but may be less optimal for PPI quality.

Lower noise can reduce diversity. Suggest short pilot batches before large campaigns.

## Flexible Peptide Targets

Use flexible peptide mode when the peptide target conformation should be diffused instead of fixed:

```bash
run_inference.py \
  inference.output_prefix=outputs/flexible_peptide \
  inference.input_pdb=peptide_target.pdb \
  'contigmap.contigs=[B10-35/0 70-100]' \
  'ppi.hotspot_res=[B28,B29]' \
  inference.num_designs=10 \
  'contigmap.inpaint_str=[B10-35]'
```

`contigmap.inpaint_str` masks structure for the peptide residues, allowing RFdiffusion to design the binder while predicting a compatible peptide conformation. This triggers an inpainting-capable checkpoint.

For secondary-structure intent, enable scaffold-guided mode and specify helix, strand, or loop masks:

```bash
run_inference.py \
  inference.output_prefix=outputs/flexible_peptide_helix \
  inference.input_pdb=peptide_target.pdb \
  'contigmap.contigs=[70-100/0 B165-178]' \
  inference.num_designs=10 \
  'contigmap.inpaint_str=[B165-178]' \
  scaffoldguided.scaffoldguided=True \
  'contigmap.inpaint_str_helix=[B165-178]'
```

Do not provide both a scaffold directory and per-residue secondary-structure flags in the same scaffold-guided run; RFdiffusion asserts that these modes are mutually exclusive.

## Scaffold-Guided PPI

Use scaffold-guided PPI when the binder topology should come from scaffold files:

```bash
run_inference.py \
  scaffoldguided.target_path=target.pdb \
  inference.output_prefix=outputs/scaffolded_binder \
  scaffoldguided.scaffoldguided=True \
  scaffoldguided.target_pdb=True \
  'ppi.hotspot_res=[A59,A83,A91]' \
  scaffoldguided.target_ss=target_ss.pt \
  scaffoldguided.target_adj=target_adj.pt \
  scaffoldguided.scaffold_dir=scaffolds/ \
  inference.num_designs=10 \
  denoiser.noise_scale_ca=0 \
  denoiser.noise_scale_frame=0
```

For scaffold tensor creation, route to `scaffold-guided-design`. In this sub-skill, only explain how to connect already prepared target/scaffold inputs into a PPI run.

## Potentials Caution

PPI workflows can use guiding potentials, such as compactness via `binder_ROG`, but repo guidance cautions that potentials can interact oddly with hotspot residues. Start with no potentials as a baseline unless the user has a specific reason. If adding a compactness potential, run a small pilot and compare interface quality and failure modes before scaling.

## Downstream Boundary

RFdiffusion produces backbone candidates, not a complete binder validation result. After generation:

- Sequence the designed binder with a separate method such as ProteinMPNN if available.
- Assess structure confidence and interface quality with the user's available prediction pipeline.
- Use backbone metrics as triage, not as proof of binding.
- Keep STRIDE, Rosetta, ProteinMPNN, and AF2 optional external boundaries; do not require them to use this skill.

See `references/downstream-assessment.md` for distilled metrics and fallback assessment when STRIDE is unavailable.

## Validation Checklist

Before giving a command, verify:

- All input PDB, checkpoint, scaffold, or tensor paths are user-provided runtime paths.
- Hydra list overrides are quoted: `'contigmap.contigs=[...]'` and `'ppi.hotspot_res=[...]'`.
- The contig uses `/0` between target and binder chains.
- Hotspot residues are included in the target contig and match the input PDB numbering.
- The selected mode does not mix mutually exclusive scaffold directory and per-residue secondary-structure masks.
- `inference.output_prefix` points to a writable output location.
- Model weights are installed and compatible with the selected mode.

## References

- `references/workflows.md` for concrete binder, flexible peptide, and scaffold-guided PPI workflows.
- `references/downstream-assessment.md` for backbone triage metrics and optional sequence/prediction boundaries.
- `references/troubleshooting.md` for Hydra, contig, hotspot, model-weight, backend, and scaffold-mode failures.
