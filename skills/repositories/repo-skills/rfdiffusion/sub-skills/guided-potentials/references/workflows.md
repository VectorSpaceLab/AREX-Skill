# Guided Potential Workflows

These workflows assume the user already has a working RFdiffusion installation, model weights, and a runtime-visible `run_inference.py` launcher. Replace placeholder PDB, checkpoint, and output paths with user-provided paths.

## Monomer Compactness Pilot

Use when an unconditional or motif-scaffolded monomer is too elongated.

Baseline first:

```bash
run_inference.py \
  inference.output_prefix=outputs/monomer_baseline/design \
  'contigmap.contigs=[100-200]' \
  inference.num_designs=10
```

Then pilot `monomer_ROG`:

```bash
run_inference.py \
  inference.output_prefix=outputs/monomer_rog/design \
  'contigmap.contigs=[100-200]' \
  inference.num_designs=10 \
  'potentials.guiding_potentials=["type:monomer_ROG,weight:1,min_dist:5"]' \
  potentials.guide_scale=2 \
  potentials.guide_decay=quadratic
```

Review whether compactness improves without obvious collapse or severe backbone artifacts. If the effect is too weak, change one parameter at a time; if too strong, reduce `potentials.guide_scale` or `weight`.

## Monomer Contact Pilot

Use when the objective is more internal contacts rather than explicit radius-of-gyration pressure.

```bash
run_inference.py \
  inference.output_prefix=outputs/monomer_contacts/design \
  'contigmap.contigs=[100-200]' \
  inference.num_designs=10 \
  'potentials.guiding_potentials=["type:monomer_contacts,weight:0.05"]'
```

Keep `weight` small initially. This potential can produce problematic gradients when pushed too hard.

## Symmetric Oligomer Contacts

Route symmetry setup to the symmetric oligomer sub-skill first. Once symmetry and contig are valid, add `olig_contacts`.

Cyclic example:

```bash
run_inference.py \
  --config-name=symmetry \
  inference.symmetry=C6 \
  inference.output_prefix=outputs/c6_oligo/design \
  'contigmap.contigs=[480-480]' \
  inference.num_designs=10 \
  'potentials.guiding_potentials=["type:olig_contacts,weight_intra:1,weight_inter:0.1"]' \
  potentials.olig_intra_all=True \
  potentials.olig_inter_all=True \
  potentials.guide_scale=2 \
  potentials.guide_decay=quadratic
```

Dihedral example:

```bash
run_inference.py \
  --config-name=symmetry \
  inference.symmetry=D2 \
  inference.output_prefix=outputs/d2_oligo/design \
  'contigmap.contigs=[320-320]' \
  inference.num_designs=10 \
  'potentials.guiding_potentials=["type:olig_contacts,weight_intra:1,weight_inter:0.1"]' \
  potentials.olig_intra_all=True \
  potentials.olig_inter_all=True \
  potentials.guide_scale=2 \
  potentials.guide_decay=quadratic
```

Tetrahedral example:

```bash
run_inference.py \
  --config-name=symmetry \
  inference.symmetry=tetrahedral \
  inference.output_prefix=outputs/tetrahedral_oligo/design \
  'contigmap.contigs=[600-600]' \
  inference.num_designs=10 \
  'potentials.guiding_potentials=["type:olig_contacts,weight_intra:1,weight_inter:0.1"]' \
  potentials.olig_intra_all=True \
  potentials.olig_inter_all=True \
  potentials.guide_scale=2 \
  potentials.guide_decay=quadratic
```

For custom chain-pair matrices, replace all-inter/all-intra settings with `potentials.olig_custom_contact`. Example with A-B attraction and A-C repulsion:

```bash
'potentials.guiding_potentials=["type:olig_contacts,weight_intra:1,weight_inter:0.1"]' \
  potentials.olig_custom_contact='A&B,A!C'
```

Use custom contacts only when the chain count and intended pair map are clear.

## Symmetric Motif Or Metal-Site Scaffolding

Use when the user already has a symmetrized motif input PDB and contigs from motif/symmetry guidance.

