# `aizynthcli` Reference

`aizynthcli` runs retrosynthesis planning from an installed AiZynthFinder environment. It requires a config and a SMILES argument.

## Required Flags

| Flag | Values | Meaning |
| --- | --- | --- |
| `--config` | file path | YAML configuration file containing search settings, stocks, expansion policies, and optional filters. |
| `--smiles` | literal SMILES or file path | Target molecule SMILES, or a file with one SMILES per row. |

## Optional Flags

| Flag | Values | Meaning |
| --- | --- | --- |
| `--policy` | one or more keys | Expansion policy key names to select from the loaded config. |
| `--filter` | one or more keys | Filter policy key names to select from the loaded config. |
| `--stocks` | one or more keys | Stock key names to select from the loaded config. |
| `--output` | file path | Output file. Single-target default is `trees.json`; batch default is `output.json.gz`. |
| `--log_to_file` | flag | Enable detailed file logging in addition to console logging. |
| `--nproc` | integer | Split a SMILES file over multiple worker processes. Requires `--smiles` to be a file. |
| `--cluster` | flag | Perform automatic route clustering after route building. |
| `--post_processing` | one or more module names | Import modules and call `post_processing(finder)` after route building. |
| `--pre_processing` | module name | Import a module and call `pre_processing(finder, index)` before each target. |
| `--checkpoint` | file path | Append/resume newline-delimited per-target checkpoint data for single-process batch runs. |

## Input Mode Detection

The CLI decides input mode from `--smiles`:

- Existing path: batch mode; file is read line by line.
- Non-existing path/string that RDKit parses as a molecule: single-target mode.
- Non-existing path/string that RDKit cannot parse: command logs an error and returns without planning.

Implications:

- A filename typo can be interpreted as invalid SMILES rather than a missing-file exception.
- A valid literal SMILES that happens to match an existing filename will be treated as a batch file.
- Use explicit file extensions and pre-check file existence when building automation.

## Defaults

When selection flags are omitted:

- `--stocks`: selects all loaded stocks.
- `--policy`: selects the first loaded expansion policy.
- `--filter`: selects all loaded filters.
- `--output`: `trees.json` for single-target mode, `output.json.gz` for batch mode.

## Safe Command Patterns

Single target:

```bash
aizynthcli --config config.yml --smiles "CCO" --output trees.json
```

Batch file:

```bash
aizynthcli --config config.yml --smiles targets.smi --output output.json.gz
```

Batch with explicit selections:

```bash
aizynthcli \
  --config config.yml \
  --smiles targets.smi \
  --policy uspto ringbreaker \
  --filter uspto_filter \
  --stocks zinc emolecules \
  --output output.json.gz
```

Checkpointed batch:

```bash
aizynthcli \
  --config config.yml \
  --smiles targets.smi \
  --output output.json.gz \
  --checkpoint checkpoint.json.gz
```

Multiprocessing batch:

```bash
aizynthcli \
  --config config.yml \
  --smiles targets.smi \
  --output output.json.gz \
  --nproc 4
```

Clustered batch:

```bash
aizynthcli \
  --config config.yml \
  --smiles targets.smi \
  --cluster \
  --output output.json.gz
```

Hooked run:

```bash
aizynthcli \
  --config config.yml \
  --smiles targets.smi \
  --pre_processing my_pre_module \
  --post_processing my_post_module another_post_module
```

## Command Builder Helper

Use the bundled helper to print a shell-quoted command without running it:

```bash
python skills/aizynthfinder/sub-skills/planning-workflows/scripts/build_aizynthcli_command.py \
  --config config.yml \
  --smiles targets.smi \
  --output output.json.gz \
  --policy uspto ringbreaker \
  --filter uspto_filter \
  --stocks zinc \
  --cluster \
  --nproc 4 \
  --checkpoint checkpoint.json.gz
```

The helper validates that `--nproc` is not used with a literal single SMILES. It prints a command string and performs no planning, downloads, imports from user hook modules, or file writes.

## Output Mode Summary

Single-target mode:

- Writes route trees to `--output` or `trees.json`.
- Logs statistics to terminal/logger.
- Does not include `stock_info` or batch dataframe columns in the same way as batch output.

Batch mode:

- Writes a pandas-compatible JSON or HDF5 output file.
- Includes per-target statistics, route dictionaries, and `stock_info`.
- With `--checkpoint`, appends per-target records to the checkpoint file during processing.

Multiprocessing mode:

- Splits the input file into per-worker files.
- Writes temporary worker outputs and concatenates them into the requested output.
- Preserves `--policy`, `--filter`, `--stocks`, `--cluster`, and `--post_processing` in worker commands.
- Does not preserve `--pre_processing`, `--checkpoint`, or `--log_to_file` in worker commands.

## Guardrails

- Do not use `--nproc` unless `--smiles` names an existing file.
- Do not use `--cluster` unless route-distance/clustering dependencies are installed.
- Do not rely on omitted selection flags when multiple policies, filters, or stocks are configured and reproducibility matters.
- Do not treat `--checkpoint` as a route-analysis file; it is a resume aid with processed rows.
- Keep custom hook authoring out of this sub-skill; route that work to `../extension-and-development/SKILL.md`.
