# Macrocycle Troubleshooting

Use this guide when RFpeptides macrocycle command construction or RFdiffusion runtime behavior is suspicious.

## Cyclic Flag Problems

Symptom: the command runs like an ordinary non-cyclic peptide design.

Checks:

- Add `inference.cyclic=True`; the base config default is `False`.
- Keep `inference.cyc_chains='a'` for a single generated macrocycle.
- Confirm `inference.cyc_chains` is not accidentally omitted by a shell wrapper or scheduler.
- Do not use `inference.symmetry=c4` or similar symmetry flags for RFpeptides macrocycles; that is a different design mode.

Symptom: the wrong chain appears to be cyclized.

Checks:

- Verify chain ordering from the contig. In the RFpeptides binder pattern, the generated peptide segment comes first and is selected by `cyc_chains='a'`.
- Do not include target chain letters in `inference.cyc_chains`.
- For multi-cyclic-chain experiments, confirm every chain letter in `cyc_chains` corresponds to a generated chain created by the contig.

## Contig Parsing Errors

Symptom: Hydra or RFdiffusion reports malformed contigs or receives split command tokens.

Fixes:

- Quote the whole contig override: `'contigmap.contigs=[12-18 A3-117/0]'`.
- Keep the contig as a Hydra list with brackets.
- Use spaces inside the list only where RFdiffusion contig syntax expects separate segments.
- Do not write `contigmap.contigs=12-18`; use `'contigmap.contigs=[12-18]'`.

Symptom: binder command creates an unexpected target/binder layout.

Fixes:

- For macrocyclic binders, start from the RFpeptides pattern: generated peptide first, target segment second, `/0` chain break at the end.
- Use target PDB chain IDs and residue numbers exactly as present in the runtime PDB.
- Recheck any target crop, chain rename, or residue renumbering step before copying example contigs.

## Hotspot Formatting Errors

Symptom: shell parsing strips brackets, commas, or quotes from `ppi.hotspot_res`.

Fixes:

- Prefer single-quoting the full Hydra list: `'ppi.hotspot_res=[A51,A52,A50]'`.
- If the user's wrapper requires explicit quoted strings inside the Hydra list, use escaped entries: `ppi.hotspot_res=[\'A51\',\'A52\',\'A50\']`.
- Do not mix both forms in one command.

Symptom: RFdiffusion rejects or ignores hotspots.

Fixes:

- Ensure every hotspot is a target residue, not a generated peptide residue.
- Ensure every hotspot residue is included in the target contig span.
- Ensure the chain ID and residue number match the exact input PDB file, not a database PDB after renumbering.
- If using a GABARAP example derived from PDB ID `7zkr`, remember the repository example notes a `+2` chain A residue-number shift in its prepared input file.

## Numbering And Chain Caveats

Macrocycle binder failures often come from copying an example target without copying its numbering assumptions.

Ask:

- Was the target PDB cropped?
- Were residues renumbered from original PDB numbering?
- Were chain IDs changed by a preprocessing tool?
- Do hotspots refer to the original structure, the cropped file, or a visualization selection?

Correct the command against the exact runtime input PDB. The contig target span and `ppi.hotspot_res` must refer to the same file and numbering scheme.

## Diffusion Schedule And Model Setup

Symptom: results differ from RFpeptides examples or the command does not match expected macrocycle defaults.

Checks:

- RFpeptides examples use `--config-name base` and `diffuser.T=50`.
- Base config includes `diffuser.T: 50`, but specifying `diffuser.T=50` makes the command explicit and portable across edited configs.
- Confirm model weights are installed and discoverable, or pass `inference.model_directory_path=/path/to/models` if the user's installation requires it.
- Confirm the active Python environment can import `rfdiffusion` and its inference modules.

## Output Validation Issues

Symptom: files are missing.

Checks:

- `inference.output_prefix` is a prefix; RFdiffusion writes indexed files such as `design_0.pdb`, not a single file named exactly `design`.
- Existing outputs may be skipped when `inference.cautious=True`; choose a fresh prefix or set a new `inference.design_startnum`.
- If trajectories are disabled with `inference.write_trajectory=False`, only final outputs and metadata are expected.

Symptom: outputs exist but do not answer the design question.

Checks:

- Confirm the `.trb` resolved config contains `inference.cyclic=True`, intended `inference.cyc_chains`, and intended contig.
- For monomers, inspect the generated peptide backbone length against the requested range.
- For binders, inspect whether the peptide is near the target site and whether contacts are plausible around the hotspot region.
- Do not treat an RFdiffusion backbone as validated binding; use downstream sequence design and structure/interface assessment.

## Scope Boundaries

Route out of this sub-skill when:

- The user needs general non-cyclic binder hotspot strategy: use `binder-design`.
- The user wants cyclic or dihedral symmetric oligomers with symmetry groups: use symmetric oligomer guidance.
- The user wants to tune attraction, repulsion, or compactness potentials: use guided-potentials guidance.
- The user needs sequence design, AlphaFold-style validation, Rosetta metrics, or experimental prioritization: explain these are downstream assessment steps.