```bash
run_inference.py \
  inference.symmetry=C4 \
  inference.input_pdb=symmetrized_motif.pdb \
  inference.output_prefix=outputs/c4_motif/design \
  inference.num_designs=15 \
  'contigmap.contigs=[50/A2-4/50/0 50/A7-9/50/0 50/A12-14/50/0 50/A17-19/50/0]' \
  'potentials.guiding_potentials=["type:olig_contacts,weight_intra:1,weight_inter:0.06"]' \
  potentials.olig_intra_all=True \
  potentials.olig_inter_all=True \
  potentials.guide_scale=2 \
  potentials.guide_decay=quadratic \
  inference.ckpt_override_path=/path/to/Base_epoch8_ckpt.pt
```

The key requirements are symmetric motif geometry, symmetry-compatible contigs, and a user-supplied checkpoint path if a non-default checkpoint is needed.

## Binder Compactness Or Contact Pilots

Route binder setup and hotspot choice to `../binder-design/SKILL.md` first. Add potentials only after a baseline run works.

Conservative binder compactness pilot:

```bash
run_inference.py \
  inference.output_prefix=outputs/binder_rog/design \
  inference.input_pdb=target.pdb \
  'contigmap.contigs=[A1-150/0 70-100]' \
  'ppi.hotspot_res=[A59,A83,A91]' \
  inference.num_designs=5 \
  denoiser.noise_scale_ca=0 \
  denoiser.noise_scale_frame=0 \
  'potentials.guiding_potentials=["type:binder_ROG,weight:0.5,min_dist:15"]' \
  potentials.guide_scale=1 \
  potentials.guide_decay=quadratic
```

Binder internal contacts pilot:

```bash
'potentials.guiding_potentials=["type:binder_ncontacts,weight:0.05,r_0:8,d_0:4"]' potentials.guide_scale=1 potentials.guide_decay=quadratic
```

Interface contact pilot:

```bash
'potentials.guiding_potentials=["type:interface_ncontacts,weight:0.05,r_0:8,d_0:6"]' potentials.guide_scale=1 potentials.guide_decay=quadratic
```

For PPI, do not treat a higher contact count as proof of a better binder. Check whether the binder still contacts the intended hotspot region and whether downstream sequence/structure evaluation remains plausible.

## Enzyme Active-Site Substrate Contacts

Route motif contigs, active-site checkpoint selection, and motif residue preservation to `../motif-scaffolding/SKILL.md` first. Then add substrate contacts when the input PDB includes the substrate residue.

```bash
run_inference.py \
  inference.output_prefix=outputs/enzyme/design \
  inference.input_pdb=active_site_input.pdb \
  'contigmap.contigs=[10-100/A1083-1083/10-100/A1051-1051/10-100/A1180-1180/10-100]' \
  inference.num_designs=10 \
  'potentials.guiding_potentials=["type:substrate_contacts,s:1,r_0:8,rep_r_0:5.0,rep_s:2,rep_r_min:1"]' \
  potentials.substrate=LLK \
  potentials.guide_scale=1 \
  inference.ckpt_override_path=/path/to/ActiveSite_ckpt.pt
```

Checklist for substrate runs:

- The input PDB contains motif residues and the substrate residue named by `potentials.substrate`.
- The contig preserves the catalytic/motif residues needed to define the substrate frame.
- The checkpoint is suitable for active-site scaffolding when the motif is very small.
- The substrate residue name matches the PDB residue name exactly.

## Combining Potentials

RFdiffusion accepts a list of multiple potential strings:

```bash
'potentials.guiding_potentials=["type:monomer_ROG,weight:0.5,min_dist:5","type:monomer_contacts,weight:0.02"]' potentials.guide_scale=1 potentials.guide_decay=quadratic
```

Use this only after each potential has been piloted separately. Combined potentials make failures harder to diagnose and can over-constrain the trajectory.

## Command Review Checklist

For every workflow:

- Keep Hydra list overrides in single quotes.
- Keep each potential as one double-quoted string inside the list.
- Use numeric values for all per-potential keys except `type`.
- Explicitly set `guide_scale` when following examples; avoid relying on the base default unless intentional.
- Choose `guide_decay=quadratic` for example-style early guidance, or `constant` only when persistent guidance is deliberate.
- Avoid original checkout paths in final commands; use user runtime paths.
