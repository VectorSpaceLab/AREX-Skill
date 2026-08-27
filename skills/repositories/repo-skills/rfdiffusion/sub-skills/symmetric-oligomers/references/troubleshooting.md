# Symmetric Oligomer Troubleshooting

Use this reference to triage RFdiffusion symmetry-mode failures before escalating to motif-scaffolding, guided-potentials, macrocycle-design, or install-level troubleshooting.

## Unrecognized Or Invalid Symmetry

Symptoms:

- `ValueError: Unrecognized symmetry ...`.
- `ValueError: Invalid cyclic symmetry ...` or `Invalid dihedral symmetry ...`.
- A command works with `c6` but not with a misspelled point-group name.

Fixes:

- Use `C<n>` or `c<n>` for cyclic symmetry, such as `C6`.
- Use `D<n>` or `d<n>` for dihedral symmetry, such as `D2`; remember this creates `2*n` chains.
- Use the exact lowercase names `tetrahedral`, `octahedral`, or `icosahedral` for saved point groups.
- Do not write informal names such as `tet`, `icos`, `C_6`, or `dihedral2`.
- Prefer `tetrahedral` over `t3` unless intentionally using the code's four-rotation `T3` branch instead of the documented saved 12-rotation point group.

## Sequence Length Not Divisible

Symptoms:

- `ValueError: Sequence length must be divisble by ...`.
- `olig_contacts` asserts that total length is not divisible by chain count.
- Output chain lengths do not match expectations.

Fixes:

- Treat `contigmap.contigs` as total oligomer length, not per-chain length.
- Multiply per-chain length by symmetry chain count: `C6` uses `6 * L`, `D2` uses `4 * L`, `tetrahedral` uses `12 * L`, `octahedral` uses `24 * L`, and `icosahedral` uses `60 * L`.
- For ranges, make both bounds compatible or use an exact total length. A range that includes incompatible totals can fail depending on the sampled length.
- In motif scaffolding, verify every symmetric repeat has the same generated and motif residue counts.

## Forgot Symmetry Config

Symptoms:

- A symmetric oligomer command behaves like base monomer generation.
- Defaults such as output prefix or contig expectations do not match symmetry examples.
- The user passed `inference.symmetry` but omitted the symmetry config in a simple generation task.

Fixes:

- Add `--config-name=symmetry` for ordinary symmetric oligomer generation.
- Keep `inference.symmetry=<name>` explicit even when the symmetry config has a default `c2`.
- Advanced motif examples may set `inference.symmetry` without `--config-name=symmetry`, but then all needed base/symmetry overrides must be deliberate.

## Hydra Quoting Failures

Symptoms:

- Hydra reports malformed overrides for `contigmap.contigs` or `potentials.guiding_potentials`.
- The shell splits a motif contig at spaces or strips brackets.
- Contact potentials are not parsed as a list.

Fixes:

- Quote contig lists as one argument: `'contigmap.contigs=[480-480]'`.
- Quote nested potential lists with single quotes outside and double quotes inside: `'potentials.guiding_potentials=["type:olig_contacts,weight_intra:1,weight_inter:0.1"]'`.
- For symmetric motif contigs with chain-break spaces, keep the entire contig in one single-quoted argument.
- For non-Bash shells, adapt quote characters so Python receives the same literal strings.

## Oligomer Contact Potential Crashes

Symptoms:

- `NotImplementedError` from chain-count calculation.
- `RuntimeError: Unknown symmetry symbol` when combining `olig_contacts` with `icosahedral`.
- Assertion errors from contact matrix shape or entries.

Fixes:

- Use documented `olig_contacts` examples first for `C*`, `D*`, or `tetrahedral`.
- Avoid promising `olig_contacts` for `octahedral` or `icosahedral` unless the user's installed RFdiffusion has extended `calc_nchains` support.
- Ensure `potentials.olig_intra_all=True` and `potentials.olig_inter_all=True` are present when using the all-to-all example pattern.
- If the user wants custom contact topology, route detailed matrix design and tuning to guided-potentials.
- Reduce `potentials.guide_scale` or weights if structures become distorted; the README recommends starting from no potentials or weak documented defaults before tuning upward.

## Symmetric Motif PDB Is Not Symmetric

Symptoms:

- Motif copies drift or appear at unexpected axes.
- Diffusion fails after centering the motif.
- The output is asymmetric even though `inference.symmetry` was set.

Fixes:

- Require an input PDB containing all motif copies already arranged in the intended symmetry.
- For cyclic symmetry, align the symmetry axis to `Z`.
- For dihedral symmetry, align the cyclic axis to `Z` and the flip/reflection axis to `X`.
- Do not provide only one asymmetric motif copy and expect RFdiffusion to generate the rest safely.
- Confirm the contig repeats motif spans and generated lengths precisely across all symmetric copies.
- Route residue-selection, inpainting, and active-site checkpoint questions to motif-scaffolding once the symmetric input requirement is satisfied.

## Missing Motif Residues Or Bad Contig Spans

Symptoms:

- RFdiffusion reports missing chain/residue references.
- A nickel-style contig fails before diffusion starts.
- The output has an unexpected chain layout.

Fixes:

- Confirm every chain and residue range in the contig exists in `inference.input_pdb`.
- Use inclusive residue ranges, such as `A2-4` for residues 2, 3, and 4 on chain `A`.
- Keep repeated symmetric motif blocks equivalent in length and arrangement.
- Preserve chain-break spaces inside the quoted contig when separating repeated motif copies.

## Memory Or Runtime Problems

Symptoms:

- Large point-group jobs run out of GPU memory.
- High-order cyclic, octahedral, or icosahedral jobs are much slower than expected.
- Trajectory files consume excessive storage.

Fixes:

- Start with `inference.num_designs=1` and shorter chain lengths.
- Disable trajectories for checks with `inference.write_trajectory=False`.
- Treat `inference.model_only_neighbors=True` as version-dependent; in this checkout it is exposed and passed into `SymGen`, but no active neighbor-reduction behavior is visible in the inspected helper.
- Test smaller point groups or per-chain lengths before scaling to production.
- Keep `inference.cautious=True` and use fresh output prefixes to avoid wasting time on skipped outputs.

## Output Validation Finds Wrong Chain Count

Symptoms:

- The PDB has fewer or more chains than expected.
- Chains have unequal residue counts for an unconditional symmetric oligomer.
- The user counted residues per chain and thinks the design is too long.

Fixes:

- Recompute expected chain count from `inference.symmetry` and compare against the PDB chain labels.
- Remember that the contig is total length; per-chain length is total divided by chain count.
- Inspect the `.trb` resolved config for the actual `contigmap.contigs` and `inference.symmetry` used.
- Check logs for cautious-mode skips, because an old output can be mistaken for the new command's output.

## Installed Package Or Model Problems

Symptoms:

- `ModuleNotFoundError: rfdiffusion`, `No module named se3_transformer`, or PyTorch backend errors.
- Checkpoint file not found.
- The first run appears to stall while schedules are computed.

Fixes:

- Verify the active environment imports `rfdiffusion`, `rfdiffusion.inference.utils`, and `rfdiffusion.inference.symmetry`.
- Confirm RFdiffusion model weights are installed and pass `inference.model_directory_path=/path/to/models` when defaults fail.
- Use `inference.ckpt_override_path=/path/to/checkpoint.pt` only when the workflow calls for a specific checkpoint.
- First-run IGSO3 schedule calculation and caching can be slow; use a writable location and a one-design smoke command to validate setup.
