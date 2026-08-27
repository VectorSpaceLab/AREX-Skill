---
name: megatron-lm
description: "Verified operating guidance for Megatron-LM and Megatron Core
  installation, distributed training, model parallelism, data, checkpoints,
  inference, optional RL/multimodal workflows, and repository maintenance."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# Megatron-LM

Use this repo skill when a task names Megatron-LM, Megatron Core, `megatron.core`, `megatron.training`, `pretrain_gpt.py`, Megatron distributed checkpoints, TP/PP/CP/EP/FSDP, Megatron inference, ModelOpt, Megatron RL, or this repository's CI/test workflows.

## Mandatory first steps

1. Pull the task artifact first: command, traceback, config, checkpoint metadata, PR diff, CI URL/log, or data sample.
2. Read [references/capability-map.md](references/capability-map.md) to choose the narrowest route.
3. Read [references/troubleshooting.md](references/troubleshooting.md) for cross-cutting constraints.
4. Load exactly the owning sub-skill and its linked references before proposing commands or code changes.
5. Verify the active environment with the install route before claiming CUDA, TE, FP8, FSDP, or distributed behavior.

## Minimal install and environment probe

For package use, the public install surface is:

```bash
uv pip install megatron-core
python -c "import megatron.core as m; print(m.__version__)"
```

For source-checkout development, use an isolated Python environment and install the checkout editable:

```bash
uv pip install -e .
python -m pip check
python -c "import megatron.core as m; print(m.__version__)"
```

For package/import/backend questions, run the bundled probe at [sub-skills/install-and-environment/scripts/check_megatron_environment.py](sub-skills/install-and-environment/scripts/check_megatron_environment.py):

```bash
python sub-skills/install-and-environment/scripts/check_megatron_environment.py --check-cuda
```

A CPU import is not evidence for NCCL, multi-GPU training, CUDA graphs, FP8, TransformerEngine, ModelOpt, or H100/GB200 behavior. Optional dependency warnings are evidence to classify the workflow, not errors to hide.

## Route the task

| User intent | Read |
|---|---|
| Install, import, Torch/CUDA, container, optional extras, build failure | [sub-skills/install-and-environment/SKILL.md](sub-skills/install-and-environment/SKILL.md) |
| `TransformerConfig`, GPT/Hybrid/Mamba model construction, TP/PP/CP/EP/DP/FSDP choice, process groups | [sub-skills/core-models-and-parallelism/SKILL.md](sub-skills/core-models-and-parallelism/SKILL.md) |
| Pretraining, `torch.distributed.run`, SLURM, tokenizer/data preprocessing, cache, mock data | [sub-skills/training-cli-and-data/SKILL.md](sub-skills/training-cli-and-data/SKILL.md) |
| Save/load/resume, `torch_dist`, `fsdp_dtensor`, safe loading, GPT↔Hybrid/HF conversion | [sub-skills/checkpointing-and-conversion/SKILL.md](sub-skills/checkpointing-and-conversion/SKILL.md) |
| Offline generation, `MegatronLLM`, coordinator mode, OpenAI-compatible server | [sub-skills/inference-and-serving/SKILL.md](sub-skills/inference-and-serving/SKILL.md) |
| ModelOpt, GRPO/RL, VLM, multimodal, MIMO, optional post-training | [sub-skills/post-training-rl-and-multimodal/SKILL.md](sub-skills/post-training-rl-and-multimodal/SKILL.md) |
| Unit/functional tests, recipes, golden drift, CI, linting, PRs, base image, nightly sync | [sub-skills/testing-ci-and-maintenance/SKILL.md](sub-skills/testing-ci-and-maintenance/SKILL.md) |

## Cross-route rules

- Choose topology with `core-models-and-parallelism` before finalizing a training, inference, checkpoint, or RL command.
- Choose checkpoint format and resume semantics with `checkpointing-and-conversion` before changing parallelism or loading optimizer state.
- Choose environment/optional dependencies with `install-and-environment`; do not install all extras as a substitute for diagnosis.
- Treat H100/GB200/FP8-specific claims as hardware-specific. A successful A100 or CPU check does not validate them.
- For CI/container changes, use `testing-ci-and-maintenance`; `dev` is the default lane and LTS is opt-in only when explicitly requested.
- Keep destructive/credentialed operations gated: internal CI triggers, GitHub writes, checkpoint overwrites, external servers, and large training runs require explicit task authorization.

## Default operating sequence

For a new task, preserve this order:

1. Normalize the requested deliverable: package answer, code change, training run, inference service, checkpoint operation, or CI/PR operation.
2. Identify the backend and evidence boundary: CPU-only, CUDA, optional fused kernels, external checkpoint/data, credentials, or remote CI.
3. Pull the relevant artifact and inspect it before reasoning: config, command, traceback, checkpoint metadata, recipe, or diff.
4. Read the owning sub-skill and references; use bundled renderers/probes before invoking source-repo commands.
5. Make topology and checkpoint decisions explicit before assembling a long command.
6. Run the smallest safe smoke: import/parser, tiny fixture, weights-only load, or two-GPU mock run.
7. Scale only after the smoke produces the expected signal; preserve logs and first failure evidence.

## Approval and side-effect gates

Ask or require explicit authorization before:

- installing broad optional dependencies or mutating a user-owned environment;
- starting long-running training, external-facing servers, or large conversions;
- overwriting checkpoints, datasets, goldens, or dependency locks;
- using credentials, downloading private/external artifacts, or invoking remote CI;
- pushing branches, opening PRs/issues, or triggering the internal GitLab force-push helper.

## Runtime boundaries

This graph distills public repository evidence into self-contained references and safe command renderers. It does not replace the Megatron-LM checkout for executing repo-owned training/tests, nor does it claim every model, accelerator, benchmark, or optional integration is verified. The source snapshot and known limitations are recorded in [references/repo-provenance.md](references/repo-provenance.md) and [references/troubleshooting.md](references/troubleshooting.md).
