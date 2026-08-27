# Analysis and Benchmarking

Detectron2 includes model-analysis and benchmarking entry points that are useful for deployment planning, but they can build models, load checkpoints, iterate over data loaders, and consume significant CPU/GPU time. Plan them separately from export.

## Safe Command Preview

Use the bundled analyzer command builder to validate tasks and print a command without importing Detectron2 or building a model:

```bash
python sub-skills/deployment-export/scripts/analyze_command_builder.py \
  --config-file CONFIG.yaml \
  --tasks parameter structure \
  --override MODEL.DEVICE=cpu
```

For data-dependent analysis:

```bash
python sub-skills/deployment-export/scripts/analyze_command_builder.py \
  --config-file CONFIG.yaml \
  --tasks flop activation \
  --num-inputs 10 \
  --override MODEL.WEIGHTS=WEIGHTS.pkl \
  --override MODEL.DEVICE=cpu
```

The helper prints a command shape and review notes only. It never starts analysis.

## Analysis Tasks

| Task | Needs data loader | Needs weights | Typical output | Safety notes |
|---|---:|---:|---|---|
| `parameter` | No | No | Parameter-count table | Safest static model-size check |
| `structure` | No | No | String representation of built model | Useful before export to confirm architecture |
| `flop` | Yes | Usually yes | Average GFLOPs by operator plus total | Data-dependent; requires valid test dataset/config or LazyConfig dataloader |
| `activation` | Yes | Usually yes | Activation counts by operator plus total | Data-dependent and can be memory-heavy |

Yacs configs build models through `build_model(cfg)` and test loaders through `build_detection_test_loader(cfg, cfg.DATASETS.TEST[0])`. LazyConfig paths instantiate `cfg.model` and `cfg.dataloader.test`, and load `cfg.train.init_checkpoint` for data-dependent tasks.

## Useful Analysis APIs

- `detectron2.utils.analysis.parameter_count_table(model, max_depth=5)` prints a parameter table.
- `detectron2.utils.analysis.parameter_count(model)` returns parameter counts by module prefix.
- `detectron2.utils.analysis.FlopCountAnalysis(model, data)` wraps fvcore flop analysis for Detectron2 inputs.
- `detectron2.utils.analysis.flop_count_operators(model, inputs)` returns operator-level FLOP counts for prepared inputs.
- `detectron2.utils.analysis.activation_count_operators(model, inputs)` returns activation counts.
- `detectron2.utils.analysis.find_unused_parameters(model, inputs)` helps diagnose unused modules before distributed training or export cleanup.

Random synthetic inputs can work for some tests, but proposal-dependent heads may not exercise all operations when random images produce few or no proposals. Treat data-dependent analysis as approximate unless it uses representative data.

## Benchmark Tasks

Benchmarking is not a correctness check. It measures throughput, dataloader cost, or training/eval loop behavior under specific hardware, config, and dataset conditions.

Common benchmark modes:

- `eval`: benchmarks single-GPU inference-like evaluation over repeated test samples; requires weights and a valid test loader.
- `train`: benchmarks a training loop with a finite dummy-data cache; uses optimizer and profiler hooks.
- `data`: benchmarks distributed dataloader throughput and RAM usage.
- `data_advanced`: breaks down dataset, mapper, workers, IPC, and distributed dataloader costs.

Benchmark runs can be expensive and hardware-sensitive. Ask before running them, especially with GPUs, multiple processes, large datasets, or profiler output. Keep results tied to the exact config, device count, batch size, worker count, input sizes, and machine class.

## Benchmark Safety Checklist

Before running any benchmark:

1. Confirm the user wants runtime measurement rather than command planning.
2. Confirm the dataset is available and small enough for the requested check.
3. Confirm weights are local or allowed to download through the configured path manager.
4. Confirm `num_gpus`, `num_machines`, and `dist_url` are intentional.
5. Confirm output/profiler directories are acceptable.
6. Record that numbers are not portable across hardware, PyTorch builds, CUDA/cuDNN settings, OpenCV variants, or dataloader worker counts.

## Export Validation vs. Benchmarking

Do not substitute a benchmark for export validation. A deployment artifact still needs a small correctness check against the eager model on representative inputs. For tracing exports, compare rebuilt outputs using the `TracingAdapter.outputs_schema` when possible. For Caffe2 exports, remember raw artifacts may omit Detectron2 post-processing, so compare at the compatible wrapper or application post-processing boundary.
