# Recipe consistency and catalog metadata

SpeechBrain keeps recipe metadata in `tests/recipes/*.csv`. These CSVs are not just documentation; consistency tests use them to validate recipe files, debug flags, README links, and expected outputs.

## Important fields

- `Task`: task label such as ASR-CTC, Enhancement, Speaker_recognition, Tokenizer.
- `Dataset`: dataset label.
- `Script_file`: recipe script to run.
- `Hparam_file`: HyperPyYAML file.
- `Data_prep_file`: dataset preparation script(s), when applicable.
- `Readme_file`: recipe README.
- `Result_url`: hosted checkpoints/logs/results when available.
- `HF_repo`: Hugging Face model repo when available.
- `test_debug_flags`: tiny/debug command-line overrides.
- `test_debug_checks`: expected files or performance checks.
- `performance`: public benchmark/performance metadata when available.

## Consistency expectations

Repository tests check that:

- Recipe hparams files are listed in the appropriate CSV unless explicitly excluded.
- `Script_file`, `Hparam_file`, `Data_prep_file`, and `Readme_file` paths exist.
- Mandatory file fields are not empty.
- README files contain the declared result/HF links.
- Debug flags are present where expected.

## Adding a recipe

1. Put files under the appropriate `recipes/<Dataset>/<Task>/<Model>/` shape.
2. Add a README with data, dependencies, command, result/HF links, and references.
3. Add an `extra_requirements.txt` only if the recipe needs additional dependencies.
4. Add or update the dataset CSV row.
5. Provide `test_debug_flags` that run on tiny/sample data and avoid full downloads when possible.
6. Provide `test_debug_checks` with file-existence checks before numeric thresholds.
7. Run focused recipe consistency tests.

## Common failure recovery

- If a new YAML is unlisted, add a CSV row or justify exclusion in the consistency test's avoid list.
- If `test_debug_flags` are missing, construct a tiny `--skip_prep=True` run against sample annotations when feasible.
- If README link checks fail, update the README or CSV URL consistently.
- If a recipe has heavy external dependencies, mark them in `extra_requirements.txt` and avoid installing them globally.
