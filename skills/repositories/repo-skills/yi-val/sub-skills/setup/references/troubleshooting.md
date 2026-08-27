# Setup troubleshooting

## Template generation

- If `yival init` outputs a config with missing defaults, import the relevant built-in component module before calling `generate_experiment_config_yaml()` programmatically. Registries are not populated until modules import.
- The CLI option for data generators is spelled `--data_genertaor_names`. YAML uses the correct `data_generators` field.
- `--custom_reader` accepts `name:class_path:config_cls_path`, but runtime YAML should use:

```yaml
custom_reader:
  my_reader:
    class: my_reader_module.MyReader
    config_cls: my_reader_module.MyReaderConfig
```

## Validation

- `yival validate` instantiates `ExperimentConfig(**config_data)` and prints errors instead of raising them to the shell. Read stdout for failure details.
- `load_and_validate_config()` returns an OmegaConf-to-object conversion cast as `ExperimentConfig`; many runtime paths then treat it like a dictionary. YAML key spelling matters more than static dataclass validation.
- A config list is accepted by `load_and_validate_configs()`; each config is run separately.

## Data paths

- Prefer absolute file paths for CSV datasets when the config may be run outside the checkout.
- For packaged demos, the copied config may contain relative paths such as `demo/data/yival_expected_results.csv`; these rely on YiVal's package-relative lookup behavior.
- Hugging Face dataset URLs must be the dataset-server `rows` endpoint, not a normal Hub dataset page.

## Custom function imports

- Direct import form: `package.module.function` works when the package/module is on `PYTHONPATH`.
- For local one-off modules, run from the parent directory or set `PYTHONPATH` before invoking YiVal.
- Ensure the custom function accepts every data column as a named parameter and also accepts `state`.

## Smoke-test sequence

```bash
python scripts/check_install.py --check-cli
python scripts/write_minimal_experiment.py --run
```

If the first command fails, fix installation/imports before debugging YAML. If the second command fails, inspect the generated fixture directory reported in JSON.
