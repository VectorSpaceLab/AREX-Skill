# Unconditional Generation Troubleshooting

Use this reference to triage RFdiffusion base monomer/backbone generation failures before escalating to motif, symmetry, potential, binder, or partial-diffusion sub-skills.

## Install Or Backend Problems

Symptoms:

- `ModuleNotFoundError: rfdiffusion`, `No module named se3_transformer`, or import errors from PyTorch/DGL/e3nn dependencies.
- Logs report no GPU and the run is unexpectedly slow.
- The command starts but fails before parsing the contig.

Checks and responses:

- Verify the active Python environment can import `rfdiffusion`, `rfdiffusion.contigs`, `rfdiffusion.diffusion`, and `rfdiffusion.inference.utils`.
- Confirm the installed package is the expected RFdiffusion version for the model weights.
- Confirm PyTorch sees the intended backend. CPU fallback can work for limited inspection but is usually impractical for production RFdiffusion inference.
- If the integrated root helper exists, run `python ../../scripts/check_rfdiffusion_environment.py --models /path/to/models` from this sub-skill directory or adapt the path to the installed skill layout.

## Missing Model Weights

Symptoms:

- Checkpoint file not found.
- Model initialization fails before sampling.
- A custom `inference.ckpt_override_path` points to a nonexistent or incompatible file.

Checks and responses:

- Ask where the RFdiffusion model weights are installed.
- Add `inference.model_directory_path=/path/to/models` when the weights are not in the default location.
- Use `inference.ckpt_override_path=/path/to/checkpoint.pt` only for a documented checkpoint-specific workflow.
- For ordinary unconditional monomer generation, remove custom checkpoint overrides unless the user has a clear reason.

## Hydra Quoting And Override Errors

Symptoms:

- Hydra reports malformed override syntax.
- The shell expands or strips brackets before RFdiffusion sees them.
- Contig parsing fails for a simple unconditional request.

Fixes:

- Use `'contigmap.contigs=[150-150]'` for exact length 150.
- Use `'contigmap.contigs=[100-200]'` for a sampled range.
- Keep the entire Hydra list override in single quotes in Bash/Zsh.
- Do not write `contigmap.contigs=150-150`; RFdiffusion expects a single-item list.
- For PowerShell or other shells, preserve the same literal string reaching Python even if the quote style must change.

## Invalid Contig Or Config For This Workflow

Symptoms:

- The contig includes residue identifiers like `A10-25`, chain breaks like `/0 `, or input PDB requirements.
- The user combines unconditional generation with motif or target syntax.
- Output length does not match the user's expectation.

Fixes:

- For pure unconditional monomers, use only a generated length segment such as `[80-120]`.
- Route fixed residues, chain breaks, `inference.input_pdb`, `contigmap.inpaint_seq`, or `contigmap.inpaint_str` to motif-scaffolding or partial-diffusion as appropriate.
- Use exact ranges like `[150-150]` when the user does not want per-design length sampling.

## Output Prefix And Overwrite Surprises

Symptoms:

- The user expects files directly named `design.pdb` but sees `design_0.pdb`.
- Logs say cautious mode skipped a design.
- Later designs start at an unexpected index.

Fixes:

- Explain that `inference.output_prefix` is a prefix; RFdiffusion appends `_0`, `_1`, and file extensions.
- Default `inference.cautious=True` skips a design when the target `.pdb` already exists.
- Choose a fresh output prefix for reruns, or set `inference.design_startnum=-1` to continue after existing indices.
- Disable cautious mode only when the user explicitly accepts overwriting risk.

## First Run Appears To Stall

Symptoms:

- The first run spends a long time near an IGSO3 calculation message.
- Later runs are faster.

Explanation and fixes:

- RFdiffusion calculates and caches IGSO3 schedules on first use.
- This is expected if the cache directory is writable and the process is still active.
- If cache writes fail, choose a writable working/output location or set the relevant schedule/cache path supported by the installed configuration.
- For storage-limited checks, use `inference.write_trajectory=False`; this does not remove the need for schedule caching.

## Deterministic Smoke Run Did Not Reproduce

Symptoms:

- Two smoke runs differ despite `inference.deterministic=True`.
- Reproducing from another machine gives different results.

Checks and responses:

- Keep the same design index; deterministic seeding is applied per design index.
- Keep the same checkpoint, RFdiffusion version, PyTorch/backend stack, and relevant hardware backend.
- Ensure the previous output was not skipped by `cautious=True`; a skipped run did not regenerate anything.
- Use a fresh output prefix for comparisons and record the resolved config from the `.trb` file.

## Trajectory Files Are Missing Or Too Large

Symptoms:

- No `traj/` directory exists.
- Output directories fill quickly.

Fixes:

- If `inference.write_trajectory=False`, trajectory files are intentionally disabled.
- With default `write_trajectory=True`, expect `traj/<prefix>_Xt-1_traj.pdb` and `traj/<prefix>_pX0_traj.pdb` next to the final outputs.
- Disable trajectories for installation checks and large batches when only final backbones and metadata are needed.

## Potential-Specific Confusion

Symptoms:

- The command includes `potentials.guiding_potentials`.
- The user asks how to tune `monomer_ROG`, `monomer_contacts`, guide scale, or decay.

Response:

- Keep the unconditional length/output/design-count command here.
- Route potential selection, signatures, quoting, scaling, decay, and failure modes to `../guided-potentials/SKILL.md`.
