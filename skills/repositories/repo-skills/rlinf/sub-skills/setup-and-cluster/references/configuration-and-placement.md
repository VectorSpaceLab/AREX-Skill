# Configuration and placement

RLinf uses Hydra/OmegaConf YAML. The `cluster:` section is the common setup surface across embodied, reasoning, agentic, SFT, offline, and evaluation workflows.

## Minimal cluster section

```yaml
hydra:
  run:
    dir: .
  output_subdir: null

cluster:
  num_nodes: 1
  component_placement:
    actor,rollout,reward: all
```

Key rules:

- `cluster.num_nodes` is the number of physical Ray nodes expected by RLinf. It must match the Ray cluster and the zero-based `RLINF_NODE_RANK` assignments.
- `cluster.component_placement` maps logical components (`actor`, `rollout`, `inference`, `env`, `reward`, `agent`, etc.) to hardware resources or nodes.
- A comma-separated component key (for example `actor,rollout`) gives each component the same placement rule.
- `all` expands to all valid resources in the selected node group.

## Placement syntax

Each placement segment has the form:

```text
resource_ranks[:process_ranks]
```

Supported range forms:

- `3` — one rank.
- `0-3` — inclusive range.
- `0,2,3` — list.
- `0-3,5,14` — mixed ranges/lists.
- `all` — all resources in the selected node group; valid only for resource ranks.

Process rank rules:

- `process_ranks` are optional. If omitted, RLinf assigns a continuous block with the same length as resources.
- Process ranks must be continuous from `0` to `N-1` and each rank must appear exactly once.
- For every `resource_ranks:process_ranks` pair, the resource count and process count must be compatible: one must be an integer multiple of the other.
- Duplicated resource ranks or non-continuous process ranks are validation errors.

Examples:

```yaml
cluster:
  num_nodes: 1
  component_placement:
    actor,inference: 0-7
    reward: 0-1
```

```yaml
cluster:
  num_nodes: 4
  component_placement:
    agent:
      node_group: node
      placement: 0-1:0-199,2-3:200-399
```

The second example uses the reserved `node` group for hardware-agnostic node placement. Resource ranks mean node ranks rather than GPU ranks.

## Short form versus node-group form

### Short form

Use short form for homogeneous clusters where accelerator ranks can be treated as one global pool:

```yaml
cluster:
  num_nodes: 2
  component_placement:
    rollout: 0-9
    inference: 10-11
    actor: 12-15
    reward: 12-15
```

### Node-group form

Use node-group form for heterogeneous hardware, CPU-only components, robot hardware, different Python interpreters, or per-node environment variables:

```yaml
cluster:
  num_nodes: 6
  component_placement:
    actor:
      node_group: train
      placement: 0-15
    rollout:
      node_group: infer
      placement: 0-7
    agent:
      node_group: node
      placement: 4-5:0-63

  node_groups:
    - label: train
      node_ranks: 0-1
      env_configs:
        - node_ranks: 0-1
          env_vars:
            - GLOO_SOCKET_IFNAME: "eth0"
    - label: infer
      node_ranks: 2-3
      env_configs:
        - node_ranks: 2-3
          env_vars:
            - GLOO_SOCKET_IFNAME: "eth1"
```

Node-group fields:

| Field | Meaning | Constraints |
|---|---|---|
| `label` | Case-sensitive group name used by `component_placement` | `cluster` and `node` are reserved labels. |
| `node_ranks` | Zero-based global node ranks in the group | Must be within `0..num_nodes-1`; supports range/list syntax. |
| `env_configs` | Per-subset software/env overrides | `node_ranks` must be inside the parent group; entries may not overlap. |
| `env_vars` | One-key dictionaries exported to workers | Each env-var key must be unique within a node group for a node. |
| `python_interpreter_path` | Interpreter to use for worker allocation on those nodes | Use only when nodes intentionally run different venvs. |
| `hardware` | Structured non-accelerator hardware such as robots | When present, placement ranks refer to this hardware type's ranks. |
| `ignore_hardware` | Treat group as CPU/node-only even if accelerators exist | Cannot be combined with `hardware`. |

Hardware rank interpretation:

1. If a node group declares `hardware`, placement ranks refer to that hardware type.
2. Otherwise, if accelerators are detected, placement ranks refer to accelerator ranks in that node group.
3. Otherwise, each node is treated as one resource.
4. The reserved `node` group always means node ranks and disables hardware placement.

## Execution modes

RLinf placement supports three common runtime patterns.

| Mode | Placement shape | Use when | Notes |
|---|---|---|---|
| Collocated | Components share the same resources, e.g. `actor,rollout,reward: all` | Small/simple setups or model-parallel reasoning where phases run sequentially on the same GPUs | Enable offload options when components cannot fit in GPU memory at the same time. |
| Disaggregated | Components use non-overlapping resource sets, e.g. `rollout: 0-9`, `inference: 10-11`, `actor,reward: 12-15` | Rollout/inference/training need dedicated GPU pools or pipelining | Reasoning model-parallel placement expects actor, rollout, reward, and often inference resources to be continuous and consistent with TP/PP/DP sizes. |
| Hybrid | Some components share, others are separate, e.g. `env: 0-3`, `rollout: 4-7`, `actor: 0-7` | Embodied pipelines where env/rollout overlap and actor later uses a larger set | `HybridComponentPlacement` is less restrictive and is common for embodied training. |

Model-parallel reasoning placement uses `ModelParallelComponentPlacement`, which classifies collocated/disaggregated/auto modes and enforces continuity constraints for actor, rollout, inference, critic, and reward GPU ranges. Embodied and mixed workloads often use `HybridComponentPlacement`.

## Render a config safely

Use the bundled renderer before starting long jobs:

```bash
python scripts/render_cluster_plan.py path/to/config.yaml
python scripts/render_cluster_plan.py path/to/config.yaml --json
```

The script performs a lightweight YAML parse and reports `num_nodes`, component placements, node groups, env configs, and hardware blocks without importing RLinf or starting Ray.

## Placement review checklist

- Does `cluster.num_nodes` match `ray status` and all `RLINF_NODE_RANK` values?
- Are component names spelled as the runner expects (`actor`, `rollout`, `inference`, `env`, `reward`, `agent`, etc.)?
- Are GPU ranges in bounds for the selected nodes/groups?
- Are process ranks continuous and non-overlapping?
- Are `node_groups` labels unique and non-reserved?
- Are `env_configs.node_ranks` subsets of their parent group without overlap?
- Do `python_interpreter_path` and env vars match what was exported before Ray started?
- For heterogeneous/robot setups, are hardware ranks and node ranks distinguished clearly?

