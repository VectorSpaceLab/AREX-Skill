# Build and Maintenance Troubleshooting

## Typical build failures

| Symptom | Likely cause | Next action |
| --- | --- | --- |
| `pip install .` fails during wheel build | Missing build prerequisites or wrong variant flags. | Check `build-and-test.md` and `package-variants.md` first. |
| Import works but TorchScript/C++ runtime APIs fail | Python-only build or no-TorchScript build. | Choose the correct build variant or stop promising C++ support. |
| Wheel builds but runtime version checks fail | PyTorch/CUDA/TensorRT family mismatch. | Align the build environment to the package metadata. |
| Windows ARM64 build fails | Wrong host/target Python or missing Visual Studio/CUDA prerequisites. | Follow the Windows ARM64 build flow exactly. |
| JetPack build fails | Wrong JetPack/CUDA/PyTorch combination. | Check the target platform notes and use the documented container/wheel family. |

## Safe diagnostic order

1. Print the Python version and active environment.
2. Probe `torch`, `torch_tensorrt`, and optional runtime packages.
3. Check the intended build flags and target platform.
4. Verify Bazel/Bazelisk and compiler/toolchain availability.
5. Run the smallest build probe before recommending a large build.

## When to stop and ask the user

Stop and ask if:

- the requested build requires a host-level install that the session cannot perform safely,
- the environment lacks the necessary GPU/toolchain backend,
- the user did not authorize mutation of a working environment,
- the chosen variant is inconsistent with the user's target artifact.
