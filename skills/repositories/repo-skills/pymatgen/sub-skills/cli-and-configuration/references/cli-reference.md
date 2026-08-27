# pymatgen CLI Reference

This reference summarizes the pymatgen console scripts and `pmg` subcommands verified from the package entry points and CLI source. The console scripts are `pmg`, `get_environment`, `feff_plot_cross_section`, and `feff_plot_dos`. Use [../scripts/pmg_help_probe.py](../scripts/pmg_help_probe.py) for safe help discovery in the active environment.

## Safety Classes

| Class | Examples | Run Without Approval? | Notes |
| --- | --- | --- | --- |
| Help only | `pmg --help`, `pmg structure --help`, `feff_plot_dos --help` | Yes | Does not read user data, mutate config, access APIs, scan directories, or open plots. |
| Redacted environment probe | `python scripts/pymatgen_environment_probe.py` | Yes | Checks imports, versions, entry points, and console scripts while hiding local paths by default. |
| Local file read | `pmg diff --incar A B`, `pmg structure --symmetry 0.1 --filenames a.cif` | Ask for user-owned data | Reads files and may expose derived scientific data in output. |
| Local file write | `pmg structure --convert --filenames in.cif out.POSCAR`, `pmg plot --xrd in.cif --out_file xrd.png` | Ask | Confirm target path and overwrite behavior. |
| Config mutation | `pmg config --add ...`, `pmg config -p ...`, `pmg config --cp2k ...` | No | Rewrites `.pmgrc.yaml` or creates resource directories. |
| Licensed resource write | `pmg potcar --symbols ...`, `pmg potcar --recursive DIR` | No | Requires licensed VASP pseudopotentials and writes `POTCAR`. |
| Network/API | `pmg query ...` | No | Requires Materials Project credentials and network. Route details to `external-data-access`. |
| GUI/display | `pmg view ...`, plotting without `--out_file`, FEFF plotting helpers | Ask | May need VTK, matplotlib display, or user FEFF files. |
| Recursive scan | `pmg analyze DIR`, `pmg potcar --recursive DIR` | Ask | May traverse many directories and write caches or generated files. |

## Top-Level `pmg`

`pmg` is a master CLI with subcommands. Always inspect `pmg <subcommand> --help` before composing commands in an unfamiliar environment.

Current subcommands:

- `config`: configure pymatgen settings, POTCAR resources, CP2K resource data, or optional external tools.
- `analyze`: inspect VASP calculation directories for energies or magnetizations.
- `query`: search Materials Project structures, entries, or summary data.
- `plot`: plot DOS, charge integration, or XRD from local files.
- `structure`: convert, group, or analyze structure files.
- `view`: open a VTK structure viewer.
- `diff`: compare INCAR files.
- `potcar`: generate POTCAR files from configured resources.

## `pmg config`

`pmg config` requires exactly one of these mutually exclusive actions:

- `-p INPUT_PSP_DIR OUTPUT_PSP_DIR`, `--potcar INPUT_PSP_DIR OUTPUT_PSP_DIR`: copy and reformat licensed VASP POTCAR resources into a pymatgen-compatible resource directory. It may decompress, rename, recompress, and copy POTCAR files. It prompts if the destination directory exists.
- `-i enumlib`, `--install enumlib`: build enumlib external tools. This can run compilers, clone/download code, and alter files in the working directory.
- `-i bader`, `--install bader`: build the Bader executable. This can download archives, run compilers, and alter files in the working directory.
- `-a KEY VALUE [KEY VALUE ...]`, `--add KEY VALUE [KEY VALUE ...]`: add or update config variables. The token count must be even because every key needs a value. String values `true`, `false`, `none`, and `null` are converted to booleans/null.
- `--cp2k INPUT_DATA_DIR OUTPUT_DATA_DIR`: generate CP2K YAML data resources from CP2K basis and potential files. It prompts if the destination directory exists.

Additional option:

- `-b SUFFIX`, `--backup SUFFIX`: suffix used when backing up an existing `.pmgrc.yaml`; default is `.bak`. An empty suffix disables backup and should not be used unless the user explicitly requests it.

Never run non-help `pmg config` without confirming the exact variables, values, target paths, backup behavior, and licensing implications. See [configuration.md](configuration.md).

## `pmg analyze`

Syntax surface:

