# Distributed Inference

Torch-TensorRT includes distributed inference support around `torchtrtrun`, `torch_tensorrt.distributed.run`, TensorRT collectives, and NCCL setup. Treat this as GPU/distributed runtime work; do not launch multirank jobs unless the user asks and resources are reserved.

## When to use

- User has tensor-parallel or distributed PyTorch inference modules compiled with Torch-TensorRT.
- User mentions `torchtrtrun`, NCCL, TensorRT collectives, `distributed_context`, rank/world-size environment variables, or teardown issues in distributed inference.
- User needs to wrap a script launch rather than manually constructing `torchrun` commands.

## Basic launcher shape

Inspect the installed launcher first:

```bash
torchtrtrun --help
```

A real launch is task-specific and may look like:

```bash
torchtrtrun --nproc-per-node 2 path/to/inference_script.py --model my_model
```

Use the installed `--help` output for exact flags; avoid guessing if the user's version differs.

## `distributed_context`

Use `torch_tensorrt.dynamo.runtime.distributed_context` around distributed compilation/execution when the workflow requires Torch-TensorRT to coordinate distributed resources and cleanup.

Practical rule: keep initialization, compile/use, and teardown in one clear scope; avoid leaving NCCL communicators alive after TensorRT engine/module destruction.

## Environment checks

Use the bundled probe before launching workers:

```bash
python scripts/torchtrtrun_env_probe.py
```

It reports import state, CUDA device count, NCCL library hints, and launcher presence without spawning distributed workers.

## Native collectives vs TRT-LLM fallback

Feature gates:

- `ENABLED_FEATURES.native_trt_collectives`: TensorRT native collectives are available.
- `ENABLED_FEATURES.trtllm_for_nccl`: TRT-LLM fallback for NCCL is available.

If both are false, distributed TensorRT collective support is not proven. The user may still run PyTorch distributed code, but Torch-TensorRT collective-specific optimizations should be treated as unavailable until verified.

## Troubleshooting

| Symptom | Likely cause | Action |
| --- | --- | --- |
| Launcher not found | Console script not installed. | Use `python -m torch_tensorrt.distributed.run --help` if available or reinstall package. |
| NCCL library missing | NCCL not installed or not discoverable. | Inspect library path, package install, container runtime, or use an NGC/PyTorch container. |
| Hang at startup | Rank/world-size/env mismatch or blocked GPU. | Test `torchrun`/NCCL separately with a tiny script and reserve GPUs. |
| Failure on teardown | Communicators or modules outlive process group/runtime context. | Use a clear `distributed_context` scope and destroy process groups after module cleanup. |
| TensorRT collectives unavailable | Feature gates false or runtime library missing. | Rebuild/reinstall with required TensorRT/NCCL/TRT-LLM support or avoid TRT collective path. |

## Safety

Distributed jobs can reserve many GPUs and hang. Always ask before running multi-rank commands, set short timeouts for smoke tests, and avoid networked multi-node assumptions unless explicitly provided.
