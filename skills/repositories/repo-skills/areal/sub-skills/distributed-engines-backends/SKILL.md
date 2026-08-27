---
name: distributed-engines-backends
description: "Plan and debug AReaL distributed engines, inference backends,
  allocation strings, weight sync, LoRA/FP8, and GPU/Ray/Slurm backend
  failures."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# distributed-engines-backends

Use this sub-skill when the task is about AReaL backend selection or backend failure modes: FSDP2, Megatron, Archon, SGLang, vLLM, backend strings, GPU allocation, parallelism dimensions, weight-update modes, LoRA, FP8, CUDA/NCCL hangs, OOM, Ray/Slurm placement, or backend install variants.

## Route first

- If the user needs a full experiment command, config migration, algorithm recipe, or which training script/workflow to run, route to sibling sub-skill `post-training-experiments` and return here only for the backend fields.
- If the user needs to start/stop/register/debug AReaL v2 services, gateways, workers, sessions, or CLI process lifecycle, route to sibling sub-skill `services-cli-operations`; return here only for worker backend, allocation, and weight-sync constraints.
- If the user is authoring datasets, reward functions, `RolloutWorkflow`, or agent workflow code, route to sibling sub-skill `custom-data-rewards-workflows`.
- Never claim that CPU import or CLI help proves GPU backend behavior. It only proves import/config surface availability.

## Operating workflow

1. Establish the user's target roles (`rollout`, `actor`, optional `critic`, `ref`, `teacher`), cluster shape, backend strings, install variant, weight-update mode, LoRA/FP8 flags, and whether actor/rollout are separated or colocated.
2. Parse backend strings and compute GPU demand with [`scripts/check_backend_plan.py`](scripts/check_backend_plan.py):

   ```bash
   python scripts/check_backend_plan.py \
     rollout.backend=sglang:d2t4 actor.backend=fsdp:d8 \
     cluster.n_nodes=2 cluster.n_gpus_per_node=8 \
     actor.weight_update_mode=xccl
   ```

   Add `--probe-env` only for safe CUDA visibility/import facts; it is still not a backend runtime proof.
3. Use [`references/backend-planning.md`](references/backend-planning.md) for backend syntax, install variants, parallelism capability, Ray/Slurm placement, LoRA, and FP8 planning.
4. Use [`references/engine-api-and-weight-sync.md`](references/engine-api-and-weight-sync.md) for train/inference engine contracts, generation request behavior, weight versioning, and `disk`/`xccl`/`awex` update modes.
5. Use [`references/troubleshooting.md`](references/troubleshooting.md) to debug parse/config errors, optional dependency issues, CUDA/NCCL hangs, OOM, LoRA/FP8 failures, placement mistakes, and checkpoint/recovery mismatches.

## Safe outputs to give users

- Backend field diffs or config snippets such as `rollout.backend=sglang:d2t4`, `actor.backend=megatron:(attn:d1p4t2c2|ffn:d1p4t1e4)`, `actor.weight_update_mode=disk`, or `actor.megatron.bridge_type=megatron-bridge`.
- A GPU-demand calculation and assumptions: separated roles sum GPU worlds; colocated roles require explicit placement and usually matching planned worlds.
- A validation checklist and one safe checker command.
- A clear skip/block statement for GPU-only, multi-node, model-download, service, or credentialed validation that was not actually run.

## Hard stops

Do not start training, launch SGLang/vLLM/Ray/Slurm services, download models/datasets, run native repo tests, mutate driver/CUDA stacks, or guess cluster-specific placement. Ask for cluster/model/runtime decisions when they are required to choose between incompatible backends or install variants.
