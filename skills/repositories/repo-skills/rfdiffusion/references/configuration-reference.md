# RFdiffusion Configuration Reference

## Purpose

Use this reference when translating a user request into RFdiffusion Hydra overrides. Keep workflow-specific choices in the nearest sub-skill; this page covers shared config groups and command construction rules.

## Entry Point

RFdiffusion installs `scripts/run_inference.py` as the main inference script. Typical usage is:

```bash
run_inference.py [--config-name=symmetry] key=value 'list.key=[item1,item2]'
```

Use `--config-name=symmetry` for point-group oligomers. Most monomer, motif, binder, partial-diffusion, scaffold-guided, and macrocycle workflows start from the base config.

## Core Groups

| Group | Important keys | Notes |
| --- | --- | --- |
| `inference` | `input_pdb`, `output_prefix`, `num_designs`, `design_startnum`, `model_directory_path`, `ckpt_override_path`, `symmetry`, `cyclic`, `cyc_chains`, `deterministic`, `cautious`, `write_trajectory`, `final_step` | Shared runtime, checkpoint, output, symmetry, and reproducibility controls. |
| `contigmap` | `contigs`, `length`, `inpaint_seq`, `inpaint_str`, `provide_seq`, `inpaint_str_helix`, `inpaint_str_strand`, `inpaint_str_loop` | Defines generated residues, fixed residues, chain breaks, sequence/structure masks, and sequence preservation. |
| `diffuser` | `T`, `partial_T`, `crd_scale`, noise schedule keys | Ordinary users usually change only `partial_T` for partial diffusion. |
| `denoiser` | `noise_scale_ca`, `noise_scale_frame`, final noise keys | Binder and scaffold-guided examples often lower the first two values. |
| `ppi` | `hotspot_res` | Chain-qualified target hotspots for binder workflows. |
| `potentials` | `guiding_potentials`, `guide_scale`, `guide_decay`, `olig_inter_all`, `olig_intra_all`, `substrate` | Auxiliary differentiable guidance; route detailed syntax to `../sub-skills/guided-potentials/SKILL.md`. |
| `scaffoldguided` | `scaffoldguided`, `target_pdb`, `target_path`, `target_ss`, `target_adj`, `scaffold_dir`, `scaffold_list`, `sampled_insertion`, `sampled_N`, `sampled_C` | Fold-conditioning and scaffolded binder inputs. |

## Quoting Rules

Quote any Hydra value containing brackets, commas, spaces, colons, or shell-special characters.

```bash
'contigmap.contigs=[A1-150/0 70-100]'
'ppi.hotspot_res=[A59,A83,A91]'
'potentials.guiding_potentials=["type:monomer_ROG,weight:1,min_dist:5"]'
```

For contigs with an internal space after a chain break, quoting is mandatory: `'contigmap.contigs=[A25-109/0 0-70/B17-29/0-70]'`.

## Output Prefix Behavior

`inference.output_prefix` is a file prefix, not just a directory. RFdiffusion appends `_0.pdb`, `_0.trb`, and later indices. If `inference.write_trajectory=True`, trajectory files are created under a sibling `traj/` directory based on the prefix directory.

## Reproducible Smoke Runs

For a fast parser/config check, use one design, deterministic mode, a fresh output prefix, and a shortened trajectory only when appropriate:

```bash
run_inference.py \
  inference.output_prefix=outputs/smoke/design \
  inference.num_designs=1 \
  inference.deterministic=True \
  inference.cautious=True \
  inference.write_trajectory=False \
  inference.final_step=48 \
  'contigmap.contigs=[60-60]'
```

Partial diffusion smoke checks often use `inference.final_step=partial_T-2` when `partial_T > 2`; do not treat that as production-quality sampling.

## Routing Reminders

- Symmetric oligomers use `--config-name=symmetry` plus `inference.symmetry`, not `inference.cyclic=True`.
- RFpeptides macrocycles use base config with `inference.cyclic=True` and `inference.cyc_chains`.
- Binder workflows usually need `ppi.hotspot_res` and a target/binder contig split by `/0`.
- Scaffold-guided workflows need `scaffoldguided.scaffoldguided=True` and either a scaffold directory/list or per-residue secondary-structure masks, not conflicting modes.
