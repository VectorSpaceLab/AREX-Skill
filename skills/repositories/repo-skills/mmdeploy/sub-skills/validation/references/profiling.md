# Latency Profiling with `profiler.py`

## Purpose

Read this when the task is to measure backend or PyTorch inference latency, not to evaluate dataset metrics. Use the bundled [profiler helper](../scripts/profiler.py) for warmup-controlled, iteration-controlled latency reports.

## Command shape

```bash
python path/to/validation/scripts/profiler.py \
  <deploy-cfg> \
  <model-cfg> \
  <image-dir> \
  --model <backend-or-pytorch-model-file> [<extra-backend-file> ...] \
  --device <cpu-or-backend-device> \
  [--shape HxW] \
  [--warmup <n>] \
  [--num-iter <n>] \
  [--batch-size <n>] \
  [--cfg-options key=value ...] \
  [--img-ext .jpg .png ...]
```

Use absolute paths or run from a checkout where configs, images, and model files resolve. Keep profiling output outside the runtime skill tree.

## Argument behavior

| Argument | Meaning | Practical guidance |
| --- | --- | --- |
| `deploy_cfg` | Deployment config used to build the task processor and infer backend type. | Must match the backend files passed to `--model`. |
| `model_cfg` | OpenMMLab model config used for preprocessing and task input construction. | The codebase package and any custom modules required by the config must be importable. |
| `image_dir` | Directory recursively scanned for input images. | If it contains too few images, the helper repeats images using a fixed NumPy seed to fill warmup plus measured iterations. |
| `--model` | Backend model files, or a PyTorch `.pth`/`.pt` model. | `.pth`/`.pt` is treated as PyTorch; other suffixes use the backend from `deploy_cfg`. Multi-file backends need all files. |
| `--device` | Inference device. Default is GPU-style. | Use `cpu` for CPU backends or when GPU packages are unavailable. Non-CPU timing enables device synchronization and cuDNN benchmark mode. |
| `--shape HxW` | Override input shape for profiling. | Shape text is height-by-width, but MMDeploy's input shape is stored internally as width-by-height. If omitted, the deploy config must provide an input shape. |
| `--warmup` | Number of warmup iterations before collecting timing. | Default is 10; increase it for GPU or edge devices with startup overhead. |
| `--num-iter` | Number of measured iterations. | Default is 100. Use enough iterations for stable averages, but avoid unbounded runs on slow edge devices. |
| `--batch-size` | Number of images per timed step. | TimeCounter divides elapsed time by batch size and reports per-image latency. Do not use a batch size that the exported engine shape range cannot accept. |
| `--cfg-options` | MMEngine-style config overrides. | Same quoting rules as evaluation: list/tuple overrides must be quoted and contain no spaces. |
| `--img-ext` | Image extensions to collect. | Add custom suffixes if the image directory is valid but the helper reports no images. |

## Output and latency scope

The helper prints a settings table followed by a TimeCounter result table:

```text
----- Settings:
batch size | <n>
shape      | <HxW>
iterations | <num-iter>
warmup     | <warmup>
----- Results:
Stats | Latency/ms | FPS
Mean  | ...        | ...
Median| ...        | ...
Min   | ...        | ...
Max   | ...        | ...
```

Interpret these values as latency of `model.test_step(data)` over prepared inputs from the task processor. They are not dataset metrics and they do not prove numerical equivalence. For metric validation, use [evaluation](evaluation.md) or [regression](regression.md).

## Choosing between `test.py` and `profiler.py`

- Use `test.py --speed-test` when the user wants metrics and a speed log in the same evaluation loop.
- Use `profiler.py` when the user only needs latency/FPS, wants explicit `--num-iter`, or wants to profile a PyTorch checkpoint against a backend artifact with the same preprocessing path.
- If the user asks for custom batch size, verify backend shape support first, run metrics with `test.py`, then run latency-only profiling with the same batch size only if the backend accepts it.