- Positional `directories`: directories to process; defaults to `.`.
- `-e`, `--energies`: print VASP energies. This is also the default when no energy/magnetization mode is selected.
- `-m ION_LIST`, `--mag ION_LIST`: print OUTCAR magnetizations for a range like `1-2`. The help mentions `All`, but the current handler is safer with explicit ranges.
- `-r`, `--reanalyze`: force reanalysis instead of reusing `vasp_data.gz`.
- `-f FORMAT`, `--format FORMAT`: table format from `tabulate`.
- `-v`, `--verbose`: enable progress logging.
- `-q`, `--quick`: parse individual VASP files for a faster, less detailed analysis.
- `-s energy_per_atom|filename`, `--sort energy_per_atom|filename`: sort output; default is `energy_per_atom`.

Safety notes:

- The energy workflow may recursively assimilate VASP directories and write or reuse `vasp_data.gz` in the working directory.
- The magnetization workflow scans OUTCAR-like files under the requested directory.
- Ask before running on user directories, especially broad roots. Route VASP/Borg assimilation concepts to [../../entries-thermodynamics-and-batteries/SKILL.md](../../entries-thermodynamics-and-batteries/SKILL.md).

## `pmg query`

Syntax surface:

- Positional `criteria`: formula, chemical system, Materials Project id, or another supported search criterion.
- Exactly one output mode is required:
  - `-s poscar|cif|cssr`, `--structure poscar|cif|cssr`: fetch structures and write them in the chosen format.
  - `-e FILENAME`, `--entries FILENAME`: fetch entries and serialize them to JSON or YAML.
  - `-d [FIELDS ...]`, `--data [FIELDS ...]`: print summary data; default fields include Materials Project id, formula, space group, energy per atom, and energy above hull.

Safety notes:

- This is a live Materials Project workflow requiring network access and an API key such as `PMG_MAPI_KEY`.
- Do not echo API keys. Route query planning, endpoint fields, pagination, and credential diagnosis to [../../external-data-access/SKILL.md](../../external-data-access/SKILL.md).

## `pmg plot`

`pmg plot` requires exactly one data source:

- `-d vasprun.xml`, `--dos vasprun.xml`: plot DOS from `Vasprun(...).complete_dos`.
- `-c CHGCAR`, `--chgint CHGCAR`: plot integrated charge from a CHGCAR-like file.
- `-x structure_file`, `--xrd structure_file`: plot XRD from a supported structure file using `XRDCalculator`.

Optional flags:

- `-s`, `--site`: plot site-projected DOS for DOS workflows.
- `-e Fe,Mn`, `--element Fe,Mn`: plot selected element-projected DOS.
- `-o`, `--orbital`: plot orbital-projected DOS.
- `-i 1,2,3`, `--indices 1,2,3`: atom indices for charge integration; without this, symmetry-distinct sites are selected.
- `-r RADIUS`, `--radius RADIUS`: charge-integration radius; default is `3`.
- `--out_file output.png`: save the figure instead of opening a display window.

Safety notes:

- Prefer `--out_file` in headless environments.
- Without `--out_file`, matplotlib attempts to show a window.
- Route plot interpretation, diffraction details, FEFF spectra, and API alternatives to [../../spectra-diffraction-and-visualization/SKILL.md](../../spectra-diffraction-and-visualization/SKILL.md).

## `pmg structure`

`pmg structure` takes `-f/--filenames filename [filename ...]` and exactly one operation:

- `-c`, `--convert`: convert structure file 1 to structure file 2. Format is inferred from filenames. If the output filename contains `prim`, pymatgen attempts a primitive cell. This writes the output file.
- `-s TOLERANCE`, `--symmetry TOLERANCE`: print space-group information for each input structure; `0.1` is a common DFT tolerance.
- `-g element|species`, `--group element|species`: group structures by similarity. `element` ignores oxidation states; `species` considers species/oxidation states. Requires at least two structures.
- `-l Center-Ligand=max_dist [Center-Ligand=max_dist ...]`, `--localenv ...`: print neighbor distances matching center/ligand bond specifications.

Safety notes:

- Conversion writes an output file and should be planned with explicit source/destination paths.
- Symmetry, group, and local-environment outputs are summaries over user structure files; route interpretation to [../../structures-local-environments-and-transformations/SKILL.md](../../structures-local-environments-and-transformations/SKILL.md).
- For a conversion plan, verify that the input filename extension is supported by `Structure.from_file()` and the output extension is supported by `Structure.to()` before running.

## `pmg view`

Syntax surface:

