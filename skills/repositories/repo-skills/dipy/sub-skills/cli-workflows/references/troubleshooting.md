# CLI Workflow Troubleshooting

Use this guide for Dipy command-line failures before debugging lower-level algorithms. Most CLI problems are entry-point discovery, optional dependencies, parser expectations, input/output path choices, or outdated command names.

## Command Not Found

Symptoms:

- Shell reports `dipy_fit_dti: command not found`.
- `python scripts/dipy_cli_probe.py` lists flows, but shell entry points fail.
- A workflow exists in Python but not on `PATH`.

Actions:

1. Run `python scripts/dipy_cli_probe.py --format json` to confirm the installed Python package exposes `dipy.workflows.cli.cli_flows`.
2. Run Python module checks from the same environment that will run the command; shell `PATH` and Python import environment can differ.
3. Prefer invoking installed console scripts after a normal package install; do not rely on repository-local old script names.
4. If only Python API import works, use the listed command names to repair the environment or call workflow classes through Python under the relevant scientific sub-skill.

## Help Probe Fails

Symptoms:

- `COMMAND --help` exits nonzero.
- Help output starts but import warnings appear.
- Optional commands fail before showing help.

Actions:

1. Run `python scripts/dipy_cli_probe.py --check-help COMMAND --timeout 8 --format json` and inspect `returncode`, `stdout_head`, and `stderr_head`.
2. Confirm the command is present in `cli_flows`; missing commands may be stale docs or old aliases.
3. For `dipy_horizon`, check visualization dependencies such as FURY and display availability.
4. For `dipy_correct_biasfield` and `dipy_evac_plus`, check neural-network backends such as PyTorch or TensorFlow and model requirements.
5. Treat optional dependency failures as environment limitations, not as proof that core Dipy CLI is broken.

## Deprecated Or Old Command Names

Symptoms:

- A tutorial or old draft mentions a command not present in `cli_flows`.
- `dipy_sh_convert_mrtrix` prints a deprecation warning.
- Very old names such as `dipy_fit_tensor`, `dipy_peak_extraction`, or `dipy_sh_estimate` appear in legacy tests or notes.

Actions:

- Prefer current project-script names from `pyproject.toml` and `cli_flows`.
- Replace `dipy_sh_convert_mrtrix` with `dipy_convert_sh` in new guidance.
- Map old tensor-fitting intent to current `dipy_fit_dti` and route parameter details to `reconstruction-models`.
- Do not copy outdated script names into public examples unless explicitly documenting migration.

## Parser Rejects Arguments

Symptoms:

- Argparse reports an unrecognized option.
- A flag that exists in a lower-level API is missing from CLI help.
- Passing `None`, tuples, booleans, or repeated values behaves unexpectedly.

Actions:

1. Run `COMMAND --help`; Dipy exposes the workflow `run` signature, not every lower-level algorithm keyword.
2. Check `references/workflow-parser.md` for docstring-derived type behavior.
3. Pass `None` or `none` for a Python `None` value.
4. For optional booleans, use the flag to set `True` and omit it for the default.
5. For optional variable arguments, provide values after the flag; a bare flag can parse as an empty list.
6. For tuple-like options, inspect help and workflow docs; argparse receives strings for tuple docstring types.

## Output Files Missing Or Not Overwritten

Symptoms:

- Command runs but expected files are not in the current directory.
- Existing files prevent a workflow from running.
- Multiple inputs overwrite or collide in output names.

Actions:

1. Always set `--out_dir` in reproducible examples.
2. Inspect command help for `out_*` output filename parameters and set them explicitly if downstream steps expect names.
3. Check log output for existing-file messages; Dipy skips processing when outputs already exist unless `--force` is passed.
4. Use `--force` only after confirming outputs are safe to replace.
5. Use `--mix_names` when multiple inputs or glob-expanded paths can create colliding output names.
6. Record `--out_strat` if you change it from the default `absolute`.

## Optional Dependency Surfaces

Base inspection showed Dipy imports available but `fury`, `matplotlib`, `torch`, and `tensorflow` were not installed. Optional command surfaces include:

| Surface | Commands | Likely missing dependency impact | Safe response |
| --- | --- | --- | --- |
| Visualization | `dipy_horizon` | FURY/display stack needed for interactive windows | Probe help; document optional visualization install rather than failing core CLI. |
| Plotting-heavy stats/segmentation | BUAN commands, clustering visual outputs | Matplotlib may be needed for plots | Separate data generation from plotting when possible. |
| Neural networks | `dipy_correct_biasfield`, `dipy_evac_plus` | PyTorch/TensorFlow/model assets may be needed | Mark optional and verify backend before recommending. |

## Version Or Checkout Confusion

Symptoms:

- Installed package reports one version while source files show another command table.
- `import dipy` fails from inside a checkout because generated version metadata is absent.
- `cli_flows` count differs from expected 61.

Actions:

1. Run `python scripts/dipy_cli_probe.py --format json` from the target environment and trust the installed `cli_flows` for executable availability.
2. Run `COMMAND --version` for the console-script version string.
3. Avoid leaking local checkout or environment paths into user-facing instructions.
4. If source checkout shadows the installed package, run probes from outside the source tree or install the package normally.

## Network And Data Safety

- `dipy_fetch` can download datasets depending on arguments; do not use it in offline or no-network smoke checks except to inspect help/list behavior.
- Visualization commands can open windows; do not run them in headless automation except for help/version probes.
- Reconstruction/tracking commands can be computationally expensive; use tiny fixtures or existing user data and route algorithm choices to the owning sub-skills.
- Never run commands that overwrite user data without explicit `--out_dir`, expected output names, and a conscious `--force` decision.
