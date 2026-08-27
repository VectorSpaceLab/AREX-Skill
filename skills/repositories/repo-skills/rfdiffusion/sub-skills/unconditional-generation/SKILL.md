---
name: unconditional-generation
description: "Build safe RFdiffusion unconditional monomer/backbone generation
  commands, including Hydra contig overrides, output prefixes,
  deterministic/cautious smoke runs, model-weight prerequisites, and output-file
  interpretation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Unconditional Generation

Use this sub-skill when a user wants RFdiffusion to generate a de novo monomer backbone without a motif, target, binder, scaffold guide, macrocycle, or symmetry constraint.

## Route Here

- The request is for an unconditional monomer, de novo backbone, or random protein of a requested length or length range.
- The main user inputs are protein length, output location, number of designs, and optional cautious/deterministic/debug settings.
- The command can be expressed with `contigmap.contigs`, `inference.output_prefix`, and `inference.num_designs` against the base inference config.
- The user asks about `.pdb`, `.trb`, or `traj/` outputs from a base RFdiffusion generation run.
- The user asks for a smoke-check command that runs one deterministic design without overwriting existing outputs.

## Route Elsewhere

- Fixed motif residues, input PDB motif contigs, sequence/structure inpainting, or active-site checkpoints belong in `../motif-scaffolding/SKILL.md`.
- Auxiliary potentials such as `monomer_ROG` or `monomer_contacts` may start here only for the unconditional base command; route detailed potential selection and tuning to `../guided-potentials/SKILL.md`.
- Cyclic, dihedral, tetrahedral, or other symmetry requests belong in `../symmetric-oligomers/SKILL.md`.
- Partial diffusion from an existing structure belongs in `../partial-diffusion/SKILL.md`.
- Binder, hotspot, receptor/target, fold-conditioned scaffold-guided, or macrocycle workflows belong in their sibling sub-skills.

## Required Context

Collect these before forming a command:

- `run_inference.py` entry point: prefer the user's installed/package-provided RFdiffusion launcher; do not assume an original checkout path.
- Model weights: know either the default model directory used by the installation or an explicit `inference.model_directory_path=/path/to/models`.
- Output prefix: a path prefix, not a directory. RFdiffusion appends design indices such as `_0.pdb` and `_0.trb`.
- Length intent: exact length like `150-150` or sampled range like `100-200`.
- Number of designs: `inference.num_designs=N`; use `1` for smoke checks.
- Overwrite policy: default `inference.cautious=True` skips existing indexed `.pdb` files.

## Command Pattern

Use the workflow reference for concrete templates: `references/workflows.md`.

Core unconditional command:

```bash
python /path/to/run_inference.py 'contigmap.contigs=[150-150]' inference.output_prefix=outputs/unconditional/design inference.num_designs=10
```

For shell safety, keep Hydra list-like values in single quotes. The contig must be a single-item Hydra list, so use `'contigmap.contigs=[150-150]'`, not `contigmap.contigs=150-150`.

If the integrated root skill includes helper scripts, prefer them for command assembly or environment checks:

```bash
python ../../scripts/check_rfdiffusion_environment.py --models /path/to/models
python ../../scripts/build_inference_command.py unconditional --contig 150-150 --output-prefix outputs/unconditional/design --num-designs 10
```

If those helpers are not present in the delivered skill copy, write the command directly from `references/workflows.md`.

## Base Overrides To Prefer

- `contigmap.contigs=[L-L]`: exact unconditional backbone length.
- `contigmap.contigs=[MIN-MAX]`: sample a length in the range for each design.
- `inference.output_prefix=outputs/name/prefix`: creates `prefix_0.pdb`, `prefix_0.trb`, and optionally `traj/prefix_0_*_traj.pdb`.
- `inference.num_designs=1`: safest initial run; increase only after the environment and weights work.
- `inference.deterministic=True`: seeds each design index deterministically.
- `inference.final_step=48`: shortens inference in the repository's smoke-test pattern; use for checks, not final production quality by default.
- `inference.cautious=True`: default skip-on-existing-output behavior; keep enabled unless the user explicitly wants replacement.
- `inference.write_trajectory=False`: reduces output volume when trajectories are not needed.
- `inference.model_directory_path=/path/to/models`: points RFdiffusion at downloaded model weights.
- `inference.ckpt_override_path=/path/to/checkpoint.pt`: use only when a documented workflow needs a non-default checkpoint.

