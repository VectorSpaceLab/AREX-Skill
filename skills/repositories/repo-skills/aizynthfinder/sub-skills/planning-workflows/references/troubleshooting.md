# Planning Troubleshooting

Use this reference for failures while running `aizynthcli`, `AiZynthFinder`, `AiZynthExpander`, or the optional notebook interface. If the problem is missing config/model/stock assets, first route to `../configuration-and-data/SKILL.md`; if the problem is route interpretation, route to `../route-analysis/SKILL.md`; if the problem is custom hook/plugin code, route to `../extension-and-development/SKILL.md`.

## `--smiles` Is Neither a File Nor Valid SMILES

Symptom:

- CLI logs that the `--smiles` argument does not point to an existing file or a valid RDKit SMILES and cannot start retrosynthesis planning.

Likely causes:

- Typo in a batch file path.
- Unquoted shell characters in a literal SMILES.
- Invalid or unsupported SMILES syntax.
- A relative path resolved from an unexpected current working directory.

Recovery:

- For batch mode, confirm the file exists before running: `test -f targets.smi`.
- For literal mode, quote the SMILES string.
- Test the target in a small Python/RDKit parse check when available.
- Use the bundled command builder; it treats an existing `--smiles` path as batch and a non-existing value as literal.

## `--nproc` With a Literal SMILES

Symptom:

- CLI raises `ValueError: For multiprocessing execution the --smiles argument needs to be a filename`.
- The command builder rejects `--nproc` with a non-existing `--smiles` value.

Cause:

- Multiprocessing splits an input file over worker processes; it cannot split a literal target.

Recovery:

- Put one or more targets into a file, one SMILES per line, and pass that file to `--smiles`.
- Remove `--nproc` for a single literal target.
- Do not combine multiprocessing with checkpointed resume if checkpoint continuity is required; use single-process batch with `--checkpoint` instead.

## `Target molecule unsanitizable`

Symptoms:

- Python `prepare_tree()` raises `ValueError("Target molecule unsanitizable")`.
- CLI prints `Failed to setup search due to: 'target molecule unsanitizable'` for a single target.
- CLI prints `Failed to setup search for TARGET due to: 'target molecule unsanitizable'` for a batch row.

Likely causes:

- RDKit can parse the string into a molecule object, but sanitization fails.
- Charges, valences, aromaticity, atom maps, or tautomer form are not compatible with RDKit sanitization.
- Pre-processing changed `finder.target_smiles` or `finder.target_mol` into an unsanitizable structure.

Recovery:

- Re-check the exact SMILES after shell quoting or after pre-processing.
- Try a canonicalized or neutralized form of the target.
- If a pre-processing hook is active, reproduce without it and then route hook debugging to `../extension-and-development/SKILL.md`.
- In Python, isolate setup with `finder.target_smiles = target; finder.prepare_tree()` before running a full search.

## No Target Molecule Set

Symptom:

- `prepare_tree()` raises `ValueError("No target molecule set")`.

Cause:

- `finder.target_smiles` or `finder.target_mol` was never assigned before `prepare_tree()`.

Recovery:

- Set `finder.target_smiles = "..."` before `prepare_tree()`.
- If a helper function accepts a finder object, assert the target assignment happens after policy/stock selection and before search.

## Search Tree Not Initialized

Symptom:

- `build_routes()` raises `ValueError("Search tree not initialized")`.
- `extract_statistics()` returns `{}` after code expected route statistics.

Likely causes:

- `tree_search()` was not called.
- The target was changed after search, which clears `finder.tree`.
- `prepare_tree()` failed and was swallowed by the caller.

Recovery:

- Use the lifecycle order: set target, `prepare_tree()`, `tree_search()`, `build_routes()`, `extract_statistics()`.
- Check for exceptions or CLI `Failed to setup search` messages before route building.
- Do not assign a new target between search and route extraction.

## Missing Config, Model, or Stock Files

Symptoms:

- Config loading fails.
- Policy or stock loading fails.
- Search starts but no routes are solved because expected stock entries are missing.

Likely causes:

- `--config` points to the wrong file.
- Relative paths inside the config do not resolve as expected.
- Public model/stock assets were not downloaded or moved.
- Optional model backend dependencies are not installed.

Recovery:

- Route to `../configuration-and-data/SKILL.md` to validate the YAML and asset paths.
- Prefer absolute or environment-expanded asset paths in production configs.
- Confirm the selected stock and policy keys are loaded before running long batches.

