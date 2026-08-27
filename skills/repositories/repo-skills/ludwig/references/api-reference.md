# Python API Reference

## When to read

Read this when embedding Ludwig in Python instead of shell commands.

## Core class

```python
from ludwig.api import LudwigModel
model = LudwigModel(config, logging_level=..., backend=..., gpus=..., callbacks=...)
```

Key methods verified from the package surface:

| API | Purpose | Important parameters | Return shape |
| --- | --- | --- | --- |
| `LudwigModel(config, logging_level=logging.ERROR, backend=None, gpus=None, gpu_memory_limit=None, allow_parallel_threads=True, callbacks=None)` | Construct a model from a config dict or YAML path | `config`, `backend`, `gpus`, `callbacks` | model object |
| `train(dataset=None, training_set=None, validation_set=None, test_set=None, training_set_metadata=None, data_format=None, experiment_name="api_experiment", model_name="run", model_resume_path=None, output_directory="results", random_seed=..., callbacks=None, **kwargs)` | Train and save model artifacts | dataset inputs, output/saving flags, resume path, seed | `TrainingResults(train_stats, preprocessed_data, output_directory)` |
| `experiment(..., eval_split="test", skip_collect_predictions=False, output_directory="results", ...)` | Train and evaluate in one call | same as train plus eval controls | model, eval stats, train stats, preprocessed data, output directory |
| `preprocess(..., skip_save_processed_input=True, random_seed=..., **kwargs)` | Preprocess without training | dataset/config/data-format fields | preprocessed dataset bundle |
| `predict(dataset=None, data_format=None, split="full", batch_size=128, generation_config=None, output_directory="results", return_type=pd.DataFrame, callbacks=None, **kwargs)` | Predict with trained model | dataset, split, batch size, LLM generation config | `(predictions, output_directory)` |
| `evaluate(dataset=None, data_format=None, split="full", batch_size=None, collect_predictions=False, collect_overall_stats=False, output_directory="results", return_type=pd.DataFrame, **kwargs)` | Evaluate against labels | dataset, split, batch size, collection flags | stats/predictions/output bundle depending flags |
| `forecast(dataset, data_format=None, horizon=1, output_directory=None, output_format="parquet", callbacks=None)` | Timeseries forecasting | horizon and output format | forecast DataFrame and optional saved output |
| `generate(input_strings, generation_config=None, streaming=False, callbacks=None)` | LLM text generation through trained LLM model | input string(s), generation overrides | string or list of strings |
| `load(model_dir, logging_level=logging.ERROR, backend=None, gpus=None, gpu_memory_limit=None, allow_parallel_threads=True, callbacks=None, from_checkpoint=False)` | Load a saved model | model directory, backend/GPU options | `LudwigModel` |
| `save(save_path)` / `save_config(save_path)` / `export_model(save_path, format="safetensors", sample_input=None)` | Save/export artifacts | destination and format | files on disk |

## Other public APIs

- `ludwig.api.kfold_cross_validate(...)` runs k-fold cross-validation from a config and dataset.
- `ludwig.config_generation.generate_config(task_description, model="claude-sonnet-4-20250514", api_key=None, validate=True)` calls an LLM provider and validates the generated config.
- `ludwig.automl.auto_train(...)`, `create_auto_config(...)`, and `init_config(...)` support AutoML flows, but the package may import Ray-related modules. Diagnose optional Ray dependencies before relying on live imports.

## Common API pitfalls

- `predict`, `evaluate`, and `forecast` require a trained or loaded model with model weights and training-set metadata.
- `forecast` requires a timeseries input feature and timeseries output feature; otherwise Ludwig raises a timeseries-related `ValueError`.
- `generate` is LLM-only and GPU-sensitive for quantized models.
- API calls that write artifacts should use explicit output directories to avoid surprising files in the current working directory.
