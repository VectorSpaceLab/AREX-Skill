# CLI Troubleshooting

Use this reference when a Snips NLU CLI command fails or behaves unexpectedly.
All commands below use `python -m snips_nlu`; replace it with `snips-nlu` only
when the console script is known to point to the intended environment.

## Missing Console Script

Symptoms:

- `snips-nlu: command not found`
- The console script runs a different Snips NLU version than expected.

Actions:

```bash
python -m snips_nlu --help
python -m snips_nlu version
python -m snips_nlu model-version
```

If the module entry point works, keep using it. If neither entry point works,
install Snips NLU in the active Python environment before constructing workflow
commands. Avoid guessing from a shell `PATH`; version-check the entry point that
will actually run the job.

## Network or Resource Download Failures

Symptoms:

- pip download/install errors during `download`, `download-entity`,
  `download-language-entities`, or `download-all-languages`
- unknown resource shortcut or compatibility lookup errors
- language resources download succeeds but linking fails

Actions:

1. Confirm the task really needs resource downloads; simple CLI help/version
   checks do not.
2. Prefer compatible shortcut downloads when possible:

   ```bash
   python -m snips_nlu download en
   ```

3. If pip arguments are needed and start with `-`, put them after `--` so the
   Snips NLU parser passes them to pip:

   ```bash
   python -m snips_nlu download en -- --no-cache-dir
   ```

4. Use `-d/--direct` only when the user has provided a full resource name with
   version, such as `snips_nlu_en-<version>`. Direct mode skips compatibility
   checks.
5. For builtin gazetteer entities, remember that the entity commands download
   the language resources first:

   ```bash
   python -m snips_nlu download-entity snips/musicArtist en
   python -m snips_nlu download-language-entities en
   ```

6. If resources are already present outside the package resource location, link
   them explicitly:

   ```bash
   python -m snips_nlu link <resources-dir> en
   ```

7. Treat `download-all-languages` as network-heavy and environment-mutating;
   avoid it unless broad language coverage is explicitly required.

## Parse Path Missing, Incomplete, or Incompatible

Symptoms:

- `parse` fails because the training path does not exist
- loading errors mention missing persisted-engine files
- incompatible model-version errors
- a workflow attempts to parse with an unfitted or unpersisted engine

Actions:

```bash
test -f trained_engine/nlu_engine.json
python -m snips_nlu model-version
python -m snips_nlu parse trained_engine -q "test utterance"
```

If `trained_engine/nlu_engine.json` is missing, train and persist the engine
first:

```bash
python -m snips_nlu train dataset.json trained_engine
```

If the persisted engine was produced by an incompatible model version, retrain
with the Snips NLU package that will run inference, or run inference in a
compatible environment. If resources cannot be loaded during parsing, repair the
language/entity resources before retraining or parsing again.

## Metrics Extra Missing

Symptoms:

- `cross-val-metrics` or `train-test-metrics` help is available, but execution
  fails with `No module named snips_nlu_metrics` or a similar import error.

Actions:

1. Install the Snips NLU metrics extra or a compatible `snips-nlu-metrics`
   package in the active environment.
2. Re-run a tiny metrics command or at least the command help:

   ```bash
   python -m snips_nlu cross-val-metrics --help
   python -m snips_nlu train-test-metrics --help
   ```

3. If the dependency is present but training fails, debug the dataset/resources
   as a training problem rather than a metrics CLI problem.

## CSV Intent Filters Containing Commas

The parse command accepts one `-f/--intents-filter` value and parses it with CSV
rules. Intent names containing commas must be quoted inside a single shell
argument:

```bash
python -m snips_nlu parse trained_engine -q "Make coffee" -f 'MakeTea,"Make,Coffee"'
```

Wrong pattern:

```bash
python -m snips_nlu parse trained_engine -q "Make coffee" -f MakeTea,Make,Coffee
```

The wrong pattern becomes three intent names (`MakeTea`, `Make`, `Coffee`), not
the intended `Make,Coffee` intent.

## Output Path Already Exists

Symptoms:

- training fails with a message like `Path already exists`
- a previously generated engine directory blocks a new `train` command

Actions:

- Choose a new engine output directory for each training run:

  ```bash
  python -m snips_nlu train dataset.json trained_engine_v2
  ```

- Remove or archive the old directory only after user approval; persisted
  engine directories are model artifacts.
- Metrics commands write JSON files and may overwrite an existing metrics file;
  training is stricter because engine persistence requires a non-existing
  directory.

## Link Target Already Exists

Symptoms:

- `link` fails because the symlink already exists
- `link -f` still refuses to overwrite a normal file or directory

Actions:

```bash
python -m snips_nlu link -f snips_nlu_en en
```

Use `-f` for an existing symlink. If a normal file or directory already occupies
the link name, move it deliberately rather than expecting `link -f` to delete it.
