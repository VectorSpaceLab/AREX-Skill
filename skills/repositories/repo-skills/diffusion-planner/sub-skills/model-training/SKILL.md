---
name: model-training
description: "Configure, smoke-check, train, resume, and troubleshoot Diffusion
  Planner models with the repository's PyTorch/DDP pipeline."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NO_LICENSE
---

# Diffusion Planner model training

Use this sub-skill for model-ready data validation, training configuration,
CUDA/DDP smoke checks, checkpoint resume, and training failure diagnosis. Follow
the staged route; consult the detailed contracts in [the reference links](#detailed-contracts-and-graph-links)
when a stage requires them.

## Scope and routing

This skill covers the repository's training flag contract, model input/output
contracts, normalization, distributed launch, EMA, logging, checkpoints, and
resume. The long-running trainer is intentionally reference-only because it
writes checkpoints, requires a generated corpus, and is not a safe portable
bundled helper; use the bundled checker before a separately managed training
entrypoint. This skill stops before nuPlan scenario preprocessing, closed-loop
simulation, or custom guidance authoring.

- For raw nuPlan data and model-ready `.npz` creation, use
  [data-preparation](../data-preparation/SKILL.md).
- For planner configuration, checkpoint consumption, and simulation, use
  [closed-loop-planning](../closed-loop-planning/SKILL.md).
- For `guidance_fn`, collision guidance, or guided sampling, use
  [guidance](../guidance/SKILL.md).
Training consumes model-ready `.npz` records plus a JSON filename list. It
produces a run directory containing `args.json`, checkpoints, and logs; the
matching `args.json` is part of the checkpoint contract for downstream use.

## Preconditions and safety boundaries

Before training or resume, confirm:

1. The active Python environment imports the project and required dependencies;
   use its interpreter, not a private interpreter path.
2. The data directory, relative-filename JSON list, normalization file, and
   planned writable save directory are valid; choose deliberate resume/overwrite.
3. CUDA/NCCL and intended devices are available for full training. CPU is only
   for parser, manifest, normalization, and limited API checks.
4. Inputs and small fixtures are local; this skill does not download data or
   checkpoints.

The checked-in launcher is a template, not a safe command. Do not copy its
placeholder values, `sudo`, or private interpreter invocation. Use the active
environment with `python -m torch.distributed.run` and explicit device
selection instead.

## Staged decision workflow

### 0. Classify the request

- **Parser/contract smoke:** stay local, bounded, and side-effect free.
- **One-process API/data smoke:** use a tiny fixture, `--ddp false`, zero
  workers, and disabled augmentation if the import path requires it.
- **Training:** proceed only after data, normalization, device, batch, launch,
  and output checks pass.
- **Resume:** inspect `args.json` and `latest.pth` as a pair first.
- Route preprocessing, simulation, and guidance to the siblings above.

### 1. Run safe preflight checks

From the project execution root, run the native parser check and the bundled
[training-contract checker](scripts/check_training_contract.py):

```bash
python scripts/check_training_contract.py --help
python scripts/check_training_contract.py --check-normalization normalization.json \
  --predicted-neighbor-num 10
```

The full trainer is a long-running, side-effectful source workflow rather than
an included runtime helper. Before invoking a separately managed trainer,
apply the flag and tensor contracts in the references and complete these
bounded checks.

For a manifest check, add `--check-manifest <data-dir> --data-list <json-file>`
and a small `--limit`. The checker is no-training, no-download, and
no-checkpoint; a parser pass is not evidence that training or CUDA is healthy.

### 2. Validate the model/data contract

Confirm the manifest resolves every filename under the chosen data directory
and that records contain the required ego, neighbor, lane, route, speed-limit,
and static-object fields. Check the configured axes for future/time length,
agent and neighbor counts, lane/route counts and lengths, and static-object
count; the detailed shapes and keys are in the [API reference](references/api-reference.md).

Use one normalization layout consistently. `normalization.json` supplies
future-state statistics for ego/neighbors and observation statistics for other
inputs. An absent key, wrong vector length, non-positive standard deviation,
non-finite value, or mismatched layout is a preflight failure, not a
learning-rate problem.

### 3. Reconcile configuration

Compare CLI flags, data axes, normalization, and checkpoint `args.json`.
Keep `hidden_dim` divisible by `num_heads`; dataset/model flags, not descriptive
ones alone, determine reshaping. For a one-process smoke, use a matching
architecture and stop after an API/forward assertion unless training was asked.

The important defaults are future length 80, history length 21, 32 agent rows,
10 predicted neighbors, 70 lanes, 25 route lanes, 5 static objects, global
batch 2048, CUDA, DDP, and EMA enabled. Treat defaults as a starting point;
verify them against the actual data and checkpoint rather than relying on them.

### 4. Choose a launch safely

For one process, set `--ddp false`, use one visible GPU when available, and
make the requested batch the local batch. For DDP, use a real launcher and
check that:

- global `batch_size % WORLD_SIZE == 0` and each rank gets a non-empty batch;
- `--nproc-per-node` equals the number of visible devices after remapping;
- all ranks use identical arguments, readable inputs, and a writable output;
- the port is free and no stale rank variables or failed worker group remain.

The script does not validate batch divisibility. A DDP flag without launcher
environment is not a reliable fallback; choose a real launcher or explicitly
use `--ddp false`. See [workflows](references/workflows.md) for launch shapes.

### 5. Observe the run and preserve evidence

Record the sanitized command, device mapping, world size/local batch,
normalization source, one manifest entry, output directory, and first traceback.
Rank 0 should write `args.json`, checkpoints, TensorBoard output, and optional
W&B files; distinguish logger/save-path failure from model or data failure.

### 6. Resume deliberately

Pass `--resume_model_path` as the directory containing `latest.pth`, not the
file. Compare its sibling `args.json` with the requested architecture before
loading. The loader accepts a wrapped checkpoint or bare state dict, and
optimizer, scheduler, epoch, W&B, and EMA fields may be absent; report a warm
start when those states were not restored. Do not use broad `strict=False` or
silently continue through architecture mismatches.

### 7. Recover and hand off

Triage the first failing contract using the [troubleshooting matrix](references/troubleshooting.md):
manifest/data, normalization, one-GPU API, CUDA visibility, DDP/port, save or
logging, then checkpoint compatibility. Stop after failed preflight; send data
defects to `data-preparation` and checkpoint/simulation defects to
`closed-loop-planning`.

## Verified warnings

- Full training is CUDA/NCCL-oriented; CPU checks cannot validate distributed
  initialization, GPU memory, or a useful epoch.
- Global batch is integer-divided across ranks without a divisibility check.
- `--use_ema false` is not flag-only here: the entrypoint still updates EMA;
  guard or initialize that path in a reviewed adaptation.
- Observed augmentation application is near `1 - augment_prob`; verify before
  reproducibility claims. The “Cosine” scheduler warms up, then uses a fixed
  multiplicative schedule rather than cosine decay.
- Missing `ema_state_dict` prevents reproducing EMA evaluation.

## Detailed contracts and graph links

- [API/config/tensor/checkpoint contract](references/api-reference.md)
- [Staged commands and launch workflows](references/workflows.md)
- [Failure recovery and non-goals](references/troubleshooting.md)
- [Bounded contract-check script](scripts/check_training_contract.py)
- [Diffusion Planner root skill](../../SKILL.md)
- [Data preparation sibling](../data-preparation/SKILL.md)
- [Closed-loop planning sibling](../closed-loop-planning/SKILL.md)
- [Guidance sibling](../guidance/SKILL.md)

Keep source-backed detail in the references; keep this router focused on
applicability, order, stop conditions, and handoffs.