Avoid changing `model`, `preprocess`, or low-level `diffuser` settings for ordinary unconditional generation unless the user is deliberately experimenting and understands the training/inference coupling.

## Output Interpretation

A design with `inference.output_prefix=outputs/unconditional/design` and default `design_startnum=0` produces:

- `outputs/unconditional/design_0.pdb`: final generated backbone; unconditional residues are written as glycine with backbone atoms.
- `outputs/unconditional/design_0.trb`: pickled run metadata, resolved config, timing/device information, pLDDT stack, and contig mappings.
- `outputs/unconditional/traj/design_0_Xt-1_traj.pdb`: reverse diffusion trajectory input states when `write_trajectory=True`.
- `outputs/unconditional/traj/design_0_pX0_traj.pdb`: predicted denoised states when `write_trajectory=True`.

The trajectory PDBs are multi-model files ordered for visualization, with the final timestep first.

## Deterministic And Cautious Runs

For a minimal reproducible check, combine:

```bash
python /path/to/run_inference.py 'contigmap.contigs=[60-60]' inference.output_prefix=outputs/smoke/design inference.num_designs=1 inference.deterministic=True inference.final_step=48 inference.cautious=True inference.write_trajectory=False
```

RFdiffusion seeds deterministic runs from the design index. If `design_startnum=0`, `_0` is reproducible for the same environment, checkpoint, and hardware backend. If `inference.cautious=True` and `outputs/smoke/design_0.pdb` already exists, RFdiffusion skips that design instead of overwriting it.

Use `inference.design_startnum=-1` when the user wants RFdiffusion to scan existing `output_prefix_*.pdb` files and continue at the next numeric index.

## Model And Environment Checks

Before blaming contigs, verify:

- `rfdiffusion`, `rfdiffusion.contigs`, `rfdiffusion.diffusion`, and `rfdiffusion.inference.utils` import in the active Python environment.
- PyTorch is installed and the intended CPU/GPU backend is visible; GPU is strongly preferred for real RFdiffusion runs.
- Model weights are downloaded and discoverable by RFdiffusion, either through installation defaults or `inference.model_directory_path`.
- Optional explicit checkpoints passed with `inference.ckpt_override_path` exist and match the requested workflow.

The first inference run may pause while calculating and caching IGSO3 schedules. That is expected; later runs reuse the cache when the cache directory is writable.

## Common Misuse To Correct

- Unquoted contigs: replace `contigmap.contigs=[100-200]` with `'contigmap.contigs=[100-200]'` in shell commands.
- Missing list brackets: replace `'contigmap.contigs=100-200'` with `'contigmap.contigs=[100-200]'`.
- Treating `output_prefix` as a directory: explain that RFdiffusion appends `_0`, `_1`, and file extensions.
- Expecting sidechains: unconditional `.pdb` outputs are backbone-focused and write designed residues as glycine.
- Using potential examples as base unconditional advice: route potential tuning to `../guided-potentials/SKILL.md` after the base command is sound.
- Overwriting surprises: keep `inference.cautious=True` or choose a fresh prefix.

## Evidence Base

This sub-skill is backed by RFdiffusion repository evidence from the README unconditional execution/output sections, the base inference config, the inference launcher behavior, unconditional example scripts, and the native test harness pattern that rewrites examples to deterministic one-design smoke runs.

Use `references/troubleshooting.md` for error triage and `references/workflows.md` for command templates.
