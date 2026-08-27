# Runtime and Test Selection

## Runtime baseline

FastVideo is Python 3.12+ and GPU-oriented. Follow repository docs for the exact
backend, for example:

```bash
UV_TORCH_BACKEND=cu126 uv pip install -e ".[dev]"
```

Use `cu130` instead only when the host and docs require it. A CPU-only install is
acceptable for parser/schema/documentation work, but not for claims about model
generation, CUDA kernels, SSIM, or training.

Safe runtime probes:

```bash
python -m pip check
python skills/disco/fastvideo/scripts/verify_fastvideo_runtime.py
python skills/disco/fastvideo/scripts/verify_fastvideo_runtime.py --cuda
fastvideo --help
fastvideo generate --help
fastvideo serve --help
fastvideo router-serve --help
```

## Construction verification summary

During skill construction, a private Conda Python 3.12.13 environment installed
FastVideo editable with `UV_TORCH_BACKEND=cu126`. `pip check` passed, `torch
2.12.0+cu126` allocated a CUDA tensor on A100 hardware, `fastvideo_kernel`
imported from the installed wheel, and CLI/help/import probes passed. Full model
runs, SSIM, training, `fastvideo-kernel` source rebuild, and Dreamverse production
deployment were intentionally not run.

This summary proves the skill was built from runtime evidence; it is not a
portable promise about another machine.

## Test-selection ladder

Choose the narrowest test that covers the touched behavior.

### API and CLI config

```bash
pytest fastvideo/tests/api/test_cli_translation.py -q
pytest fastvideo/tests/api/ -q
fastvideo generate --help
fastvideo serve --help
fastvideo router-serve --help
```

### Public generator and servers

```bash
pytest fastvideo/tests/entrypoints/test_video_generator.py -q
pytest fastvideo/tests/entrypoints/test_openai_api.py -q
pytest fastvideo/tests/entrypoints/streaming/test_server.py -q
pytest fastvideo/tests/entrypoints/streaming/test_prompt_providers.py -q
```

### Attention/backend selection

```bash
pytest fastvideo/tests/attention/test_selector_role_override.py -q
pytest fastvideo/tests/attention/ -q
```

For actual backend kernels, confirm the backend package, GPU architecture,
CUDA/runtime tag, and docs first.

### Model-porting

```bash
python skills/disco/fastvideo/scripts/select_fastvideo_tests.py model-porting
pytest fastvideo/tests/golden_gate/ -q
pytest fastvideo/tests/train/models/ -q
```

Then read and run only the model-specific `tests/local_tests/<family>/README.md`
command that matches the target model/backend.

### Training

```bash
python skills/disco/fastvideo/scripts/select_fastvideo_tests.py training
pytest fastvideo/tests/train/methods/test_wan_finetune.py -q
pytest fastvideo/tests/train/ -q
pytest fastvideo/tests/dataset/ -q
```

Distributed, full training, and Slurm commands require explicit hardware and
runtime budget.

### Dreamverse

```bash
dreamverse-server --help
dreamverse-mock-server --help
pytest apps/dreamverse/dreamverse/tests/test_entrypoints.py -q
pytest apps/dreamverse/dreamverse/tests/test_mock_server.py -q
pytest apps/dreamverse/dreamverse/tests/test_gpu_pool.py -q
pytest fastvideo/tests/contract/test_dreamverse_shape.py -q
```

### SSIM / generation quality

```bash
pytest fastvideo/tests/ssim/ -vs
```

Run this only when output quality is part of acceptance and reference assets,
model weights, and GPU budget are available.

## Backend gates

- CUDA required: generation, SSIM, most training, kernel/runtime backends, and
  many model-porting parity tests.
- CPU acceptable: parser/schema tests, safe imports, CLI `--help`, docs-only
  checks, and some mock/server contract tests.
- External services/credentials required: Dreamverse production providers,
  Modal deployments, Hugging Face private models, W&B logging, and some download
  scripts.
- Source build tools required: `fastvideo-kernel/` rebuilds need the appropriate
  compiler/CUDA toolkit; a prebuilt wheel import is a different claim.

## Reporting skipped tests

When skipping a heavier native case, say exactly why:

- missing model weights or dataset;
- external credentials not available;
- GPU memory/count does not match the docs;
- runtime budget not approved;
- source build toolkit absent;
- test is unrelated to touched files.

Do not write “not run” without a reason.
