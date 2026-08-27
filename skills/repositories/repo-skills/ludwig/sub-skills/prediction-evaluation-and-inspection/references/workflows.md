# Prediction and Evaluation Workflows

## Batch prediction CLI

```bash
ludwig predict --model_path results/experiment_run/model --dataset predict.csv --output_directory predictions
```

Prediction datasets should include only input columns unless the model workflow expects otherwise. Use `--generation_config` for LLM generation overrides.

## Evaluation CLI

```bash
ludwig evaluate --model_path results/experiment_run/model --dataset eval.csv --output_directory eval_results
```

Evaluation data must include output/label columns. Use collection flags deliberately because collecting predictions can create larger outputs.

## Forecasting

```bash
ludwig forecast --model_path results/experiment_run/model --dataset history.csv --horizon 5 --output_format parquet
```

Forecast requires a model trained with timeseries input/output features and enough recent history.

## Inspection

```bash
ludwig inspect --model_path results/experiment_run/model --json
ludwig collect_summary --model results/experiment_run/model
```

Collecting weights/activations can be memory-heavy on large models. Start with summary/JSON output.
