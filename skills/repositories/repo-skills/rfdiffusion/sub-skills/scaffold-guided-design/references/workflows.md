# Scaffold-Guided RFdiffusion Workflows

These workflows assume the user has an installed RFdiffusion runtime, model weights, and a callable `run_inference.py`. Replace `/path/to/run_inference.py`, tensor paths, PDB paths, and output prefixes with paths in the user's working project.

## Monomer Fold Conditioning From a Scaffold Directory

Use this when the goal is to generate monomer backbones with a coarse fold/topology, such as a TIM barrel, without a target protein.

```bash
python /path/to/run_inference.py \
  inference.output_prefix=outputs/fold_conditioned/design \
  scaffoldguided.scaffoldguided=True \
  scaffoldguided.target_pdb=False \
  scaffoldguided.scaffold_dir=scaffolds/tim_barrel \
  inference.num_designs=10 \
  denoiser.noise_scale_ca=0.5 \
  denoiser.noise_scale_frame=0.5
```

Add sampled loop and terminal length variation when the scaffold set is small or the user wants length diversity:

```bash
python /path/to/run_inference.py \
  inference.output_prefix=outputs/tim_barrel_variable/design \
  scaffoldguided.scaffoldguided=True \
  scaffoldguided.target_pdb=False \
  scaffoldguided.scaffold_dir=scaffolds/tim_barrel \
  scaffoldguided.sampled_insertion=0-5 \
  scaffoldguided.sampled_N=0-5 \
  scaffoldguided.sampled_C=0-5 \
  inference.num_designs=10 \
  denoiser.noise_scale_ca=0.5 \
  denoiser.noise_scale_frame=0.5
```

Interpretation:

- `sampled_insertion=0-5` samples extra residues in scaffold loop regions.
- `sampled_N=0-5` and `sampled_C=0-5` sample terminal additions.
- The model receives masked loop/insertion features and explicit secondary-structure/block-adjacency features for retained secondary-structure blocks.
- Use `scaffoldguided.ss_mask=N` to mask N residues near each end of helix/strand blocks when boundary uncertainty is useful.

## Scaffolded Binder Fold Conditioning

Use this when the user wants a binder whose fold comes from a scaffold library while binding a target protein.

```bash
python /path/to/run_inference.py \
  inference.output_prefix=outputs/scaffolded_binder/design \
  scaffoldguided.scaffoldguided=True \
  scaffoldguided.target_pdb=True \
  scaffoldguided.target_path=target.pdb \
  scaffoldguided.target_ss=target_folds/target_ss.pt \
  scaffoldguided.target_adj=target_folds/target_adj.pt \
  scaffoldguided.scaffold_dir=scaffolds/ppi \
  'ppi.hotspot_res=[A59,A83,A91]' \
  scaffoldguided.mask_loops=False \
  inference.num_designs=10 \
  denoiser.noise_scale_ca=0 \
  denoiser.noise_scale_frame=0
```

Binder-specific guidance:

- Route hotspot choice, target crop strategy, and interface feasibility to `../binder-design/SKILL.md`.
- For scaffolded PPI with a large scaffold set, `mask_loops=False` is often preferred; do not request loop/terminal additions in that mode.
- Lower denoiser noise (`0` or `0.5`) is commonly used for PPI fold conditioning. It can improve quality but reduces diversity.
- If the target is cropped, prepare `target_ss` and `target_adj` for the same cropped target or use `scaffoldguided.contig_crop` consistently.

## Restricting a Scaffold Library

When a directory contains many scaffold tensors but only some should be sampled, create a text file with one scaffold ID per line, without `_ss.pt` or `_adj.pt` suffixes:

```text
scaf001
scaf014
scaf022
```

Then run:

```bash
python /path/to/run_inference.py \
  inference.output_prefix=outputs/scaffold_subset/design \
  scaffoldguided.scaffoldguided=True \
  scaffoldguided.target_pdb=False \
  scaffoldguided.scaffold_dir=scaffolds/library \
  scaffoldguided.scaffold_list=scaffolds/subset.txt \
  inference.num_designs=3
```

Validation checklist:

- Every listed ID has both `ID_ss.pt` and `ID_adj.pt` in `scaffold_dir`.
- `inference.num_designs` is at least the number of listed scaffolds when the user expects systematic coverage.
- Use `scaffoldguided.systematic=True` when the user wants to step through the list instead of random scaffold sampling.

## Per-Residue Secondary-Structure Masks Without a Scaffold Directory

RFdiffusion also supports scaffold-guided mode without `scaffold_dir` when the secondary-structure intent is specified through contig inpainting masks:

```bash
python /path/to/run_inference.py \
  inference.output_prefix=outputs/flexible_peptide_strand/design \
  inference.input_pdb=peptide_target.pdb \
  'contigmap.contigs=[70-100/0 B165-178]' \
  'contigmap.inpaint_str=[B165-178]' \
  scaffoldguided.scaffoldguided=True \
  'contigmap.inpaint_str_strand=[B165-178]' \
  inference.num_designs=10
```

Rules:

- Do not also set `scaffoldguided.scaffold_dir`.
- At least one of `contigmap.inpaint_str_helix`, `contigmap.inpaint_str_strand`, or `contigmap.inpaint_str_loop` must be present when `scaffold_dir` is absent.
- If `contigmap.inpaint_str_loop` is used, set `scaffoldguided.mask_loops=False` because explicitly specified loop secondary structure should not also be loop-masked.

## Target PDB Modes

`scaffoldguided.target_pdb=False` means the scaffold-guided features describe the generated monomer or binder-like chain alone. It is the normal mode for monomer fold conditioning.

`scaffoldguided.target_pdb=True` means a target structure is appended as context during scaffold-guided generation. In this mode:

- Provide `scaffoldguided.target_path=target.pdb`.
- Provide `scaffoldguided.target_ss=..._ss.pt` and `scaffoldguided.target_adj=..._adj.pt` when using scaffolded PPI workflows.
- Use `ppi.hotspot_res` for interface targeting and route hotspot selection to `../binder-design/SKILL.md`.
- Ensure target tensor lengths match the loaded target after any crop.

## Preflight Validation

Run the bundled checker before inference:

```bash
python sub-skills/scaffold-guided-design/scripts/check_scaffold_inputs.py \
  --scaffold-dir scaffolds/library \
  --scaffold-list scaffolds/subset.txt \
  --target-pdb target.pdb \
  --target-ss target_folds/target_ss.pt \
  --target-adj target_folds/target_adj.pt \
  --hotspots A59,A83,A91 \
  --mask-loops false
```

If the checker reports missing PyTorch, install PyTorch in the user's runtime environment or treat the result as a naming/path-only check and let RFdiffusion perform tensor loading later.
