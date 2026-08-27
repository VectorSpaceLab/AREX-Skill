# CLI Reference

## Purpose

Read this when you need the Anomalib command map, help behavior, config-loading rules, or export flag selection.

## Command map

| Command | Best for | Primary route | Notes |
| --- | --- | --- | --- |
| `fit` | Lightning-style training loop | `Trainer.fit` | Use when you want the direct fit step without the combined Anomalib train/test flow. |
| `validate` | Standalone validation | `Trainer.validate` | Use to validate a checkpoint or model without training. |
| `test` | Standalone testing | `Trainer.test` | Use to run the test loop on a checkpoint or trained model. |
| `train` | End-to-end Anomalib training | `Engine.train` | This is the documented training command in the getting-started guides. |
| `predict` | Inference on an image, folder, dataloader, or datamodule | `Engine.predict` | Use the current `--data` syntax, not the legacy `--data_path` example flags. |
| `export` | Torch, ONNX, or OpenVINO export | `Engine.export` | OpenVINO export accepts `--compression_type`, `--data`, and `--ov_kwargs.*`. |
| `benchmark` | Experimental benchmark pipeline | pipeline registry | The command exists when the pipeline module imports successfully; workflow details live in the sibling pipeline sub-skill. |
| `install` | Add optional bundles to an existing install | `anomalib install` | Use `--option` plus `-v` for installer logging. |

## Help behavior

- `anomalib -h` shows the top-level router and available subcommands.
- `anomalib <subcommand> -h` shows the subcommand help.
- For `fit`, `validate`, `test`, `train`, `predict`, and `export`, the formatter supports verbosity levels:
  - `-h` shows the quick-start guide.
  - `-h -v` shows the quick-start guide plus the arguments panel.
  - `-h -vv` shows the full arguments panel without the quick-start guide.
- For `install`, `-v` means verbose install logging; it is not the same as help verbosity.

## Config loading

- `-c` and `--config` load YAML or JSON config files.
- CLI arguments and config files can be combined.
- `--print_config` is available from the jsonargparse parser and prints the merged configuration.
- The train/validate/test/fit/predict routes update their config before class instantiation, so class-path and init-args mistakes surface at runtime rather than as a parse error.
- Prefer fully qualified public class paths in configs, for example `anomalib.data.MVTecAD` or `anomalib.models.Patchcore`.

## Command selection notes

- Choose `train` for the simplest training path shown in the getting-started docs.
- Choose `fit` when you want the direct Lightning loop and plan to separate validation or testing yourself.
- Choose `validate` or `test` when you already have a checkpoint and only want evaluation.
- Choose `predict` when you want inference on a folder, image, dataloader, or datamodule.
- Choose `export` when you need Torch, ONNX, or OpenVINO artifacts.
- Choose `benchmark` only when you intend to work with the pipeline benchmark flow; use the sibling pipeline sub-skill for the rest of the workflow.
- Choose `install` only for add-on bundles inside an already usable Anomalib environment.

## Export flags

- `--export_type` accepts the export target.
- `--input_size` is used for ONNX and OpenVINO export flows.
- `--compression_type` applies to OpenVINO export only.
- `--data` is required for quantized OpenVINO export paths that need a datamodule.
- OpenVINO Model Optimizer arguments are namespaced under `--ov_kwargs.<name>` when the OpenVINO parser is available.

## Bundled helper

- Run [scripts/check_cli_help.sh](../scripts/check_cli_help.sh) after installation or dependency changes to smoke-test help output, install help, verbose help, and export flags.
- Run [scripts/cli_recipes.sh](../scripts/cli_recipes.sh) when you want copyable command examples for training, prediction, export, benchmark, or install selection.
