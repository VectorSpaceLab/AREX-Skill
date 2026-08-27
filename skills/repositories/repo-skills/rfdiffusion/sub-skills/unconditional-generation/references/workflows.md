# Unconditional Generation Workflows

This reference gives portable command templates for RFdiffusion unconditional monomer/backbone generation. Replace `/path/to/run_inference.py`, `/path/to/models`, and output paths with paths in the user's environment. Do not rely on an original RFdiffusion source checkout being present.

## Minimal Exact-Length Monomer

Use this when the user asks for a single-chain backbone with a fixed length.

```bash
python /path/to/run_inference.py \
  'contigmap.contigs=[150-150]' \
  inference.output_prefix=outputs/unconditional/design \
  inference.num_designs=10
```

What the overrides mean:

- `'contigmap.contigs=[150-150]'` asks RFdiffusion to generate one chain with exactly 150 residues.
- `inference.output_prefix=outputs/unconditional/design` is a file prefix; output files become `design_0.pdb`, `design_0.trb`, and so on.
- `inference.num_designs=10` runs design indices `0` through `9` when `design_startnum=0`.

## Sample A Length Range

Use a length range when the user wants diversity in chain length.

```bash
python /path/to/run_inference.py \
  'contigmap.contigs=[100-200]' \
  inference.output_prefix=outputs/range/design \
  inference.num_designs=10
```

RFdiffusion records the sampled contig and resolved config in each `.trb` file. If the user needs a fixed length, use `150-150` rather than `100-200`.

## Deterministic One-Design Smoke Check

Use this before long production batches, especially after installing RFdiffusion or moving model weights.

```bash
python /path/to/run_inference.py \
  'contigmap.contigs=[60-60]' \
  inference.output_prefix=outputs/smoke/design \
  inference.num_designs=1 \
  inference.deterministic=True \
  inference.final_step=48 \
  inference.cautious=True \
  inference.write_trajectory=False
```

Expected behavior:

- Runs one design with deterministic seeding for design index `_0`.
- Uses the repository's native smoke-test style of `inference.final_step=48` to reduce runtime.
- Skips the design if `outputs/smoke/design_0.pdb` already exists because `cautious=True`.
- Writes only `.pdb` and `.trb` because trajectories are disabled.

If the user needs a true non-mutating dry run, explain that RFdiffusion's inference command normally writes outputs; instead, run environment/model checks first and choose a temporary output prefix.

## Continue Numbering Without Overwrite

Use `inference.design_startnum=-1` when an output prefix already has designs and the user wants to continue at the next available index.

```bash
python /path/to/run_inference.py \
  'contigmap.contigs=[100-100]' \
  inference.output_prefix=outputs/batch/design \
  inference.num_designs=5 \
  inference.design_startnum=-1 \
  inference.cautious=True
```

RFdiffusion scans existing files matching `output_prefix_*.pdb`, finds the highest numeric suffix, and starts after it. Keep `cautious=True` as a second guard.

## Use An Explicit Model Directory

Use this when model weights are not in the default location for the installation.

```bash
python /path/to/run_inference.py \
  'contigmap.contigs=[150-150]' \
  inference.output_prefix=outputs/with_models/design \
  inference.num_designs=1 \
  inference.model_directory_path=/path/to/models
```

The model directory must contain the checkpoints expected by the installed RFdiffusion version. If the user asks how to obtain weights, route to the root model-weights reference when present.

## Use An Explicit Checkpoint

Use `inference.ckpt_override_path` sparingly. It is appropriate when a documented workflow requires a specific checkpoint; ordinary unconditional monomer generation should usually use the default model selection.

```bash
python /path/to/run_inference.py \
  'contigmap.contigs=[150-150]' \
  inference.output_prefix=outputs/custom_ckpt/design \
  inference.num_designs=1 \
  inference.ckpt_override_path=/path/to/checkpoint.pt
```

If the request mentions active sites, binder beta checkpoints, motifs, or complexes, route to the relevant sibling sub-skill rather than treating it as generic unconditional generation.

## Trajectory Output Controls

Default base config has `inference.write_trajectory=True`, which writes trajectory PDBs under a sibling `traj/` directory next to the output prefix.

```bash
python /path/to/run_inference.py \
  'contigmap.contigs=[120-120]' \
  inference.output_prefix=outputs/no_traj/design \
  inference.num_designs=3 \
  inference.write_trajectory=False
```

Turn trajectories off for quick checks or storage-sensitive runs. Keep them on when the user wants PyMOL visualization of the reverse diffusion path.

## Add Potential Guidance Without Owning It Here

The unconditional examples include potential-guided variants. Build the base command here, then route detailed potential syntax and tuning to `../guided-potentials/SKILL.md`.

```bash
python /path/to/run_inference.py \
  'contigmap.contigs=[100-200]' \
  inference.output_prefix=outputs/potential/design \
  inference.num_designs=10 \
  'potentials.guiding_potentials=["type:monomer_contacts,weight:0.05"]'
```

For radius-of-gyration guidance, the live potential constructor is `monomer_ROG(weight=1, min_dist=15)`, but weighting, guide scale, and decay choices belong in the guided-potentials sub-skill.

## Command Quoting Rules

Hydra overrides are parsed by both the shell and Hydra. Preserve these rules:

- Quote list-like overrides with single quotes: `'contigmap.contigs=[100-200]'`.
- Quote nested potential lists with single quotes outside and double quotes inside.
- Avoid shell glob characters in unquoted values.
- Use absolute or user-relative paths for model/checkpoint paths; avoid paths from a DisCo generation environment.
- Do not insert spaces inside one Hydra override except where the documented contig syntax requires a chain-break space for other workflows.

## Output Checklist

After a successful run with `inference.output_prefix=outputs/unconditional/design` and `inference.num_designs=1`, check for:

- `outputs/unconditional/design_0.pdb`
- `outputs/unconditional/design_0.trb`
- `outputs/unconditional/traj/design_0_Xt-1_traj.pdb` when `write_trajectory=True`
- `outputs/unconditional/traj/design_0_pX0_traj.pdb` when `write_trajectory=True`

If `.pdb` is missing but logs say cautious mode skipped the design, choose a new output prefix, delete old outputs intentionally, or set a new `inference.design_startnum`.
