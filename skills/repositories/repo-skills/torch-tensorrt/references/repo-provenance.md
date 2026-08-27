# Torch-TensorRT Repo Provenance

- schema: `disco.repo-provenance.v1`
- generated skill id: `torch-tensorrt`
- source repository: `https://github.com/pytorch/TensorRT.git`
- source project branding: Torch-TensorRT
- source commit: `c1d7a4ee1c238fea68db4dbf412e5d997f12d62e`
- source branch at extraction: `main`
- exact tag at extraction: none reported
- version file: `version.txt` reported `2.14.0a0`
- public Python package names: `torch-tensorrt`, `torch-tensorrt-rtx`
- import package: `torch_tensorrt`
- console entry point: `torchtrtrun`
- generation policy: `auto decide and not import`
- runtime output path in the source tree: `skills/disco/torch-tensorrt/`
- review artifacts path in the source tree: `skills/tests/torch-tensorrt/`

## Working tree state at extraction

The original checkout was otherwise unmodified before skill generation; untracked files are the generated skill and review artifacts under `skills/disco/torch-tensorrt/` and `skills/tests/torch-tensorrt/`.

## Evidence retained

Primary public evidence categories retained for this skill:

- Top-level purpose, install, quickstart, platform support, dependency versions: `README.md`, `version.txt`, `pyproject.toml`, `setup.py`, `dev_dep_versions.yml`.
- Python package source and feature gates: `py/torch_tensorrt/__init__.py`, `_compile.py`, `_Input.py`, `_Device.py`, `_features.py`, `dynamo/`, `runtime/`, `kernels/`, `distributed/run/`.
- Getting-started and compilation docs: `docsrc/getting_started/installation.rst`, `docsrc/getting_started/quick_start.rst`, `docsrc/getting_started/tensorrt_rtx.rst`, `docsrc/user_guide/compilation/`.
- Runtime optimization docs: `docsrc/user_guide/runtime_performance/`, `docsrc/tutorials/runtime_opt/`, `docsrc/tutorials/resource_memory/`, `docsrc/tutorials/weight_refit/`.
- Deployment docs/examples: `docsrc/tutorials/deployment/`, `docsrc/ts/getting_started_with_cpp_api.rst`, `docsrc/user_guide/runtime_performance/aot_inductor.rst`, `docsrc/user_guide/runtime_performance/serialized_engine.rst`, `docsrc/user_guide/runtime_performance/using_dla.rst`, `examples/triton/`, `examples/torchtrt_aoti_example/`, `examples/torchtrt_runtime_example/`, `examples/torchtrt_executorch_example/`, `examples/distributed_inference/`.
- Debugging/extensibility evidence: `docsrc/debugging/`, `docsrc/tutorials/compilation_analysis/`, `docsrc/tutorials/extensibility/`, `docsrc/py_api/kernels.rst`, `examples/dynamo/debugger_example.py`, `examples/dynamo/auto_generate_converters.py`, `examples/dynamo/custom_kernel_plugins.py`.
- Build/test/maintenance evidence: `CONTRIBUTING.md`, `tests/README.md`, `tests/NOTES.md`, `tests/ci/suites.py`, `justfile`, `noxfile.py`, Bazel/CMake files, `packaging/`, `docker/`.

## Evidence excluded or reduced

- Generated HTML documentation, caches, build outputs, lock/cache directories, vendored dependencies, and `third_party/` were excluded from runtime content.
- Large tests, benchmarks, model downloads, Triton server execution, distributed multirank jobs, C++/Bazel builds, ExecuTorch full export, QDP plugin execution, and quantization runs were treated as optional or blocked verification candidates rather than mandatory runtime examples.
- Source repository files are not runtime dependencies for this generated skill. Important workflow knowledge was distilled into bundled references and helper scripts.

## Installed-package inspection summary

A package inspection environment imported `torch_tensorrt` and captured public API signatures. The proved runtime was partial:

- CUDA hardware was present and a tiny CUDA allocation succeeded.
- TensorRT-RTX package import succeeded and a tiny Dynamo compile/execute smoke succeeded under a Python-only TensorRT-RTX build.
- Standard TensorRT wheel installation did not finish in the available time because the NVIDIA `tensorrt_cu13_libs` wheel was very large.
- `pip check` did not pass in the inspection environment because the inherited PyTorch version did not satisfy the local wheel metadata and unrelated inherited packages had dependency conflicts.
- TorchScript frontend, C++ runtime, QDP plugin, ModelOpt quantization, standard TensorRT, distributed/NCCL runtime, and save/load serialization execution were not fully verified in that environment.

Future users should verify the exact backend they intend to use with `scripts/check_torch_tensorrt_env.py` and any task-specific smoke test before relying on performance, serialization, distributed, plugin, or platform-specific behavior.
