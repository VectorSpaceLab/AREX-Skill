# Dependency and Backend Guidance

Use this reference before installing NeMo Speech for repository development or diagnosing optional dependency failures. Choose the smallest dependency set that can validate the changed area.

## Baseline Facts

- Package name: `nemo-toolkit`.
- Verified generation-time version: `3.1.0+8f85359`.
- Package metadata declares Python `>=3.10` and `torch>=2.6.0`, but current NeMo Speech docs target Python 3.12+, PyTorch 2.7+, and GPU/CUDA for training.
- Current docs describe Python 3.13, PyTorch 2.12, and CUDA 12.6/13.2 as the actively tested lock/container baseline, not as the only valid runtime.
- Training requires NVIDIA GPU + CUDA. CPU-only inference may be possible but is slow and not suitable for most maintainer validation of training paths.
- Package metadata exposes no console entry points for general CLI use. Most workflows are Python APIs or Hydra example scripts rather than installed commands.
- A vLLM plugin entry point named `nemo_speechlm` is declared for SpeechLM2 vLLM integration.

## Extras and Groups

Collection extras are for runtime capabilities:

- `asr`: ASR models, Lhotse, audio libraries, decoding/evaluation dependencies, and shared Lightning/Hydra stack.
- `tts`: TTS/vocoder/audio codec dependencies plus ASR/common/shared pieces used by TTS.
- `audio`: audio enhancement/separation dependencies, metrics, Lhotse, and shared stack.
- `speechlm2`: NeMo Automodel, FlashOptim, PEFT, ASR/common/TTS-adjacent pieces needed by SpeechLM2.
- `all`: broad collection coverage.
- `cu12` / `cu13`: pinned PyTorch/CUDA wheel choices for Linux. Pick exactly one.
- `compiled` / `compiled-a100`: optional source-built accelerated backends. Pick at most one and prefer container builds.

Dependency groups are not extras:

- `test`: Black, isort, pytest, coverage, pytest plugins, Sphinx, and related test tooling.
- `docs`: Sphinx theme/extensions and docs build dependencies.

Do not install `.[test]` or `.[docs]`; use dependency-group syntax in uv workflows.

## Recommended Install Patterns

For source development with the supported stack:

```bash
uv sync --extra all --extra cu13
```

For tests:

```bash
uv sync --extra all --extra cu13 --group test
```

For docs:

```bash
uv sync --locked --group docs
```

For an exact lock/container-like environment:

```bash
uv sync --locked --python 3.13 --extra all --extra cu13
```

For bring-your-own PyTorch/CUDA:

```bash
uv venv --python 3.12
uv pip install torch --index-url https://download.pytorch.org/whl/cu126
uv pip install 'nemo-toolkit[asr,tts]'
```

Use `pip` similarly if the environment already has the desired Python/PyTorch stack. Avoid `uv sync --locked` in bring-your-own environments because it intentionally applies the project lock and can replace PyTorch/CUDA.

## Optional Compiled Backends

SpeechLM2/Automodel can run without compiled dependencies. The compiled extras are optional performance accelerators for specific GPU stacks:

- `compiled`: Hopper/Blackwell and newer, such as H100/H200/B200. Includes Transformer Engine, FlashAttention, Mamba/state-space kernels, grouped GEMM/MoE, DeepEP, and ONNX export tooling.
- `compiled-a100`: A100-focused variant. It omits or adjusts pieces that require special A100 handling.

These packages may build from source and require a full CUDA build environment, architecture flags, no-build-isolation behavior, and Dockerfile-managed patches. For maintainers, do not install compiled extras for ordinary formatting, docs, CPU unit tests, manifest validation, or non-SpeechLM2 changes. Prefer the repository’s container build path when a compiled-backend bug must be reproduced.

## CUDA and PyTorch Mismatch Signals

Common symptoms:

- `torch.cuda.is_available()` is false while GPU tests are expected.
- CUDA extension import errors mention missing symbols, incompatible CUDA runtime, or unsupported architecture.
- `numba`/CUDA checks fail in tests that use Numba-backed kernels.
- k2 or other optional libraries import but report no CUDA support.
- FlashAttention, Mamba, Transformer Engine, DeepEP, or grouped GEMM fail during import or wheel build.

Triage steps:

1. Verify Python, PyTorch, and CUDA versions in the active environment.
2. Confirm the install path: uv locked stack, bring-your-own pip/uv pip, Docker, or collection-only install.
3. Check that only one CUDA extra was selected.
4. For compiled backend issues, confirm the GPU target and whether a container build is required.
5. For CPU-safe validation, rerun the focused test with `--cpu` when the suite supports it and the behavior is not GPU-specific.

## Optional Import Patterns

NeMo source uses optional dependency helpers and collection-local imports. When adding optional features:

- Keep optional imports lazy when the dependency is not required for the base package import.
- Produce actionable error messages that name the missing extra or backend family.
- Add CPU-safe tests for error messages and validation logic where possible.
- Do not make top-level `import nemo` or unrelated collection imports require heavy optional packages.
- If a new dependency is needed only by one collection, keep it in that collection extra instead of broadening the base dependency set.

## Checkpoint Loading Safety

Current PyTorch defaults may use `weights_only=True` for `torch.load`. Some trusted legacy checkpoints may require `weights_only=False`; docs describe `TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1` as an escape hatch. Only use this with trusted checkpoint files because full pickle loading can execute arbitrary code.

## Environment Hygiene

- Do not leak local virtualenv paths, conda prefixes, Python executable paths, or checkout paths into public docs, generated skills, examples, or user-facing error messages.
- Do not mutate a user-provided existing environment to repair dependency conflicts without asking.
- Prefer adding a minimal extra/group to reproduce a failure rather than installing `all`, CUDA, compiled, test, and docs dependencies together.
