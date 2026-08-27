---
name: backend-extension
description: "Tune LMDeploy PyTorch/TurboMind backend configs and extend PyTorch
  model/backend support safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# LMDeploy Backend Extension

Use this sub-skill when the task is about advanced LMDeploy backend selection, PyTorch/TurboMind engine tuning, scheduler/cache behavior, TurboMind build/runtime failures, or maintainer workflows for adding PyTorch model support.

Route elsewhere when the task is mainly:

- Basic offline text generation or prompt batching: use `pipeline-inference`.
- OpenAI-compatible API server, proxy, or client usage: use `serving-apis`.
- `lmdeploy lite` quantization artifact creation: use `quantization`.
- Images, video, multimodal messages, or VLM media loading: use `vision-language`.

## Start Here

1. Identify whether the user is tuning an existing deployment, selecting PyTorch vs TurboMind, debugging a backend/build failure, or adding model support.
2. For config tuning, read `references/backend-config.md` first, then `references/turbomind-config.md` for TurboMind-specific cache/config.ini details.
3. For new PyTorch model support, read `references/new-model-support.md` before editing model/configuration/registration code.
4. For import/build/runtime symptoms, read `references/troubleshooting.md` and run the smallest safe probe before changing dependencies or rebuilding.
5. Use `scripts/inspect_backend_config.py` to inspect installed `PytorchEngineConfig`, `TurbomindEngineConfig`, `QuantPolicy`, and module-map keys without loading model weights.

## Safe Probes

```bash
python scripts/inspect_backend_config.py --help
python scripts/inspect_backend_config.py --json --filter qwen
python -m lmdeploy check_env
```

If working inside an LMDeploy source checkout after backend/model edits, prefer targeted validation before broad tests:

```bash
pytest tests/pytorch/config/test_model_config.py
pytest tests/pytorch/paging/test_scheduler.py
```

## Key References

- `references/backend-config.md`: backend choice, high-value config fields, scheduler/cache knobs, and validation patterns.
- `references/turbomind-config.md`: TurboMind config.ini concepts, cache block sizing, prefix caching, and KV quant policy.
- `references/new-model-support.md`: PyTorch model patching, configuration builders, `custom_module_map`, model methods, and focused tests.
- `references/troubleshooting.md`: missing `_turbomind`, CUDA/NCCL/runtime mismatches, OOM cache tuning, multiprocessing guards, and source-build choices.
