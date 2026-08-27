# CLI Reference

This reference summarizes the user-facing `openfe` command tree and safe command patterns. Use `openfe --help` and `openfe <command> --help` to verify the installed command surface before running expensive commands.

## Global Command Rules

- Main shape: `openfe [GLOBAL_OPTIONS] COMMAND [COMMAND_OPTIONS] [ARGS]`.
- `--version` prints the installed OpenFE CLI version.
- `--log PATH` loads a logging configuration file and must be placed before the subcommand: `openfe --log logging.conf quickrun transformation.json -d work -o result.json`.
- `-h` and `--help` are safe at both global and subcommand levels.
- Planning, charge generation, fetching, tests, and `quickrun` can create files, download data, or run expensive computations; ask before running them.

## Command Families

The top-level help groups commands into `Network Planning Commands`, `Quickrun Executor Commands`, and `Miscellaneous Commands`.

| Command | Help section | Purpose | Usually safe to run? | Primary outputs |
| --- | --- | --- | --- | --- |
| `openfe plan-rbfe-network` | Network Planning | Plan a relative binding free energy campaign from ligands plus protein or protein-membrane input. | No; parses inputs, charges molecules, writes output directories. | Network JSON, `ligand_network.graphml`, and per-edge transformation JSONs. |
| `openfe plan-rhfe-network` | Network Planning | Plan a relative hydration free energy campaign from ligand inputs. | No; parses inputs, charges molecules, writes output directories. | Network JSON, `ligand_network.graphml`, and per-edge transformation JSONs. |
| `openfe view-ligand-network` | Network Planning | Display a ligand network from GraphML. | Opens a GUI window; not useful in headless sessions. | Interactive plot window. |
| `openfe quickrun` | Quickrun Executor | Execute one transformation JSON and write one result JSON. | No; runs simulations and writes work/cache/result files. | Result JSON plus work/cache files. |
| `openfe gather` | Quickrun Executor | Gather RBFE result JSONs into TSV-style summaries. | Usually read-mostly, but writes/prints summaries depending options. | RBFE DG/DDG/raw summary tables. |
| `openfe gather-abfe` | Quickrun Executor | Experimental ABFE result gatherer. | Usually read-mostly, but experimental. | ABFE DG/raw summary tables. |
| `openfe gather-septop` | Quickrun Executor | Experimental SepTop result gatherer. | Usually read-mostly, but experimental. | SepTop DG/DDG/raw summary tables. |
| `openfe fetch` | Miscellaneous | Fetch tutorial or resource data. | Not always; some resources require internet and write files/cache. | Resource files. |
| `openfe test` | Miscellaneous | Run OpenFE and OpenFE CLI tests. | Potentially slow; `--long` is much slower. | Pytest output; optional downloaded test cache. |
| `openfe charge-molecules` | Miscellaneous | Generate partial charges and write a charged ligand SDF. | No; may be slow and refuses existing output file. | Charged SDF file. |

## Planning Commands

### `plan-rbfe-network`

Use RBFE planning for ligand transformations in a protein or protein-membrane context.

Common shape:

```bash
openfe plan-rbfe-network \
  -M ligands.sdf \
  -p protein.pdb \
  -o network_setup \
  --n-protocol-repeats 3
```

Important options:

- `-M, --molecules PATH`: required; SDF/MOL2 file or directory containing ligand files.
- `-p, --protein PATH`: PDB, PDBx, or mmCIF protein file.
- `--protein-membrane PATH`: fully solvated protein-membrane input; mutually exclusive with `--protein`.
- `-C, --cofactors PATH`: optional SDF cofactor file; can be supplied more than once.
- `-s, --settings PATH`: YAML planner settings for mapper, network planner, and partial charge options.
- `-o, --output-dir PATH`: output directory; default is `alchemicalNetwork`.
- `--n-protocol-repeats INT`: independent repeats to run per transformation execution; use `1` when planning repeats for separate parallel quickrun jobs.
- `-n, --n-cores INT`: multiprocessing cores for charge generation.
- `--overwrite-charges`: replace existing partial charges in input molecules.

Rules:

- Provide exactly one of `--protein` or `--protein-membrane`.
- Planning assigns ligand partial charges before building the network, which can be slow.
- Output directories are created if needed; choose a fresh directory when you want an unambiguous campaign.

### `plan-rhfe-network`

Use RHFE planning for hydration-only ligand transformations.

Common shape:

