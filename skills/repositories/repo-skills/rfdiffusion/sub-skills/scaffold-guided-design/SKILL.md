---
name: scaffold-guided-design
description: "Build and validate RFdiffusion scaffold-guided fold-conditioning
  inputs for monomers and binders, including scaffold directories, target
  tensors, secondary-structure masks, adjacency tensors, and sampled insertion
  settings."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# RFdiffusion Scaffold-Guided Design

Use this sub-skill when the user wants RFdiffusion fold conditioning from secondary-structure and block-adjacency tensors, either for monomer topology generation or binder design with a target plus scaffold library.

## Route Here

Route to `scaffold-guided-design` for:

- Scaffold-guided monomer design with `scaffoldguided.scaffoldguided=True` and `scaffoldguided.target_pdb=False`.
- Scaffold-guided binder input preparation with `scaffoldguided.target_pdb=True`, `target_path`, `target_ss`, `target_adj`, and a binder scaffold directory.
- Creating, checking, or explaining `*_ss.pt` and `*_adj.pt` files for scaffold directories or target folds.
- Choosing `scaffold_dir`, `scaffold_list`, `mask_loops`, `sampled_insertion`, `sampled_N`, `sampled_C`, `ss_mask`, or `systematic` settings.
- Debugging mutual exclusion between `scaffold_dir` and per-residue secondary-structure masks.

Route elsewhere when:

- The user wants hotspot strategy, target cropping, or interface design logic; use `../binder-design/SKILL.md`.
- The user wants pure monomer generation from length only; use `../unconditional-generation/SKILL.md`.
- The user wants partial diffusion around an existing backbone; use `../partial-diffusion/SKILL.md`.
- The user wants motif or active-site scaffolding as the primary task; use `../motif-scaffolding/SKILL.md`.

## Required Context

Collect these before drafting a command or validation plan:

- Runtime `run_inference.py` command path available to the user, not a source-checkout path from this skill.
- Output prefix and number of designs.
- Whether the workflow is monomer fold conditioning or target-bound binder fold conditioning.
- Scaffold directory containing paired `NAME_ss.pt` and `NAME_adj.pt` tensors, or explicit per-residue secondary-structure masks.
- Optional scaffold selection list, either a text file of scaffold IDs or an inline Hydra list.
- For target-bound runs: target PDB path plus optional `target_ss` and `target_adj` tensors prepared for that same target/crop.
- Sampling settings: `mask_loops`, `sampled_insertion`, `sampled_N`, `sampled_C`, and `ss_mask`.

## Safe Input Checker

Use the bundled checker before expensive inference:

```bash
python sub-skills/scaffold-guided-design/scripts/check_scaffold_inputs.py \
  --scaffold-dir scaffolds/tim_barrel \
  --sampled-insertion 0-5 \
  --sampled-n 0-5 \
  --sampled-c 0-5
```

For a scaffolded binder target:

```bash
python sub-skills/scaffold-guided-design/scripts/check_scaffold_inputs.py \
  --scaffold-dir scaffolds/ppi \
  --target-pdb target.pdb \
  --target-ss target_folds/target_ss.pt \
  --target-adj target_folds/target_adj.pt \
  --hotspots A59,A83,A91 \
  --mask-loops false
```

The checker validates file pairing, tensor ranks, shape compatibility, scaffold list membership, target tensor presence, hotspot formatting, and common RFdiffusion assertion failures. It uses Python plus optional PyTorch; when PyTorch is absent, it still performs path and naming checks.

## Command Patterns

Use `references/workflows.md` for full templates. Core monomer fold conditioning:

```bash
python /path/to/run_inference.py \
  inference.output_prefix=outputs/tim_barrel/design \
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

Core scaffolded binder fold conditioning:

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

Keep Hydra list-like values in single quotes. Prefer pilot runs with one or a few designs before scaling a large scaffold library.

## Key Rules

- `scaffoldguided.scaffoldguided=True` selects the scaffold-guided model runner.
- `scaffoldguided.scaffold_dir` expects paired files named `ID_ss.pt` and `ID_adj.pt`.
- `scaffoldguided.scaffold_dir` is mutually exclusive with `contigmap.inpaint_str_helix`, `contigmap.inpaint_str_strand`, and `contigmap.inpaint_str_loop`.
- If `scaffoldguided.mask_loops=False`, keep `sampled_insertion=0`, `sampled_N=0`, and `sampled_C=0`.
- If `scaffoldguided.target_pdb=True`, provide `scaffoldguided.target_path`; target tensors are strongly recommended for scaffolded PPI and must match the target after any crop.
- `scaffoldguided.scaffold_list` can restrict a large scaffold directory, but every listed ID must have both tensor files.

## References

- `references/workflows.md`: monomer, binder, scaffold-list, per-residue secondary-structure, and target-mode command templates.
- `references/data-formats.md`: expected tensor names, shapes, encodings, directory layouts, and optional tensor generation notes.
- `references/troubleshooting.md`: common RFdiffusion scaffold-guided errors and fixes.
