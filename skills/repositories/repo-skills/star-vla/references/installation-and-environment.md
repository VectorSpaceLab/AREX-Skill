# Installation and Environment Guidance

## When to read

Read this before installing StarVLA dependencies, choosing CPU/GPU/ROCm/NPU packages, or interpreting import checks. StarVLA is an ML/robotics stack: a small CPU environment can inspect APIs, but real training/evaluation often needs large accelerator and simulator environments.

## Python and package baseline

- Package distribution name: `starVLA`.
- Import roots used by this skill: `starVLA` and `deployment`.
- Package metadata in the generation snapshot declares Python `>=3.10` and version `1.0.1`.
- Community docs commonly use Python 3.10 for training/evaluation environments; Python 3.11 is also suitable for inspection when wheels are available.
- Avoid Python 3.13 for StarVLA ML environments unless every compiled dependency has compatible wheels.

## Environment tiers

| Tier | Use it for | Typical contents | What it does not prove |
| --- | --- | --- | --- |
| CPU inspection | Reading APIs, registry/config inspection, safe validators, mocked native tests | Editable `starVLA`, CPU PyTorch/TorchVision, OmegaConf, Transformers, Pydantic/numpydantic, data IO, websocket/ZMQ packages | GPU training, flash-attn, simulator eval, checkpoint inference speed/correctness |
| StarVLA training/inference | Model instantiation, checkpoint loading, policy server, training | GPU-capable PyTorch/TorchVision, Transformers, Accelerate, DeepSpeed, optional flash-attn or torch_npu, VLM/world-model weights | Simulator/robot environment dependencies unless separately installed |
| Simulator evaluation | LIBERO, SimplerEnv, RoboCasa, RoboTwin, DOMINO, BEHAVIOR, VLA-Arena, Calvin, RoboDojo clients | Benchmark-specific simulator packages, MuJoCo/Vulkan/rendering libs, client dependencies, sometimes a separate Python version | StarVLA server dependencies unless installed in a separate server env |
| Real-robot deployment | Physical robot bridges, cameras, SDKs, control loops | Robot SDKs, camera drivers, network/service access, safety wrappers, checkpoint server | General benchmark reproducibility |

## Conservative install strategy

1. Start with an isolated environment. Do not mutate Conda `base` or a user's working training environment unless explicitly approved.
2. Install the backend foundation first: PyTorch/TorchVision CPU, CUDA, ROCm, NPU, or another vendor stack according to the selected workflow.
3. Install StarVLA and only the dependency groups needed for the task. Avoid broad dev or benchmark packages if the task is only inspection.
4. Run an import/backend smoke before model construction or server startup.
5. For full training/evaluation, prepare data/model caches and simulator envs separately; do not treat a server import as simulator readiness.

## Minimal inspection smoke

Use the root helper for a non-destructive check:

```bash
python /path/to/star-vla/scripts/check_starvla_install.py --json
```

If using a local checkout that is not installed, point the helper at it:

```bash
python /path/to/star-vla/scripts/check_starvla_install.py --repo-root /path/to/StarVLA-checkout
```

The helper imports core modules, reports package versions when available, and checks whether CUDA is visible to PyTorch. It does not instantiate large models, download weights, start servers, or run training.

## Backend selection rules

- **CUDA**: required for most practical training, large checkpoint inference, and benchmark evaluation throughput. Match PyTorch/TorchVision wheels to the host driver and Python version. Flash-attn must match the installed torch/CUDA ABI and may require `--no-build-isolation`.
- **ROCm**: community docs note AMD MI300X can work with an SDPA attention override. Treat ROCm as its own backend with ROCm PyTorch wheels; do not assume CUDA wheels work.
- **Ascend NPU**: StarVLA code has optional `torch_npu` import paths. Treat NPU as accelerator-specific and follow vendor PyTorch/toolchain guidance.
- **CPU**: acceptable for config parsing, registry inspection, and mocked tests. It is not an adequate substitute for GPU-only model construction or benchmark performance.

## Dependency surfaces by task

| Task | Required surfaces |
| --- | --- |
| Framework registry/config inspection | `starVLA`, PyTorch import, OmegaConf, source or installed package metadata |
| LeRobot data validation | JSON/YAML tooling for static schema checks; real loading additionally needs pandas/pyarrow/video backends and actual dataset files |
| Training command planning | YAML parser and no GPU required; actual training needs Accelerate, DeepSpeed, backend-specific torch, data, weights, W&B policy |
| Policy server startup | checkpoint, paired config/statistics, PyTorch backend, `websockets`/`websocket-client` or `pyzmq`, reachable port |
| Benchmark evaluation | running policy server plus separate benchmark client dependencies and renderer/simulator setup |
| Real robot bridge | policy server plus robot SDKs/cameras/controllers and safety gating |

## Safe environment checks

- Use `python -m pip check` after installing compiled dependencies.
- Import `starVLA.model.framework.base_framework` before trying to load model weights.
- Import `deployment.model_server.policy_wrapper` before starting a server.
- Run StarVLA-provided or bundled validators before long training/evaluation.
- For CUDA, verify `torch.cuda.is_available()`, device name, and a tiny tensor allocation in the target environment.

## Known dependency hazards

- `flash-attn` frequently fails when CUDA toolkit, driver, torch ABI, Python version, or GPU architecture do not match.
- Some benchmark clients pin old `numpy`, MuJoCo, Vulkan, or simulator versions; isolate them from the StarVLA server environment.
- Video backends (`decord`, `PyAV`, OpenCV, torchvision video) differ by platform. A dataloader import may pass while actual video decoding fails.
- `deepspeed` and accelerator extensions can compile or import slowly; install only when actual training requires them.
- Some source examples are intentionally environment-specific launchers. Convert them to a local plan instead of copying their path, NCCL, W&B, or GPU-count assumptions blindly.

## What to record in task notes

When preparing a real execution environment, record:

- Python version and manager.
- Backend target and verified torch/backend version.
- Whether pretrained weights and dataset files are local or need network access.
- Benchmark or robot environment names and versions.
- Exact config YAML and overrides.
- Which smoke checks passed and which optional capabilities remain unverified.

Do not bake private paths, activation commands, tokens, proxy settings, or machine-specific cache locations into generated code or reusable instructions.
