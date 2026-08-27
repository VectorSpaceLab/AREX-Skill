# CLI and Configuration Troubleshooting

Use this reference for predictable CLI/configuration failures. Start with read-only checks unless the user has already approved a specific mutation.

## Missing Console Scripts

Symptoms:

- `pmg: command not found`
- `get_environment: command not found`
- `feff_plot_dos: command not found`
- `feff_plot_cross_section: command not found`

Likely causes:

- `pymatgen` is not installed in the active Python environment.
- Console-script entry points are not on `PATH`.
- Only a core package subset is available while the full distribution entry points are missing.
- The shell is not using the Python environment where pymatgen was installed.

Safe checks:

```bash
python scripts/pymatgen_environment_probe.py
python scripts/pmg_help_probe.py --commands pmg get_environment feff_plot_dos feff_plot_cross_section
```

Recovery:

- If imports fail, install or activate the intended pymatgen environment.
- If imports pass but scripts are missing from `PATH`, use the correct environment activation or reinstall the full package entry points.
- Use `--reveal-paths` on `pymatgen_environment_probe.py` only for private debugging when local executable paths are acceptable.

## Config Mutation Risk

Symptoms:

- User asks to run `pmg config --add ...`.
- A `.pmgrc.yaml` or backup file unexpectedly appears.
- Wrong config value was persisted.

Likely causes:

- `pmg config --add` rewrites the config file.
- Default backup suffix `.bak` was used.
- A command used the active user's real config instead of an isolated `PMG_CONFIG_FILE`.

Recovery:

- Stop before additional mutation.
- Identify the intended config location without leaking full local paths in public output.
- Restore from the backup if appropriate.
- For experimentation, use a user-approved temporary config via `PMG_CONFIG_FILE` rather than the default config file.
- Re-run `pmg config --add` only after confirming exact values and backup behavior.

## POTCAR Licensing and Directory Layout

Symptoms:

- `pmg potcar --symbols ...` cannot find POTCAR data.
- `pmg config -p ...` does not create the expected resource tree.
- VASP input generation complains about missing POTCARs.
- POTCAR hash or compatibility checks fail.

Likely causes:

- `PMG_VASP_PSP_DIR` is unset or points at the wrong directory.
- The source directory is not an extracted licensed VASP pseudopotential tree.
- `PMG_DEFAULT_FUNCTIONAL` does not match available resource subdirectories.
- POTCAR checks were disabled and masked an earlier path/metadata issue.

Recovery:

- Confirm the user has licensed VASP pseudopotentials; never request or display real POTCAR contents.
- Use `pmg config -p INPUT_PSP_DIR OUTPUT_PSP_DIR` only after approval.
- Set `PMG_VASP_PSP_DIR` only after the resource directory is known to be pymatgen-compatible.
- Avoid `PMG_POTCAR_CHECKS=false` unless the user explicitly accepts global validation risk.
- Route VASP entry compatibility semantics to [../../entries-thermodynamics-and-batteries/SKILL.md](../../entries-thermodynamics-and-batteries/SKILL.md).

## API Key Handling

Symptoms:

- `pmg query` fails authentication.
- User asks where to set a Materials Project API key.
- Logs or commands risk exposing `PMG_MAPI_KEY`.

Recovery:

- Do not ask the user to paste an API key into chat unless there is no alternative.
- Prefer a session environment variable for one-off work.
- Persist with `pmg config --add PMG_MAPI_KEY <redacted-api-key>` only after approval.
- Redact key values in all summaries and transcripts.
- Route endpoint fields, pagination, rate limits, and network failures to [../../external-data-access/SKILL.md](../../external-data-access/SKILL.md).

## Missing VASP Files

Symptoms:

- `pmg analyze` prints `No valid vasp run found.`
- `pmg plot --dos` cannot read `vasprun.xml`.
- `pmg plot --chgint` cannot read `CHGCAR`.
- `pmg diff --incar` cannot read one of the INCAR files.

Likely causes:

- Command is running from the wrong directory.
- Required VASP output files are absent, compressed unexpectedly, or incomplete.
- `pmg analyze` was pointed at a broad or unrelated directory tree.
- `pmg analyze` cache `vasp_data.gz` is stale or not writable.

Recovery:

- Confirm filenames and working directory before running.
- For `pmg analyze`, ask before scanning and use the narrowest calculation directory.
- Use `--quick` only when the user accepts less detailed parsing.
- Use `--reanalyze` only when the user agrees to refresh cached analysis.
- For analysis interpretation, route to [../../entries-thermodynamics-and-batteries/SKILL.md](../../entries-thermodynamics-and-batteries/SKILL.md).

## FEFF File Absence or Plot Failures

Symptoms:

- `feff_plot_dos` cannot load LDOS files.
- `feff_plot_cross_section` cannot load `xmu.dat`.
- FEFF helper opens or hangs on a plot window.

Likely causes:

- Required FEFF output files or `feff.inp` are missing.
- The command was run from the wrong FEFF calculation directory.
- No display-capable matplotlib backend is available.

Recovery:

- Confirm `feff.inp` and the relevant LDOS or `xmu` files exist.
- Use the FEFF helpers only for user-approved local files.
- For headless plotting, prefer API-level plotting from [../../spectra-diffraction-and-visualization/SKILL.md](../../spectra-diffraction-and-visualization/SKILL.md) because the FEFF console scripts do not expose `--out_file`.

## Headless Plotting and GUI Commands

Symptoms:

- `pmg view` fails importing VTK.
- Plot commands hang or error with display/backend messages.
- Figures do not appear on a remote server.

Recovery:

- Prefer `pmg plot ... --out_file output.png` where available.
- Set a noninteractive matplotlib backend in scripts before plotting.
- Avoid `pmg view` unless VTK and a display are confirmed.
- For visualization alternatives, route to [../../spectra-diffraction-and-visualization/SKILL.md](../../spectra-diffraction-and-visualization/SKILL.md).

## Dangerous Recursive Scans

Symptoms:

- User asks to run `pmg analyze /` or a large home/project directory.
- User asks to run `pmg potcar --recursive` over a broad tree.
- Command becomes slow or writes many files.

Recovery:

- Stop and ask for a narrow target directory.
- Explain expected side effects: `pmg analyze` may write `vasp_data.gz`; `pmg potcar --recursive` writes `POTCAR` next to each `POTCAR.spec`.
- Prefer listing or checking the target tree first with user approval.
- Never run recursive POTCAR generation without confirming licensed resources and write locations.

## `pmg structure --convert` Input Problems

Symptoms:

- Conversion fails with “Error converting file” or parser exceptions.
- User did not specify input or output format.
- Output file extension is ambiguous.

Recovery:

- Ask for both input and output filenames.
- Confirm the input file exists and is a structure format supported by `Structure.from_file()`.
- Confirm output extension and overwrite behavior.
- If the user needs deeper format/API debugging, route to [../../structures-local-environments-and-transformations/SKILL.md](../../structures-local-environments-and-transformations/SKILL.md).

## Local Validation Boundary

Use the bundled help and environment probes for ordinary skill use. Original repository CLI tests are evidence for this guidance, but they are not runtime dependencies and should not be required for user workflows.