```bash
openfe plan-rhfe-network \
  -M ligands.sdf \
  -o hydration_network \
  --n-protocol-repeats 3
```

Important options:

- `-M, --molecules PATH`: required; SDF/MOL2 file or directory containing molecules.
- `-s, --settings PATH`: YAML planner settings.
- `-o, --output-dir PATH`: output directory; default is `alchemicalNetwork`.
- `--n-protocol-repeats INT`: independent repeats to run per transformation execution.
- `-n, --n-cores INT`: multiprocessing cores for charge generation.
- `--overwrite-charges`: replace existing partial charges.

## Planning YAML

Planner YAML can include any of these optional top-level sections:

```yaml
mapper:
  method: KartografAtomMapper
  settings:
    atom_max_distance: 0.95
network:
  method: generate_minimal_spanning_network
partial_charge:
  method: am1bcc
  settings:
    off_toolkit_backend: ambertools
```

Supported mapper aliases include `KartografAtomMapper`, `kartograf`, `LomapAtomMapper`, and `lomap`. Supported network choices include `generate_minimal_spanning_network`, `mst`, `generate_minimal_redundant_network`, `generate_radial_network`, `radial`, `generate_lomap_network`, and `generate_maximal_network`. Supported partial charge methods include `am1bcc`, `am1bccelf10`, `nagl`, and `espaloma`; optional backends and models depend on the installed environment.

If YAML parsing or option resolution fails, check indentation, top-level section names, method spelling, and whether optional charge backends are installed.

## Quickrun

Common shape:

```bash
openfe quickrun network_setup/transformations/edge.json \
  -d work/edge \
  -o results/edge_results.json
```

Options:

- Positional `TRANSFORMATION`: a transformation JSON produced by a planner command or by the Python API.
- `-d, --work-dir DIRECTORY`: work/cache/checkpoint directory; created if it does not exist; current directory is used when omitted.
- `-o PATH`: result JSON output path; parent directories are created if needed; default is `<transformation_key>_results.json` inside the work directory; an existing output file is rejected with a Click file error.
- `--resume`: attempt to resume from the quickrun cache for the same transformation and output path.

`quickrun` prints a resume command at startup. Preserve the same transformation file, `-d`, and `-o` values if using `--resume` later.

## Gather Commands

Use gather commands after `quickrun` has produced result JSONs.

- `openfe gather RESULTS...`: intended for RBFE results; `--report` accepts `dg`, `ddg`, or `raw`.
- `openfe gather-abfe RESULTS...`: experimental ABFE gatherer; `--report` accepts `dg` or `raw`.
- `openfe gather-septop RESULTS...`: experimental SepTop gatherer; `--report` accepts `dg`, `ddg`, or `raw`.
- `RESULTS` can be one or more files or directories; directories are walked recursively and invalid/non-result JSONs are ignored.
- `-o PATH` writes TSV output to a file, `--tsv` makes stdout tab-separated instead of human-readable, and `--allow-partial` skips missing result parts with warnings instead of failing.

Report modes and exact TSV schemas belong in `../../results-analysis/SKILL.md`. In CLI workflow tasks, focus on choosing the right gather command and pointing it at the root containing result JSONs or repeat folders.

## Charge, View, Fetch, and Test

### `charge-molecules`

```bash
openfe charge-molecules -M ligands.sdf -o charged_ligands.sdf -n 4
```

- Reads SDF/MOL2 ligand input from a file or directory.
- Uses optional `-s, --settings PATH` YAML; only `partial_charge` settings are relevant.
- Refuses to overwrite an existing output file; choose a new `-o` path.
- `--overwrite-charges` overwrites partial charges already present in input molecules.

### `view-ligand-network`

```bash
openfe view-ligand-network network_setup/ligand_network.graphml
```

This expects a GraphML ligand network and opens an interactive plot. In headless environments, inspect the file path or use non-GUI analysis instead of running the viewer.

### `fetch`

`openfe fetch` has nested resource commands. Use `openfe fetch --help` to list installed fetchables. Some fetchables require internet or write cache files, so ask before running.

### `test`

```bash
openfe test
openfe test --download-only
openfe test --long
```

- `openfe test` imports OpenFE and runs the main OpenFE/OpenFE CLI test suites; it is a minutes-scale validation command, not a cheap smoke check.
- `--download-only` checks/downloads test data cache without running tests.
- `--long` enables additional slow tests through `OFE_SLOW_TESTS`; avoid it for quick smoke checks unless the user requests deep validation.
