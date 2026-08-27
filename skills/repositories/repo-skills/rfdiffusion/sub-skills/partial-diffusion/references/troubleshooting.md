# Partial-Diffusion Troubleshooting

## Command or Hydra Override Fails Immediately

Likely causes:

- The shell parsed brackets, commas, slashes, or spaces before Hydra saw them.
- The contig was passed as a string rather than a single-item Hydra list.
- A contig containing a chain break and a space omitted inner double quotes.

Fixes:

```bash
'contigmap.contigs=[79-79]'
'contigmap.contigs=["172-172/0 34-34"]'
'contigmap.provide_seq=[172-177,200-205]'
```

Keep these overrides single-quoted in POSIX shells. If running from another launcher, preserve the same literal strings in that launcher's argument list.

## Missing input_pdb, Checkpoint, or Model Files

Symptoms:

- File-not-found errors before sampling.
- Checkpoint/model-load failures.
- `provide_seq` runs fail after a base partial-diffusion run worked.

Checks:

- `inference.input_pdb` points to an existing PDB file.
- `inference.output_prefix` parent directory is writable or can be created.
- RFdiffusion model weights have been downloaded and are discoverable by the installed package.
- If using `inference.ckpt_override_path`, the checkpoint file exists.
- If using `inference.model_directory_path`, that directory contains the expected RFdiffusion weights.

`contigmap.provide_seq` may cause RFdiffusion to use a different checkpoint automatically. Treat missing checkpoint failures as an environment/model-weight issue, not as a sequence-range issue, unless the config also reports invalid ranges.

## No GPU or Backend Problems

RFdiffusion can report that no GPU is detected and fall back to CPU. CPU runs may be very slow. Backend issues commonly involve `torch`, CUDA compatibility, or `se3-transformer` installation.

Checks:

- Python can import `rfdiffusion`, `torch`, and `se3_transformer`-related dependencies in the active environment.
- `torch.cuda.is_available()` matches the intended hardware expectation.
- Installed RFdiffusion package metadata includes the `run_inference.py` script entrypoint.
- Model weights and CUDA libraries are available on the machine running inference.

Do not fix backend problems by changing partial-diffusion contigs. First prove a minimal one-design command can initialize the sampler.

## Contig Length Does Not Match the Input PDB

Symptoms:

- Errors during contig mapping or sampler initialization.
- Output length differs from the user's expectation.
- Partial diffusion appears to add or remove residues unexpectedly.

Cause:

Partial diffusion starts from known coordinates. The total length represented by `contigmap.contigs` must exactly match the input structure being diffused. RFdiffusion cannot partial-diffuse extra residues that do not exist in the input coordinate distribution.

Fix workflow:

1. Count the residues in the input PDB after selecting intended chains/spans.
2. Sum fixed contig lengths and sampled ranges after they resolve.
3. Include chain-break-separated partners in the total.
4. Make the total equal to the input length.
5. Use fixed ranges such as `100-100`, not broad sampled ranges, when exact length matching matters.

Examples:

- Valid for a 79-residue monomer: `'contigmap.contigs=[79-79]'`.
- Valid for a 250-residue binder-target complex: `'contigmap.contigs=[100-100/0 B1-150]'`.
- Invalid for an 80-residue input: `'contigmap.contigs=[100-100]'`.

## provide_seq Preserves the Wrong Residues

Symptoms:

- A peptide or motif sequence changes even though `provide_seq` was set.
- The wrong chain segment remains fixed.
- Multiple ranges preserve unexpected positions.

Cause:

`contigmap.provide_seq` uses zero-indexed positions over the full contig, not PDB residue numbers and not per-chain numbering. Ranges are inclusive.

Fix workflow:

1. Write the contig as a linear sequence of output positions.
2. Assign zero-indexed positions from left to right across chain breaks.
3. Convert the intended preserved spans into global positions.
4. Use inclusive ranges.
5. For multiple spans, separate ranges with commas inside one quoted override.

Example:

For `'contigmap.contigs=["172-172/0 34-34"]'`, positions `0-171` are the scaffold and positions `172-205` are the peptide. Preserve the whole peptide with:

```bash
'contigmap.provide_seq=[172-205]'
```

Preserve only peptide termini with:

```bash
'contigmap.provide_seq=[172-177,200-205]'
```

## partial_T Gives Too Much or Too Little Diversity

Symptoms:

- Outputs are nearly identical to the input.
- Outputs drift too far from the input fold or interface.
- The same command works structurally but does not meet the design goal.

Fixes:

- Decrease `diffuser.partial_T` for less drift.
- Increase `diffuser.partial_T` for more diversity.
- Under default `diffuser.T=50`, try a small sweep such as `partial_T=5`, `10`, `15`, and `20`.
- Avoid assuming values from older 200-step schedules transfer directly; `partial_T=80` in a 200-step setup is roughly analogous to `partial_T=20` with `T=50`.

## final_step Misuse in Smoke Tests

`inference.final_step=partial_T-2` is useful for fast deterministic command checks when `partial_T` is greater than `2`. It shortens the denoising loop and should not be mistaken for the default production trajectory.

For production, omit `inference.final_step` unless the user intentionally wants early stopping and understands the consequence.

## Cautious Mode Skips Designs

By default, `inference.cautious=True`. If an output PDB already exists for the requested prefix and design index, RFdiffusion skips that design.

Fixes:

- Choose a new `inference.output_prefix`.
- Set `inference.design_startnum` to a fresh index.
- Remove or archive old outputs if appropriate.
- Only set `inference.cautious=False` when overwriting is intentional.

## Output Files Are Missing or Unexpected

Expected files for `inference.output_prefix=outputs/partial/design` include:

- `outputs/partial/design_0.pdb`
- `outputs/partial/design_0.trb`
- `outputs/partial/traj/design_0_Xt-1_traj.pdb` when trajectories are enabled
- `outputs/partial/traj/design_0_pX0_traj.pdb` when trajectories are enabled

If files are absent:

- Check logs for cautious-mode skips.
- Confirm the parent output directory is writable.
- Confirm the command reached the sampling loop rather than failing during sampler initialization.
- Run a one-design deterministic smoke test with a fresh output prefix.

## When to Route Elsewhere

- No input PDB and the user wants new proteins by length: use unconditional generation.
- New binder design strategy, hotspot residues, or interface potentials: use binder design.
- Motif scaffolding where the user wants to build new connector residues around a fixed motif: use motif-scaffolding guidance if available.
- Symmetric oligomer generation: use symmetry guidance if available, then return here only if partial diffusion around a symmetric input is explicitly requested.
