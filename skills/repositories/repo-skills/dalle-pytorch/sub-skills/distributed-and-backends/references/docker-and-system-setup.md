# Docker and system setup notes

The repository included a Dockerfile based on an older PyTorch CUDA image and installed DeepSpeed from source. Treat this as a compatibility baseline, not as a command to run blindly.

## Docker workflow shape

A Docker-based workflow usually needs:

1. NVIDIA driver on the host.
2. NVIDIA container runtime or equivalent GPU passthrough.
3. A PyTorch CUDA image matching the desired torch/CUDA stack.
4. Source build tools for DeepSpeed ops if sparse attention is selected.
5. A bind mount for data/checkpoints.

Example command shape to discuss with the user:

```bash
docker build -t dalle <docker-context>
docker run --gpus all -it --mount src="$PWD",target=/workspace/dalle,type=bind dalle:latest bash
```

Do not run Docker builds without approval; they pull images, compile packages, and can consume large disk/network resources.

## Source-build prerequisites

DeepSpeed sparse attention and Apex AMP can require:

- compatible torch/CUDA versions;
- NVIDIA driver and CUDA runtime;
- `nvcc` for source builds;
- CMake, LLVM, GCC, and `libaio`-style system libraries;
- enough RAM and temporary disk for compilation.

A visible GPU is not enough; verify package ABI and toolkit availability before building.

## Modernization caution

The source baseline is old. Modern torch may work for `DiscreteVAE`, `DALLE`, and `CLIP`, but OpenAI VAE has a torch `<=1.10` assertion and old DeepSpeed sparse attention docs referenced `triton==0.4.2`. Avoid mixing old sparse-attention instructions with modern torch unless the user is prepared to debug ABI issues.
