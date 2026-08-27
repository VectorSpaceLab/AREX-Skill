# Enumeration Troubleshooting

## Config Fails Before Running

Symptoms:

- Pydantic or validation error about extra `[parameters]` keys.
- Config copied from an older example does not accept `amino_acid_library` or `amino_acid_name_column`.
- Runtime falls back to `nnaas.csv` and then reports a missing amino-acid library.

Fixes:

- Use current runtime key names: `amino_acid_library_file` and `aa_names_column`.
- Keep `smiles_file`, `amino_acid_library_file`, `aa_names_column`, `smiles_column`, `batch_size`, and `output_csv` under `[parameters]`.
- Keep scoring under `[scoring]`; do not place scoring component keys under `[parameters]`.
- Use `python sub-skills/enumeration/scripts/validate_seed_files.py enumeration.toml --kind enumeration` before launching the CLI.

## No Masks or Too Many Masks

Symptoms:

- `No masked amino acids found in the input peptide.`
- `Enumeration is limited to 2 or less masked amino acids.`
- Output rows still contain `?`.

Fixes:

- Ensure peptide templates contain `?` exactly where amino-acid fragments should be inserted.
- Keep runtime peptide enumeration to one or two masks per template.
- Use `|` as the peptide fragment separator around masked positions.
- For model-vocabulary or token-generation problems in PepInvent sampling, switch to the sibling `sampling` or `learning` sub-skill; enumeration does not train or sample model tokens.

## Amino-Acid Library Problems

Symptoms:

- Missing column errors from the CSV reader or pandas.
- Fewer rows than expected in the final output.
- Fillers are blank or peptide joins fail.

Fixes:

- Confirm the library CSV has the columns named by `aa_names_column` and `smiles_column`.
- Keep amino-acid names non-empty and unique; duplicate names collapse when the runtime builds its name-to-SMILES dictionary.
- Keep fragment SMILES non-empty and compatible with peptide insertion. Enumeration removes the final character of each library fragment before replacement, so fragment convention matters.
- Avoid using `RDKit_SMILES (REINVENT)` as `smiles_column`; it is reserved by REINVENT4 scoring output.

## Attachment-Point and Warhead Failures

Symptoms:

- LibInvent or LinkInvent seed checks fail before sampling.
- Joined library-design molecules are `None` or sanitization fails.
- LinkInvent rows produce mismatched warheads/linkers.

Fixes:

- LibInvent scaffold rows should include wildcard attachment points such as `*`, `[*]`, `[*:0]`, and `[*:1]`.
- LinkInvent rows must contain exactly one pipe separator between warheads.
- Each LinkInvent warhead side should usually contain exactly one attachment point.
- Do not use semicolons, commas, whitespace, or multiple pipes as the warhead separator.
- If keeping attachment labels for reaction filtering, avoid multiple attachment points on the same atom because label ambiguity can break downstream filtering.

## Output CSV Looks Wrong

Symptoms:

- `output_csv` is missing.
- Output row count is lower than `library_size ** mask_count`.
- Header is duplicated or old rows remain.
- `SMILES`, `Amino_Acids`, or `Score` columns are missing.

Fixes:

- Delete or rename an existing `output_csv` before rerunning unless appending is intentional.
- Check the log for invalid completed peptide SMILES filtered by validation or scoring errors.
- Confirm the first parsed template has the expected number of masks; current runtime builds the iterator from the first template row.
- Confirm the `[scoring]` block has at least one useful component when a meaningful `Score` is expected.
- Use the sibling `scoring` sub-skill if endpoint names, aggregation, transforms, external components, or plugin imports are the issue.

## Scoring Block Reuse Fails

Symptoms:

- Enumeration starts, then scoring component validation or plugin import fails.
- External scoring processes or REST components do not run.
- Optional chemistry/model packages are missing.

Fixes:

- First validate seed files and enumeration parameters so scoring is the only remaining failure surface.
- Reuse scoring blocks that already pass a standalone `run_type = "scoring"` smoke test on representative completed peptide SMILES.
- Move component-specific debugging to the sibling `scoring` sub-skill.
- If `reinvent --help` or config parsing fails while importing plotting utilities, ensure the runtime environment has the package dependencies required by the installed REINVENT4 distribution. In one inspection environment, `scipy` was needed because plotting imports `scipy.stats.gaussian_kde`.

## Wrong Workflow Routed Here

Use another sub-skill when the issue is not enumeration-specific:

- `sampling`: model/prior selection, `run_type = "sampling"`, LibInvent/LinkInvent/Mol2Mol/PepInvent generation, output sampling CSVs, invalid generated tokens.
- `scoring`: scoring components, transforms, aggregation, plugins, external processes, REST scoring, optional component dependencies.
- `learning`: transfer learning, staged reinforcement learning, agent checkpoints, model vocabulary drift, staged scoring reuse during optimization.
