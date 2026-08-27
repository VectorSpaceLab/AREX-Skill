# Results and Metadata Tables

`timm` ships validation, benchmark, and metadata CSV files that are useful for choosing models and interpreting local benchmark output. Treat them as curated snapshots, not live measurements of the user's hardware.

## Benchmark CSV Files

Files named like `benchmark-infer-amp-nchw-pt291-cu130-5090.csv` encode common run conditions:

- `benchmark-infer`: inference benchmark results.
- `amp`, `amp_bf16`, `bf16`, or `fp32`: precision family.
- `nchw` or `nhwc`: memory layout; `nhwc` corresponds to channels-last.
- `pt...` and `cu...`: PyTorch and CUDA/runtime versions.
- Final token: accelerator or CPU identifier, sometimes with `dynamo`/compile indication.

Common benchmark columns:

| Column | Meaning | Notes |
| --- | --- | --- |
| `model` | timm model identifier | May include pretrained weight tags for validation-style rows or architecture names for benchmark rows. |
| `infer_samples_per_sec` | Images per second for inference | Higher is faster; compare only under similar hardware, software, precision, layout, and batch size. |
| `infer_step_time` | Mean inference step time in milliseconds | Lower is faster; step time is per batch, not per image. |
| `infer_batch_size` | Batch size used for timing | Batch-size changes can dominate throughput. |
| `infer_img_size` | Resolved square image size | Larger image sizes increase cost; some models have non-default test sizes. |
| `infer_gmacs` | Estimated giga multiply-accumulates | Depends on optional profiler behavior and input size; use as approximate compute cost. |
| `infer_macts` | Estimated mega activations | Usually from `fvcore`; may be absent when not available. |
| `train_samples_per_sec` | Synthetic train-step samples per second | Includes forward/backward/optimizer work; not a full training recipe measure. |
| `train_step_time` | Mean train step time in milliseconds | Per batch. With `--detail`, fwd/bwd/opt breakdown columns may appear. |
| `param_count` | Parameter count in millions | Shared field after benchmark merges inference/train results. |
| `error` | Failure string | Appears when a model cannot be benchmarked or batch-size retry exhausts. |

## Validation Result Tables

`results-imagenet.csv` is the standard ImageNet-1k validation summary. Its header is:

```text
model,img_size,top1,top1_err,top5,top5_err,param_count,crop_pct,interpolation
```

Interpretation:

| Column | Meaning |
| --- | --- |
| `model` | Model name or model plus pretrained weight tag. |
| `img_size` | Evaluation image size. |
| `top1`, `top5` | Top-1 and top-5 accuracy percentages. |
| `top1_err`, `top5_err` | Error percentages, generally `100 - accuracy`. |
| `param_count` | Parameters in millions. |
| `crop_pct` | Evaluation crop percentage from the model data config. |
| `interpolation` | Resize interpolation used for evaluation. |

Additional result files cover ImageNet Real Labels, ImageNetV2, Sketch, ImageNet-A, ImageNet-R, and clean 200-class comparison subsets for A/R. Rank or delta columns in those files should be interpreted relative to the matching dataset definition, not as direct replacements for ImageNet validation accuracy.

## Model Metadata

`model_metadata-in1k.csv` maps ImageNet-1k model names to a compact pretraining/source label. Its header is:

```text
model,pretrain
```

Examples of `pretrain` labels include dataset or technique markers such as ImageNet-1k, ImageNet-21k, self-supervised learning, weakly supervised learning, adversarial training, or distillation-style notes. Use this table to explain why two models with similar architecture names may have different accuracy or transfer behavior.

Metadata caveats:

- The table is manually curated and may lag behind newly added pretrained configs.
- It is not a complete recipe description; augmentation, optimizer, schedule, and fine-tune details are not guaranteed.
- For a current live answer, cross-check model availability with `timm.list_models(pretrained=True)` and model-specific pretrained config fields.

## Comparing Rows Safely

When comparing benchmark or result table rows, require alignment on:

- Same model variant and weight tag.
- Same input size and crop/test-size policy.
- Same batch size for throughput comparisons.
- Same device class, PyTorch/CUDA/runtime version, precision, layout, and compile state.
- Same benchmark mode: inference, train, or profile.
- Same dataset and label set for validation or robustness tables.

Do not mix `top1` validation accuracy and `infer_samples_per_sec` throughput into a single score unless the user explicitly defines a weighted objective.
