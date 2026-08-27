---
name: cli-and-configuration
description: "Use pymatgen command-line tools and persistent configuration
  safely, including pmg subcommands, POTCAR setup, Materials Project keys, FEFF
  helpers, and redacted environment probes."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# CLI and Configuration

Use this sub-skill when a task is about `pmg`, `pmg config`, `pmg analyze`, `pmg query`, `pmg plot`, `pmg structure`, `pmg view`, `pmg diff`, `pmg potcar`, `get_environment`, FEFF plotting console scripts, `.pmgrc.yaml`, `PMG_CONFIG_FILE`, `PMG_MAPI_KEY`, `PMG_VASP_PSP_DIR`, `PMG_POTCAR_CHECKS`, `PMG_DEFAULT_FUNCTIONAL`, or `PMG_CP2K_DATA_DIR`.

## Read First

- Read [references/cli-reference.md](references/cli-reference.md) for exact command flags, file expectations, and safe-versus-mutating command classification.
- Read [references/configuration.md](references/configuration.md) before changing `.pmgrc.yaml`, using `PMG_CONFIG_FILE`, saving a Materials Project key, configuring POTCAR paths, or generating CP2K data resources.
- Read [references/troubleshooting.md](references/troubleshooting.md) when console scripts are missing, config changes are risky, POTCAR resources are unavailable, credentials fail, VASP/FEFF files are absent, plotting is headless, or recursive scans could be dangerous.

## Bundled Safe Probes

- Run [scripts/pmg_help_probe.py](scripts/pmg_help_probe.py) to call only `--help` for known pymatgen console scripts and `pmg` subcommands; it does not mutate config, access the network, open GUIs, scan user directories, or touch POTCAR data.
- Run [scripts/pymatgen_environment_probe.py](scripts/pymatgen_environment_probe.py) for redacted distribution, import, entry-point, and console-script checks; local executable paths are hidden unless the user explicitly asks for private debugging with `--reveal-paths`.

## Safety Policy

- Safe without extra approval: `--help` checks, redacted import/version checks, and entry-point discovery.
- Ask before running commands that mutate `.pmgrc.yaml`, create/copy resource files, write `POTCAR`, save output files, read credentials, access Materials Project, recursively scan calculation directories, open a GUI, or inspect large user directory trees.
- Use `pmg plot ... --out_file ...` instead of display windows whenever possible, and avoid `pmg view` on headless systems unless the user confirms visualization support.
- For query semantics and network behavior, route to [../external-data-access/SKILL.md](../external-data-access/SKILL.md); for VASP/Borg analysis semantics behind `pmg analyze`, route to [../entries-thermodynamics-and-batteries/SKILL.md](../entries-thermodynamics-and-batteries/SKILL.md); for diffraction, spectra, and plotting interpretation, route to [../spectra-diffraction-and-visualization/SKILL.md](../spectra-diffraction-and-visualization/SKILL.md); for structure/local-environment interpretation, route to [../structures-local-environments-and-transformations/SKILL.md](../structures-local-environments-and-transformations/SKILL.md).
