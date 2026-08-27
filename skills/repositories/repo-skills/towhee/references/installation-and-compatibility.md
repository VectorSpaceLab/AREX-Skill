# Installation and Compatibility

## Purpose

Read this when a task starts with installing Towhee, checking whether the active environment is usable, or deciding which optional dependency family is needed. This reference is self-contained for Towhee 1.1.x package operation.

## Base install

Towhee's public docs describe Python 3.7+ and the common pip install path:

```bash
pip install towhee
```

Many user workflows also need Hub/model operators. The README and install docs describe the separate model package:

```bash
pip install towhee.models
```

Do not install `towhee.models`, PyTorch, TensorFlow, Docker, Triton, or all test requirements unless the user's workflow specifically needs those surfaces.

## Minimal import and smoke check

From any shell where Towhee should be active:

```bash
python - <<'PY'
from towhee import AutoConfig, pipe
p = pipe.input('x').map('x', 'y', lambda x: x + 1).output('y')
print(p(2).get())
print(AutoConfig.LocalCPUConfig().config)
PY
```

Expected output includes `[3]` and `{'device': -1}`.

For a fuller no-network diagnostic, copy or run the bundled root helper from the generated skill tree:

```bash
python scripts/check_towhee_environment.py --verbose
```

The helper checks imports, a lambda pipeline, batch execution, `Entity.combine`, `APIService`, and CLI help. It does not download Hub operators, start services, run Docker/Triton, or train models.

## Compatibility facts verified during skill creation

- Distribution: `towhee` 1.1.3.
- Console scripts declared by package metadata: `towhee=towhee.command.cmdline:main`, `triton_builder=towhee.serve.triton.pipeline_builder:main`.
- Base runtime requirements from package metadata include `requests`, `tqdm`, `tabulate`, `numpy`, `twine`, `tenacity`, and `pydantic`.
- Towhee 1.1.x imports `pkg_resources`. Modern environments where `setuptools` no longer provides `pkg_resources` can fail at import time. Pin or install a compatible setuptools version, for example `pip install 'setuptools<81'`, when the error is `ModuleNotFoundError: No module named 'pkg_resources'`.
- The repository's own test requirements pin `pydantic<2`; prefer Pydantic v1 for old Towhee 1.1.x service/API workflows unless you have tested the specific deployment path on Pydantic v2.

## Optional dependency families

| Need | Add only when needed | Notes |
|---|---|---|
| Hub model operators and direct model imports | `towhee.models`, model-specific dependencies, often PyTorch or TensorFlow | May download model weights or operator code. Prefer pinned revisions and isolated caches for reproducibility. |
| `towhee.trainer` and `NNOperator.train()` | PyTorch, TorchVision, TorchMetrics, YAML helpers | Training can be CPU or CUDA; actual model training may download weights and take time. |
| HTTP service startup | FastAPI/Starlette/Uvicorn-like stack used by Towhee's service modules | Object-level `APIService` construction is safe without starting a listener; live server tests bind ports. |
| gRPC service startup | gRPC client/server dependencies | Use short-lived local processes only when explicitly requested. |
| Triton deployment | Docker, NVIDIA Triton image/server, `tritonclient`, CUDA/GPU for GPU paths | Building images/model repositories can create large artifacts and should not be routine validation. |
| Media processing operators | OpenCV/PIL/audio/video libraries, model-specific packages | Operators may install or download extra code through Towhee Hub. |

## Environment strategy

1. Start with the base `towhee` install and run the root helper.
2. If the task is only pipeline graph authoring, stay base-only and use local lambdas/callables until the graph shape is correct.
3. Add optional packages only for the owning workflow: model operators, training, live service, or Triton.
4. Do not treat a CPU import as proof that CUDA/Triton/Docker/model-download workflows work. Use the relevant sub-skill and plan those checks separately.
