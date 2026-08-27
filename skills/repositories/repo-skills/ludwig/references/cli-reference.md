# Ludwig CLI Reference

## When to read

Read this when translating a task into `ludwig <command>` invocations or diagnosing command-line flags.

## Command map

| Command | Purpose | Common required inputs | Notes |
| --- | --- | --- | --- |
| `train` | Train a model | `--config` or `--config_str`; `--dataset` or train/validation/test sets | Supports `--backend {local,dask,ray}`, `--gpus`, `--model_resume_path`, save-skip flags, output directory. |
| `experiment` | Train and evaluate | Same as `train`, plus `--eval_split` | Produces training and test/eval artifacts. |
| `predict` | Batch predictions from a saved model | `--model_path`, `--dataset` | Use `--generation_config` for LLM generation overrides. |
| `evaluate` | Compare predictions to ground truth | `--model_path`, `--dataset` | Can collect predictions/overall stats unless skipped. |
| `forecast` | Future steps for timeseries models | `--model_path`, `--dataset`, `--horizon` | Requires a valid timeseries model/config. |
| `preprocess` | Preprocess data using config | `--preprocessing_config` or string plus dataset inputs | Does not train. Useful for data/schema checks. |
| `synthesize_dataset` | Generate synthetic CSV data | `--output_path`, `--features` | Good for tiny local fixtures. |
| `generate_config` | LLM-backed config generation | natural-language description | Needs Anthropic/OpenAI-compatible credentials unless only showing help. |
| `init_config` | Infer initial config from dataset/target | `--dataset`, `--target` | AutoML-related; may need optional dependencies for advanced paths. |
| `render_config` | Fill defaults in a config | `--config`, `--output` | Useful for debugging implicit defaults. |
| `hyperopt` | Hyperparameter search | config with `hyperopt` section and dataset | Actual runs may require Ray/Optuna/hyperopt extras. |
| `serve` | Start local inference server | `--model_path` | Long-running server; requires serve dependencies. Use payload helper before starting. |
| `export_model` | Export trained model | `--model_path`, `--output_path`, `--format` | Formats: `safetensors`, `torch_export`, `onnx`; ONNX may need extra deps. |
| `export_mlflow` | Export MLflow model | `--model_path`, `--output_path` | Needs MLflow contrib deps for actual export. |
| `inspect` | Inspect model summary/weights/importance | `--model_path` | Add `--weights`, `--importance`, or `--json`. |
| `collect_summary`, `collect_weights`, `collect_activations` | Inspect tensors from model | model path or pretrained model and optional dataset | Can be memory-heavy for large models. |
| `datasets` | List/download Ludwig datasets | dataset command args | Network/cache-sensitive. |
| `upload` | Push model artifacts to hub | service, repo id, model path | Requires credentials and may create remote state. |
| `export_schema` | Print/export Ludwig config JSON schema | optional `--model-type`, `--output`, `--full` | Safe schema check. |
| `check_install` | Tiny synthetic installation check | none | Runs training; use help first if runtime is constrained. |

## Safe command construction

- Always set `--output_directory` to a user-approved scratch path for training, prediction, evaluation, and hyperopt.
- Prefer `--skip_save_processed_input`, `--skip_save_log`, and similar flags for smoke tests where artifacts are not needed.
- Do not pass GPU flags unless the task requires GPU and the backend check passed.
- Do not run `serve` without planning how it will be stopped; use [serving-export-and-deployment](../sub-skills/serving-export-and-deployment/SKILL.md) first.
