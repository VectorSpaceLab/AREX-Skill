# Deployment Troubleshooting

## Artifact/runtime mismatch

| User has | But runtime expects | Result | Fix |
| --- | --- | --- | --- |
| `.ep` ExportedProgram | C++ TorchScript | C++ cannot load it as a TorchScript module. | Save `.ts` with runtime support or use Python load. |
| `.ts` TorchScript | Python-only wheel | Runtime library missing. | Install/build with Torch-TensorRT runtime or choose `.ep`. |
| `.pt2` AOTI package | Windows/non-AOTI runtime | Load failure. | Use Linux AOTI runtime or choose another artifact. |
| `.engine` raw TensorRT | PyTorch fallback required | Missing ops or wrong outputs. | Use `.ep`/compiled module with fallback or rewrite model. |
| TensorRT-RTX artifact/settings | Standard TensorRT runtime | Cache/settings unavailable or errors. | Match package flavor or remove RTX-only settings. |

## Triton model load failures

Check:

- Model repository path has `model_name/version/artifact` shape.
- `config.pbtxt` backend, platform, input/output names, dtypes, and shapes match the artifact.
- Triton container includes the same class of runtime dependencies used to create the artifact: TensorRT, PyTorch, Torch-TensorRT, TensorRT-RTX if applicable.
- Dynamic dimensions in Triton config do not exceed the TensorRT profile range.

## C++ deployment failures

- `libtorchtrt_runtime.so` / platform equivalent missing: install a runtime-enabled build and add libraries to the loader path.
- ABI or libtorch mismatch: build/save with matching PyTorch/libtorch versions.
- TensorRT deserialization failure: rebuild for compatible TensorRT version/GPU or use `hardware_compatible`/`version_compatible` where appropriate.

## Distributed failures

- Launcher parser errors: use `torchtrtrun --help` from the installed package; flags can change.
- NCCL missing: verify NCCL libraries or use an NGC/PyTorch container.
- Hangs: reduce to single node, two ranks, tiny model, and short timeout before running production models.
- Teardown crashes: keep TensorRT modules and distributed resources scoped cleanly; use `distributed_context` when appropriate.

## Platform-specific failures

- DLA errors on non-DLA hardware are expected. Use DLA only on supported embedded devices and FP16/INT8.
- Windows cross-compile must run from Linux x86-64 and target Windows x86-64; Windows ARM64 is a separate source-build workflow.
- TensorRT-RTX is experimental and RTX-targeted; test standard TensorRT when production behavior is required.

## Safe recovery response

When a deployment fails, ask for or collect:

- Artifact type and how it was produced.
- Build and target OS, GPU, CUDA, TensorRT, PyTorch, Torch-TensorRT versions.
- `ENABLED_FEATURES` and package flavor.
- Exact load command and error.
- One minimal input shape/dtype used to verify the artifact.

Then route to compile, runtime, extensibility, or build sub-skills if the failure source is not deployment packaging.
