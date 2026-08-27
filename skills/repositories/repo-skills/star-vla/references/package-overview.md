# StarVLA Package Overview

## When to read

Read this when you need a compact map of StarVLA's moving parts before choosing a sub-skill. It is a runtime overview distilled from the repository evidence; it does not require reopening source docs.

## What StarVLA is

StarVLA is a modular research codebase for developing vision-language-action policies for robot manipulation. Its design goal is to let users swap model backbones, action heads, datasets, trainers, benchmark adapters, and deployment bridges with minimal coupling.

The main operating axes are:

- **Model family**: VLM4A, VM4A, or WM4A.
- **Action representation**: continuous MLP/OFT, discrete FAST tokens, flow-matching/π-style action heads, GR00T-style dual-system heads, ACT, or Diffusion Policy.
- **Data format**: LeRobot-format robot trajectories with `meta/modality.json`, robot-specific data configs, and named mixtures.
- **Training entry point**: VLA-only, VLM-only, or VLA+VLM co-training scripts using Accelerate/DeepSpeed and OmegaConf overrides.
- **Evaluation/deployment**: a policy server serves a checkpoint while simulator or robot clients send observations and receive unnormalized action chunks.

## High-level layout

| Area | Responsibility | Owning sub-skill |
| --- | --- | --- |
| Model registry and framework classes | Resolve `framework.name`, instantiate VLM4A/VM4A/WM4A policy classes, expose `forward`, `predict_action`, and checkpoint loading contracts | [model-frameworks](../sub-skills/model-frameworks/SKILL.md) |
| Action, VLM, and world-model modules | Provide action heads, VLM wrappers, visual encoders, world-model wrappers, and normalization helpers used by framework classes | [model-frameworks](../sub-skills/model-frameworks/SKILL.md) |
| Training scripts and trainer utilities | Prepare dataloaders, optimizers, LR groups, checkpoints, distributed training, W&B logging, and YAML/dotlist override behavior | [training-config](../sub-skills/training-config/SKILL.md) |
| LeRobot dataloaders and registries | Load robot trajectories, combine dataset mixtures, apply state/action/video transforms, compute or cache statistics | [data-integration](../sub-skills/data-integration/SKILL.md) |
| Simulation benchmark examples | Provide environment-specific evaluation clients, launch scripts, result aggregation patterns, and benchmark caveats | [benchmark-evaluation](../sub-skills/benchmark-evaluation/SKILL.md) |
| Policy serving and robot bridges | Serve checkpoints over websocket or GR00T-compatible ZMQ, own server-side action unnormalization, expose metadata and client contracts | [policy-deployment](../sub-skills/policy-deployment/SKILL.md) |

## Workflow ownership

### Model development

Use [model-frameworks](../sub-skills/model-frameworks/SKILL.md) when the user asks which framework name to set, how a new backbone/action head should fit, why a registry key is missing, or how checkpoint config compatibility works. StarVLA's router pattern is `framework.name -> registered class -> baseframework`.

### Training and co-training

Use [training-config](../sub-skills/training-config/SKILL.md) when the task is to build commands, adjust YAML, apply CLI overrides, freeze modules, set learning rates, plan DeepSpeed/Accelerate resources, or explain checkpoint directories. Do not launch multi-GPU jobs or downloads unless the user explicitly asks and the environment is ready.

### Dataset and robot integration

Use [data-integration](../sub-skills/data-integration/SKILL.md) when the task names LeRobot, `modality.json`, `DataConfig`, `data_mix`, robot types, action/state dimensions, or dataset statistics. Most training errors that mention missing mixtures, bad state/action keys, or language lookup should route there before retrying training.

### Simulation benchmark evaluation

Use [benchmark-evaluation](../sub-skills/benchmark-evaluation/SKILL.md) when the task is to run or plan LIBERO, SimplerEnv, RoboCasa, RoboTwin, DOMINO, BEHAVIOR, VLA-Arena, Calvin, RoboDojo, or similar evaluation. These flows commonly need two environments: a StarVLA environment for the policy server and a simulator-specific environment for the client.

### Serving and deployment

Use [policy-deployment](../sub-skills/policy-deployment/SKILL.md) when the task names `server_policy`, `PolicyServerWrapper`, websocket clients, GR00T ZMQ, `unnorm_key`, `available_unnorm_keys`, metadata, or action response schemas. Current serving returns unnormalized `actions`; older prose or client code that expects `normalized_actions` needs migration.

## Common artifact names

| Artifact | Meaning |
| --- | --- |
| `config.yaml` | Training/checkpoint config; StarVLA merges CLI dotlist overrides on top of config/checkpoint values. |
| `dataset_statistics.json` | Saved statistics used for action unnormalization and deployment metadata. Keep it paired with checkpoints. |
| `meta/modality.json` | Per-dataset schema mapping raw data columns to video/state/action/language modality fields. |
| `data_mix` | Named mixture selecting one or more dataset folders and robot types. |
| `framework.name` | Main framework registry key for model construction. |
| `action_horizon` or `future_action_window_size + 1` | Action chunk length expected by deployment clients and server metadata. |
| `unnorm_key` | Dataset/statistics key selecting which normalization statistics to use for multi-dataset checkpoints. |

## Verification stance

The safe default is to validate static configuration and import/contracts first:

1. Run the root install checker.
2. Inspect model/config/dataset/server contracts with bundled scripts.
3. Use CPU-safe tests or synthetic validation where possible.
4. Only then run GPU training, simulator evaluation, or robot deployment in an explicitly prepared environment.

A CPU import check proves basic package readability. It does **not** prove CUDA/ROCm/NPU training, benchmark success rates, checkpoint reproduction, or real-robot safety.