## Policy, Filter, or Stock Key Mismatch

Symptoms:

- Selection calls fail or choose no useful model/stock.
- CLI run fails shortly after loading the config.
- Results are unexpectedly unsolved because the intended stock was not selected.

Likely causes:

- CLI `--policy`, `--filter`, or `--stocks` values do not match config keys.
- The config has multiple policies but the CLI default selected only the first expansion policy.
- The filter policy is optional and a requested filter key was not loaded.

Recovery:

- Inspect config keys before selecting them.
- Use explicit `--policy`, `--filter`, and `--stocks` for reproducibility.
- In Python, print or inspect `finder.expansion_policy.items`, `finder.filter_policy.items`, and `finder.stock.items` before selection.
- Route config-key repair to `../configuration-and-data/SKILL.md`.

## Invalid Break or Freeze Bonds

Symptoms:

- `prepare_tree()` raises `ValueError("Bonds in 'break_bonds' must exist in target molecule")`.
- `prepare_tree()` raises `ValueError("Bonds in 'freeze_bond' must exist in target molecule")`.

Likely causes:

- The configured atom index pair does not correspond to a bond in the target molecule.
- Atom numbering changed after SMILES canonicalization or target editing.
- `break_bonds` is active with `"broken bonds"` search reward and the target does not contain every requested bond.
- `freeze_bonds` always requires every requested bond to exist.

Recovery:

- Verify atom-map/index conventions against the exact target used at runtime.
- Start with no focused bonds, then add one bond pair at a time.
- For multi-objective MCTS with broken bonds, ensure `search.algorithm_config.search_rewards` includes `"broken bonds"` only when configured bonds exist.
- Keep configuration repair in `../configuration-and-data/SKILL.md` and scoring interpretation in `../route-analysis/SKILL.md`.

## Clustering Fails

Symptoms:

- CLI fails after search when `--cluster` is enabled.
- GUI clustering import fails.
- Clustering tests or route-distance calls are skipped or unavailable.

Likely causes:

- Optional route-distance dependencies are not installed.
- Route-distance model config is missing.
- Routes are malformed or absent.

Recovery:

- Re-run without `--cluster` to verify core planning succeeds.
- Install/validate optional clustering dependencies and route-distance settings before enabling clustering.
- Route cluster interpretation and route-distance result analysis to `../route-analysis/SKILL.md`.

## Pre/Post-Processing Module Is Ignored

Symptoms:

- Expected hook output does not appear.
- CLI prints no `Adding pre-processing job from ...` or `Adding post-processing job from ...` message.

Likely causes:

- The module is not importable from the process `PYTHONPATH`.
- The module does not define `pre_processing` or `post_processing` with the expected name.
- `--post_processing` was supplied as one string containing spaces instead of separate module names.
- Multiprocessing was used; worker commands do not preserve `--pre_processing`.

Recovery:

- Confirm the module can be imported with the same Python environment used by `aizynthcli`.
- Confirm `pre_processing(finder, index)` or `post_processing(finder)` exists.
- Avoid `--nproc` when pre-processing is required.
- Route hook implementation and validation to `../extension-and-development/SKILL.md`.

## Checkpoint Resume Looks Wrong

Symptoms:

- Resume skips too many or too few rows.
- Output and checkpoint disagree after changing inputs.

Likely causes:

- Checkpoint resume uses the number of `processed_smiles` entries already in the checkpoint, not target identifiers.
- The input file order changed between runs.
- Config or selection flags changed between runs.
- A previous checkpoint was reused for a different target file.

Recovery:

- Resume with the same input file order and same config/selections.
- Use a fresh checkpoint for changed target lists.
- Inspect newline-delimited checkpoint records before trusting a resume.
- Keep checkpoint files separate from final route-analysis outputs.

## GUI or Notebook Does Not Launch

Symptoms:

- `aizynthapp --config config.yml` does not open a browser.
- Widget display fails in a notebook.
- GUI clustering import fails.

Likely causes:

- Jupyter, IPython, jupytext, or ipywidgets support is missing.
- Running in a headless environment without browser access.
- Optional clustering dependencies are missing.

Recovery:

- Save a notebook instead of launching: `aizynthapp --config config.yml --output aizynthfinder_app.ipynb`.
- Open the notebook in an environment with Jupyter and widgets enabled.
- Use CLI or Python API workflows for non-interactive automation.
- Treat GUI clustering as optional; core planning does not require it.