- `pmg view filename`
- `pmg view filename -e Li,Na`, `pmg view filename --exclude_bonding Li,Na`

Safety notes:

- Loads the structure file and opens `StructureVis` from `pymatgen.vis.structure_vtk`.
- Requires optional visualization dependencies such as VTK and a display-capable environment.
- Ask before running; avoid on headless servers unless display forwarding and visualization dependencies are confirmed.

## `pmg diff`

Syntax surface:

- `pmg diff -i INCAR1 INCAR2`, `pmg diff --incar INCAR1 INCAR2`

Safety notes:

- The current implementation supports INCAR diffs only.
- It reads both files and prints same/different parameter tables; it does not write output files.
- After confirming the two input files, this is one of the safest non-help `pmg` commands.

## `pmg potcar`

Syntax surface:

- Optional `-f FUNCTIONAL`, `--functional FUNCTIONAL`: choose a POTCAR functional. If omitted, pymatgen uses `PMG_DEFAULT_FUNCTIONAL` from settings, then falls back to `PBE`.
- Exactly one generation mode is required:
  - `-s SYMBOL [SYMBOL ...]`, `--symbols SYMBOL [SYMBOL ...]`: generate a `POTCAR` in the current directory from requested symbols.
  - `-r DIR`, `--recursive DIR`: recurse through `DIR`, find `POTCAR.spec`, and write sibling `POTCAR` files.

Safety notes:

- Requires a correctly configured `PMG_VASP_PSP_DIR` pointing to licensed VASP pseudopotential resources.
- Writes files named `POTCAR`; recursive mode can write many of them.
- Do not run without explicit user approval, target-directory confirmation, and licensing acknowledgement.

## `get_environment`

The `get_environment` console script launches a ChemEnv command-line workflow.

Flags:

- `-s`, `--setup`: set up ChemEnv package configuration, including Materials Project access, ICSD database access, and package options. This may prompt and mutate configuration.
- `-m LEVEL`, `--message-level LEVEL`: message level; accepted values documented by help are `DEBUG`, `INFO`, `WARNING`, `ERROR`, and `CRITICAL`. Default is `WARNING`.

Safety notes:

- `get_environment --help` is safe.
- `get_environment --setup` is mutating/interactive and requires approval.
- Without `--setup`, the script still enters the ChemEnv computation flow and can prompt for user input; prefer API workflows in [../../structures-local-environments-and-transformations/SKILL.md](../../structures-local-environments-and-transformations/SKILL.md) unless the user specifically wants the interactive CLI.

## FEFF Plotting Console Scripts

`feff_plot_dos`:

- Positional `filename`: FEFF LDOS file set to plot.
- Positional `filename1`: `feff.inp` input file.
- `-s`, `--site`: plot site-projected DOS.
- `-e`, `--element`: plot element-projected DOS.
- `-o`, `--orbital`: plot orbital-projected DOS.
- Opens a matplotlib plot; no CLI `--out_file` is exposed.

`feff_plot_cross_section`:

- Positional `filename`: `xmu` file to plot.
- Positional `filename1`: `feff.inp` file to import.
- Opens a matplotlib plot; no CLI `--out_file` is exposed.

Safety notes:

- These scripts read FEFF output files and display plots; they do not run FEFF.
- For headless workflows, prefer API-level plotting guidance in [../../spectra-diffraction-and-visualization/SKILL.md](../../spectra-diffraction-and-visualization/SKILL.md).

## Safe Planning Patterns

### POTCAR Configuration Request

When a user asks to configure POTCARs, do not immediately run `pmg config -p` or `pmg potcar`. First produce a plan:

1. Confirm the user has licensed VASP pseudopotentials.
2. Confirm source and destination resource directories.
3. Explain that `pmg config -p` copies/transforms POTCAR files and may prompt if the destination exists.
4. Decide whether to persist `PMG_VASP_PSP_DIR` with `pmg config --add` and what backup suffix to use.
5. After approval, run the exact command from the intended working directory.

### Structure Conversion Request

For `pmg structure --convert`, plan before running:

1. Identify input file and output file.
2. Confirm the input exists and format is supported by `Structure.from_file()`.
3. Confirm the output extension and overwrite behavior.
4. Use `pmg structure --convert --filenames input output` only after the output path is approved.
5. If the input format is missing or ambiguous, ask for the file or route to Python API inspection in [../../structures-local-environments-and-transformations/SKILL.md](../../structures-local-environments-and-transformations/SKILL.md).
