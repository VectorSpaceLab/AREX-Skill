# Installation and environment reference

Use this reference when setting up Chronos Forecasting for a user task or diagnosing imports/backend availability.

## Base install

```sh
pip install chronos-forecasting
```

The package requires Python >=3.10 and depends on PyTorch, Transformers, Accelerate, NumPy, pandas, and einops.

Minimal import check:

```python
import chronos
from chronos import BaseChronosPipeline, Chronos2Pipeline, ChronosBoltPipeline, ChronosPipeline
print(chronos.__version__)
```

## Optional extras and packages

| Need | Install direction | Notes |
| --- | --- | --- |
| S3 model loading | `boto3` or package `extras` | Required for `BaseChronosPipeline.from_pretrained("s3://...")`. |
| LoRA adapters/fine-tuning | `peft` or package `extras`/`test` | `Chronos2Pipeline.from_pretrained` can load LoRA adapter dirs when PEFT metadata is present. |
| fev benchmarks | `fev`, `datasets` or package `extras`/`test`/`dev` | May download datasets; verify cache/network policy. |
| Parquet examples | `pandas[pyarrow]` or `pyarrow` | Needed for parquet data loading shown by Chronos-2 examples. |
| Maintainer training/evaluation scripts | package `dev` dependencies | Includes GluonTS, datasets, typer, tensorboard, typer-config, joblib, rich, fev. Use only for selected training/evaluation tasks. |
| AWS deployment | SageMaker/AWS SDK stack | Not part of base package; requires credentials and cost approval. |

## CPU/GPU policy

CPU is sufficient for API inspection, tiny dummy-model tests, and many small examples. Real model inference and training may be slow on CPU. Use CUDA only when the user requests it or the task requires practical large-model runtime.

When using CUDA:

- Install a PyTorch wheel compatible with the driver and hardware.
- Pass `device_map="cuda"` or `device_map="auto"` intentionally.
- Consider `torch_dtype="bfloat16"` on supported GPUs, especially for large models.
- Keep `batch_size`, `context_length`, and `prediction_length` explicit to control memory.

Do not claim GPU verification from a CPU-only import check. If a task depends on GPU throughput or memory, run a backend smoke in that environment first.

## Safe environment smoke

The generated root helper is safe by default:

```sh
python scripts/chronos_api_smoke.py
```

It imports the package, prints public signatures, and reports whether CUDA is visible. It does not download or load a model unless a user supplies a model anchor.

Focused helpers exist in sub-skills:

- Chronos-2: `sub-skills/chronos-2-forecasting/scripts/chronos2_smoke_forecast.py`
- Bolt/original: `sub-skills/chronos-bolt-and-original/scripts/bolt_original_smoke.py`
- Data validation: `sub-skills/data-formats-and-validation/scripts/validate_chronos_dataframe.py`
- Training/evaluation: `sub-skills/training-evaluation-deployment/scripts/aggregate_relative_scores.py` and `chronos2_fit_smoke_template.py`

## Network, cache, and credentials

Hugging Face model IDs, `s3://` URIs, fev datasets, SageMaker endpoints, and hub pushes may use network, local caches, or credentials. Before running them, confirm:

- the model/dataset/URI,
- whether downloads are allowed,
- where caches or outputs should live,
- credentials/tokens are already configured outside the generated skill, and
- cleanup/cost expectations for cloud resources.
