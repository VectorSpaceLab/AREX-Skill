# Prediction API Reference

## Loading

```python
from ludwig.api import LudwigModel
model = LudwigModel.load("results/experiment_run/model")
```

## `predict`

`model.predict(dataset, data_format=None, split="full", batch_size=128, generation_config=None, skip_save_unprocessed_output=True, skip_save_predictions=True, output_directory="results", return_type=pd.DataFrame, callbacks=None, **kwargs)` returns predictions and an output directory.

## `evaluate`

`model.evaluate(dataset, data_format=None, split="full", batch_size=None, skip_save_unprocessed_output=True, skip_save_predictions=True, skip_save_eval_stats=True, collect_predictions=False, collect_overall_stats=False, output_directory="results", return_type=pd.DataFrame, **kwargs)` evaluates labels against predictions.

## `forecast`

`model.forecast(dataset, data_format=None, horizon=1, output_directory=None, output_format="parquet", callbacks=None)` returns a forecast DataFrame and optionally writes output.

## `generate`

`model.generate(input_strings, generation_config=None, streaming=False, callbacks=None)` is LLM-only. Quantized models may require CUDA.

## Collection APIs

`collect_weights` and `collect_activations` inspect tensors; use them carefully with large models and datasets.
