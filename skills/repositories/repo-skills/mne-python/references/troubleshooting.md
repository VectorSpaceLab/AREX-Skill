# Cross-Cutting Troubleshooting

Use this when an MNE-Python issue spans installation, imports, optional
dependencies, datasets, plotting backends, CLI commands, or workflow routing.

## Import or version mismatch

Symptoms:

- `ModuleNotFoundError: No module named 'mne'`;
- code imports a different MNE version than expected;
- repository-development checks report the wrong import location.

Recovery:

1. Run `python -c "import mne; print(mne.__version__, mne.__file__)"` in the
   target environment.
2. If working in a checkout, use `sub-skills/repo-development/scripts/check_mne_checkout.py`.
3. Reinstall in the intended environment; do not mutate a shared environment
   without permission.

## Optional dependency missing

Symptoms:

- missing `sklearn`, `h5io`, `pymatreader`, PyVista, Qt bindings, nibabel,
  nilearn, FreeSurfer/OpenMEEG binaries, or vendor reader packages;
- a workflow works in docs but fails in a minimal install.

Recovery:

- Identify the owning workflow and install only the needed optional package or
  extra.
- Use `references/installation-and-environment.md` for install choices.
- Do not call a base import check proof of optional backend support.

## Dataset download or cache problems

Symptoms:

- dataset helper prompts/downloads unexpectedly;
- checksum or network errors;
- code cannot find sample/testing data.

Recovery:

1. Use `download=False` no-download checks to see if data already exist.
2. Ask before network downloads or persistent config changes.
3. Use `mne.get_config_path()`, `mne.get_config()`, and dataset-specific paths
   to diagnose cache/config state.
4. Route details to `cli-datasets-config`.

## Headless plotting or GUI failures

Symptoms:

- blank figures, blocked scripts, Qt/PyVista import errors, no display, browser
  not opening, notebook backend issues.

Recovery:

- Use `show=False`, a non-interactive Matplotlib backend, explicit output files,
  and `open_browser=False` for reports.
- Run `sub-skills/visualization-reporting/scripts/plotting_backend_probe.py`.
- Treat 3D/Qt/notebook rendering as optional unless display/backend support is
  verified.

## Data-shape or object-state surprises

Symptoms:

- array shape mismatch;
- event labels do not align with epochs;
- unexpected channel units/types;
- source/analysis code receives the wrong object type.

Recovery:

1. Print object type, shape, channel names/types, sampling frequency, bads,
   event ids, and projector/reference state.
2. Route to the owning sub-skill: I/O for `Raw`/`Info`, preprocessing for
   events/epochs/evoked, analysis for PSD/TFR/stats/decoding, source for
   forward/inverse objects.
3. Use bundled smoke scripts to create tiny known-good examples.

## CLI command errors

Symptoms:

- `Invalid command` from `mne`;
- confusion between underscore module names and hyphen/space CLI names;
- mutating BEM/source commands missing required files.

Recovery:

- Run `python scripts/mne_cli_probe.py --strict` or read
  `sub-skills/cli-datasets-config/references/cli-reference.md`.
- Use `mne <command> --help` before running mutating commands.
- Route source/BEM command context to `source-modeling-inverse`.

## Repository contribution and AI-assistance policy

MNE-Python permits assisted work only with human review and understanding. Do
not submit fully automated issues/PRs or unreviewed AI-generated code/text.
Route repository edits to `repo-development` and follow changelog, docs,
public API stub, test, and license rules.
