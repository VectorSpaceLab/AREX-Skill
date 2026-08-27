---
name: installation-and-launch
description: "Install ColossalAI, verify PyTorch/CUDA and optional extensions,
  and launch distributed jobs through ColossalAI CLI or launch APIs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Installation and Launch

Use this sub-skill when the task is about getting ColossalAI importable, interpreting `colossalai check -i`, using `colossalai run`, constructing hostfile or torchrun commands, or fixing distributed startup errors.

## Route Here

- Install `colossalai` from PyPI or source and decide whether `BUILD_EXT=1` is appropriate.
- Check Python, PyTorch, CUDA, GPU visibility, `CUDA_HOME`, and optional CUDA extension status.
- Use `colossalai check -i`, `colossalai --help`, `colossalai run --help`, or CLI launcher flags.
- Generate safe `colossalai run` commands for single-node, hostfile, include/exclude, extra launch args, or `-m` module mode.
- Use `colossalai.launch`, `launch_from_torch`, `launch_from_slurm`, or `launch_from_openmpi` inside scripts.

## Reroute

- Choosing `Booster` plugins or writing the training loop: use `../booster-training/SKILL.md`.
- Deciding tensor/pipeline/sequence parallel topology: use `../parallelism-and-sharding/SKILL.md`.
- LLM or diffusion generation/inference commands: use `../inference-and-serving/SKILL.md`.
- ColossalChat, ColossalQA, ColossalEval, Colossal-LLaMA, or ColossalMoE environment isolation: use `../application-recipes/SKILL.md`.

## Fast Start

```bash
python ../../scripts/check_colossalai_environment.py --check-cli
colossalai check -i
colossalai run --nproc_per_node 1 train.py --arg value
```

Inside a script launched with `torchrun` or `colossalai run`, initialize ColossalAI with:

```python
import colossalai
colossalai.launch_from_torch(seed=42)
```

For manual single-process initialization, pass explicit rank, world size, host, and port:

```python
colossalai.launch(rank=0, world_size=1, host="127.0.0.1", port=29500)
```

## References and Helpers

- `references/installation-and-backends.md` explains install variants, PyTorch/CUDA checks, and optional extension signals.
- `references/cli-and-launch.md` lists `colossalai run` flags, launch APIs, and safe command patterns.
- `references/troubleshooting.md` maps install, CLI, hostfile, environment-variable, port, and NCCL failures to recovery steps.
- `scripts/colossalai_launch_builder.py` safely builds launch commands without running the training script.

## Operating Rules

- Do not treat CPU import as proof of CUDA training or inference readiness.
- Do not install broad app/test requirements just to fix a core import problem.
- Do not run user training scripts from this sub-skill; generate or inspect commands, then route to the workflow owner.
- Use a unique `--master_port` for concurrent jobs or repeated test runs on shared hosts.
