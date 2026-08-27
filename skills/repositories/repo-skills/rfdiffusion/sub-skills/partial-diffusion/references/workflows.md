# Partial-Diffusion Workflows

These workflows assume RFdiffusion is installed so `run_inference.py` is available on `PATH`, model weights are available to RFdiffusion, and all input files are user-provided portable paths. Do not rely on a source checkout layout.

## Configuration Facts

RFdiffusion inference is controlled by Hydra overrides. The relevant base groups are:

- `inference.input_pdb`: path to the known structure to partially noise.
- `inference.output_prefix`: output path prefix; designs are suffixed as `_0.pdb`, `_1.pdb`, and so on.
- `inference.num_designs`: number of designs to sample.
- `inference.final_step`: final reverse-diffusion step; default is `1`.
- `inference.deterministic`: deterministic seed behavior for testing and debugging.
- `contigmap.contigs`: list containing the contig string.
- `contigmap.provide_seq`: optional zero-indexed inclusive sequence ranges to preserve.
- `diffuser.T`: default total timesteps, `50`.
- `diffuser.partial_T`: partial-diffusion noising depth; default is unset.

The installed `Diffuser` accepts `partial_T` along with diffusion schedule parameters including `T`, `b_0`, `b_T`, `min_sigma`, `max_sigma`, `min_b`, `max_b`, `schedule_type`, `so3_schedule_type`, `so3_type`, `crd_scale`, and `var_scale`.

## Workflow 1: Diversify a Monomer Backbone

Use this when the full input monomer should be partially diffused.

1. Count residues in the input PDB.
2. Build a fixed-length contig with that same length, such as `[79-79]` for a 79-residue PDB.
3. Pick a conservative initial `partial_T`, such as `10` under default `diffuser.T=50`.
4. Run a one-design deterministic smoke check.
5. Increase `inference.num_designs` after the smoke check succeeds.

Smoke command:

```bash
run_inference.py \
  inference.input_pdb=/path/to/monomer_79aa.pdb \
  inference.output_prefix=outputs/smoke/monomer_partial \
  'contigmap.contigs=[79-79]' \
  diffuser.partial_T=10 \
  inference.num_designs=1 \
  inference.deterministic=True \
  inference.final_step=8
```

Production command:

```bash
run_inference.py \
  inference.input_pdb=/path/to/monomer_79aa.pdb \
  inference.output_prefix=outputs/partial/monomer_partial \
  'contigmap.contigs=[79-79]' \
  diffuser.partial_T=10 \
  inference.num_designs=10
```

Validation:

- Confirm `outputs/partial/monomer_partial_0.pdb` and `.trb` exist.
- Confirm every output has 79 residues.
- Compare outputs to the input to confirm diversification is local enough for the task.
- If all outputs are too similar, sample a larger `diffuser.partial_T`.
- If outputs drift too far, sample a smaller `diffuser.partial_T`.

## Workflow 2: Diversify a Binder or Chain in Complex Context

Use this when an existing complex supplies both the designed chain and the partner context. Partial diffusion still requires the contig total to match the input length.

Example for a 100-residue binder plus a 150-residue target segment:

```bash
run_inference.py \
  inference.input_pdb=/path/to/binder_target_complex.pdb \
  inference.output_prefix=outputs/partial/binder_context \
  'contigmap.contigs=[100-100/0 B1-150]' \
  diffuser.partial_T=20 \
  inference.num_designs=10
```

Decision notes:

- `[100-100]` represents the designed/diversified chain length.
- `/0` inserts a chain break.
- `B1-150` maps a 150-residue target segment from the input PDB.
- Total length is 250 residues, so the input mapping must provide 250 residues.
- If the user wants target hotspot design rather than complex diversification, use a binder-design workflow first.

Validation:

- Confirm chain organization in output matches the intended binder/target split.
- Confirm the `.trb` mapping records the intended contig-derived positions.
- Confirm residue counts on both sides of the chain break are as expected.

## Workflow 3: Preserve a Peptide Sequence During Complex Diversification

Use this when the input complex includes a peptide whose sequence should remain fixed while coordinates are allowed to relax.

Example for a 172-residue scaffold and a 34-residue peptide:

```bash
run_inference.py \
  inference.input_pdb=/path/to/peptide_complex_ideal_helix.pdb \
  inference.output_prefix=outputs/partial/peptide_sequence_preserved \
  'contigmap.contigs=["172-172/0 34-34"]' \
  diffuser.partial_T=10 \
  inference.num_designs=10 \
  'contigmap.provide_seq=[172-205]'
```

Why the range is `172-205`:

- `provide_seq` is zero-indexed across the whole contig.
- The scaffold occupies positions `0` through `171`.
- The peptide occupies positions `172` through `205`.
- Ranges are inclusive.

Validation:

- Extract the output sequence for contig positions `172-205` and compare it to the input peptide sequence.
- Confirm the `.trb` config includes `contigmap.provide_seq` exactly as intended.
- Confirm model weights are present if RFdiffusion switches to a provide-seq-capable checkpoint.

## Workflow 4: Preserve Multiple Disjoint Sequence Ranges

Use comma-separated ranges when only selected positions should retain sequence identity.

```bash
run_inference.py \
  inference.input_pdb=/path/to/peptide_complex_ideal_helix.pdb \
  inference.output_prefix=outputs/partial/peptide_terminal_sequence_preserved \
  'contigmap.contigs=["172-172/0 34-34"]' \
  diffuser.partial_T=10 \
  inference.num_designs=10 \
  'contigmap.provide_seq=[172-177,200-205]'
```

Use this for cases such as preserving peptide termini while allowing the middle to redesign. Remember that ranges do not need to be on the same chain, but they are always global zero-indexed contig positions.

## Choosing partial_T

Start by deciding how much the design may move from the input:

- `partial_T=5-10`: conservative local diversification under default `T=50`.
- `partial_T=10-20`: moderate diversification; useful first sweep for many backbones and complexes.
- `partial_T` greater than `20`: stronger exploration, but higher risk of moving away from the starting fold or interface.

Always treat these as sampling parameters, not guarantees. Sweep different `partial_T` values for the specific problem.

## Hydra Quoting Rules

Use single quotes around contig and provide-seq overrides so the shell does not parse brackets, slashes, spaces, or commas:

```bash
'contigmap.contigs=[79-79]'
'contigmap.contigs=["172-172/0 34-34"]'
'contigmap.provide_seq=[172-177,200-205]'
```

If a contig element contains a space, keep the inner double quotes as shown in the peptide-complex examples.

## Output Inspection Checklist

For each completed run:

1. Find numbered output PDB files matching `inference.output_prefix`.
2. Find matching `.trb` metadata files.
3. Inspect the saved config in `.trb` for `diffuser.partial_T`, `contigmap.contigs`, and `contigmap.provide_seq`.
4. Count output residues and compare against the contig total.
5. Compare preserved sequence positions against the input sequence when `provide_seq` is used.
6. Inspect trajectories when `inference.write_trajectory=True` and structural drift is unexpected.

## Safe Smoke-Test Pattern

For command validation without a full trajectory, set deterministic mode, one design, and a shortened final step:

```bash
run_inference.py \
  inference.input_pdb=/path/to/input.pdb \
  inference.output_prefix=outputs/smoke/partial \
  'contigmap.contigs=[79-79]' \
  diffuser.partial_T=10 \
  inference.num_designs=1 \
  inference.deterministic=True \
  inference.final_step=8
```

The RFdiffusion test harness adapts example commands similarly by setting `inference.deterministic=True`, `inference.num_designs=1`, and for partial-diffusion examples `inference.final_step=partial_T-2`.
