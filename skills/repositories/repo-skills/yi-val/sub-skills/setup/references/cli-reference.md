# YiVal CLI reference

The console script `yival` resolves to `yival.__main__:main`, which builds an `argparse` parser and adds subcommands from `yival.cli`.

## Subcommands

| Subcommand | Purpose | Important arguments |
| --- | --- | --- |
| `init` | Generate a YAML experiment template. | `--config_path`, `--source_type {dataset,machine_generated,user}`, `--function`, `--reader_name`, `--evaluator_names`, `--enhancer_name`, `--data_genertaor_names`, `--wrapper_names`, `--variations`, custom component flags, `--selection_strategy`. |
| `validate` | Load YAML and instantiate `ExperimentConfig`. | positional `config_file`. |
| `run` | Run a YAML experiment through `ExperimentRunner`. | positional `config_path`, `--display`, `--interactive`, `--output_path`, `--experiment_input_path`, `--async_eval`, `--enhance_page`. |
| `demo` | Copy and run packaged demo configs. | `--basic_interactive`, `--qa_expected_results`, `--auto_prompts`, `--async_eval`. |
| `bot` | Run experiment and open interactive bot behavior. | positional `config_path`, `--display`, `--interactive`, `--output_path`, `--experiment_input_path`, `--async_eval`. |
| `gen` | Launch interactive auto prompt/config generation. | `--display`. |
| `task` | Launch the default task-generation demo. | `--display`. |

## `yival init` details

`init` calls `generate_experiment_config_yaml(...)`. Useful examples:

```bash
yival init \
  --config_path qa.yml \
  --source_type dataset \
  --function my_task.answer \
  --reader_name csv_reader \
  --evaluator_names string_expected_result \
  --variations 'qa=str:,Think first;generator_name='
```

The `--variations` parser expects:

```text
key=value_type:value1,value2,...;generator_name=gen_name
```

For custom components, CLI flags use colon-separated triples:

```text
name:class_path:config_cls_path
```

At runtime, YAML registration helpers expect keys named `class` and optional `config_cls`.

## `yival run` details

`run` constructs `ExperimentRunner(config_path)` and calls:

```python
runner.run(
    display=args.display,
    interactive=args.interactive,
    output_path=args.output_path,
    experiment_input_path=args.experiment_input_path,
    async_eval=args.async_eval,
    enhance_page=args.enhance_page,
)
```

Notes:

- `--display` is default `True`, so a CLI run can start Dash and block until the UI thread ends.
- `--async_eval` uses asynchronous custom-function calls only when you pass `True` in a way argparse converts to a bool; programmatic `async_eval=True` is more reliable.
- `--output_path results.pkl` writes `results_0.pkl` for the first config because `ExperimentRunner` appends the config index to the stem.

## `yival demo` details

Demo flags copy configs from YiVal's packaged `demo/configs` area into the current working directory before running:

- `--basic_interactive`: translation prompt variations with `dataset.source_type: user_input`.
- `--qa_expected_results`: CSV-backed QA with `string_expected_result`.
- `--auto_prompts`: OpenAI-backed synthetic examples, prompt variations, evaluators, AHP, and enhancement.

The demos call external APIs when their custom functions or generators do; check credentials and cost before running beyond offline smoke tests.
