# Backend matrix

## Base package

The base package installs Python modules and common dependencies but does not make every simulator runnable. Base imports are useful for config inspection, parser checks, package metadata, and many pure helper tests.

## MuJoCo

- Use for CPU debugging, fast parser checks, standalone deployment validation, and some sim2sim tests.
- It is CPU-only in the docs and generally single-env (`--num-envs 1`).
- Requires `mujoco`, `onnxruntime` for deployment validation, and package dependencies.
- Good smoke: import `mujoco`, run `protomotions info --json`, then perform headless CLI/help checks.

## Newton

- GPU-accelerated stack built on NVIDIA Warp.
- Requires Python 3.10+; Python 3.11+ is easier for wheels.
- Requires NVIDIA GPU compute capability at least 5.0 and driver 545+.
- Install CUDA-capable torch from the appropriate PyTorch wheel index before Newton/Warp dependencies.
- Native runtime checks should prove `torch.cuda.is_available()`, tiny CUDA allocation, and Newton/Warp import/device selection.

## IsaacLab

- ProtoMotions targets IsaacLab 12.0.0 / Isaac Sim 6.0 from the documented pinned IsaacLab commit.
- Requires Python 3.12 on Linux x86_64.
- Create the IsaacLab workspace first, install its Isaac Sim extra, then install ProtoMotions into that environment.
- IsaacLab/IsaacSim may need unattended EULA opt-in for headless jobs.
- Import IsaacLab before torch. ProtoMotions validates installed IsaacLab version early.

## IsaacGym

- Legacy GPU backend; requires Python 3.8.
- NVIDIA IsaacGym Preview 4 must be downloaded and installed manually.
- Import IsaacGym before torch.
- Not compatible with many modern package-only Python stacks.

## Genesis

- Experimental backend.
- Use a separate Python 3.10 environment and install Genesis according to its own docs before ProtoMotions Genesis dependencies.
- Treat successful import as insufficient; run a tiny backend smoke before claiming coverage.

## PyRoki retargeting

- PyRoki uses a separate JAX/CUDA dependency stack from ProtoMotions.
- Retargeting pipelines require both a ProtoMotions Python and a PyRoki Python.
- Use `--skip-existing` and small skip frequencies during interrupted or exploratory batch retargeting.

## Backend claims

A CPU package check can verify package importability, CLI parsers, config objects, and some pure deployment helpers. It cannot verify GPU simulator runtime, Isaac Sim conversion, Newton device allocation, or PyRoki optimization.
