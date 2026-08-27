# Scheduler API mental model

RLinf hides most Ray details behind scheduler abstractions. Use this reference to reason about setup, not to add new components. Extension work belongs in the `extension-development` sub-skill.

## Core objects

| Object | Role | Setup implications |
|---|---|---|
| `Cluster` | Singleton that initializes/attaches to Ray, waits for nodes, records topology, creates manager actors, and allocates workers to nodes/resources. | Construct it before any direct `ray.init()`. Pass `cluster_cfg=cfg.cluster` in drivers that own startup. |
| `ClusterConfig` | Dataclass-backed schema for `cluster.num_nodes`, `component_placement`, `node_groups`, `env_configs`, hardware, and profiling options. | Validates node ranks, reserved labels, env var shapes, hardware configs, and positive node count. |
| `ComponentPlacement` | Parses `cluster.component_placement` and turns rank strings into placement strategies. | Short form defaults to the cluster-wide group; node-group form selects labeled groups. |
| `HybridComponentPlacement` | Allows arbitrary component resource sets and marks placement mode `HYBRID`. | Common for embodied workflows with env/rollout/actor pipelines. |
| `ModelParallelComponentPlacement` | Validates model-parallel actor/rollout/reward/inference placement, classifying collocated/disaggregated/auto modes. | Common for reasoning/agentic workloads; requires continuous ranges and consistency with TP/PP/DP sizes. |
| `PlacementStrategy` | Low-level plan that maps process ranks to node ranks and hardware ranks. | `FlexiblePlacementStrategy` maps to accelerators/custom hardware; `NodePlacementStrategy` maps to nodes; `PackedPlacementStrategy` packs contiguous hardware ranges. |
| `Worker` | Base class for remote processes. Workers receive rank/world-size/master/env information and communication helpers. | Worker code should use `self.log_*` methods, not bare prints, in production paths. |
| `WorkerGroup` | Launches a group of identical workers and exposes methods that execute remotely across ranks. | `create_group().launch(cluster, placement_strategy=...)` realizes the placement. |
| `Channel` | Distributed FIFO/weighted queue abstraction over worker communication. | Used for producer/consumer rollout pipelines and load balancing. |

## Cluster lifecycle

When a driver constructs `Cluster(cluster_cfg=cfg.cluster)`, RLinf:

1. Ensures Ray is not already initialized by user code.
2. Calls `ray.init(address="auto", namespace="RLinf", ...)` if a Ray cluster is running, otherwise starts local Ray.
3. Waits until the expected node count is alive.
4. Builds node and node-group topology using `RLINF_NODE_RANK`, accelerator detection, and `cluster.node_groups`.
5. Sets scheduler environment variables and launches manager actors on node rank 0.
6. Uses `Cluster.allocate()` to start remote worker actors pinned to physical nodes and assigned resources.

If code sync is enabled with `RLINF_CODE_WORKING_DIR`, `Cluster` adds a Ray `runtime_env` fragment that ships only the `rlinf` package subtree to workers.

## Worker environment

Workers launched through `WorkerGroup` receive environment variables such as:

- `MASTER_ADDR`, `MASTER_PORT` for process-group rendezvous.
- `RANK`, `LOCAL_RANK`, `WORLD_SIZE`, and group/world rank metadata.
- Accelerator visibility variables such as `CUDA_VISIBLE_DEVICES` when isolation is enabled.
- Env vars from matching `node_groups.env_configs`.

A worker group can be launched with a named placement strategy:

```python
from rlinf.scheduler import Cluster, Worker
from rlinf.utils.placement import HybridComponentPlacement

class SetupCheckWorker(Worker):
    def ping(self):
        return {"rank": self._rank, "world_size": self._world_size}

cluster = Cluster(cluster_cfg=cfg.cluster)
placement = HybridComponentPlacement(cfg, cluster)
strategy = placement.get_strategy("actor")
group = SetupCheckWorker.create_group().launch(
    cluster,
    name="setup_check",
    placement_strategy=strategy,
)
print(group.ping().wait())
```

For model-parallel reasoning placement, use `ModelParallelComponentPlacement` instead of `HybridComponentPlacement` and expect stricter actor/rollout/reward/inference validation.

## Placement strategy details

- `FlexiblePlacementStrategy` places processes on accelerators or custom hardware within one selected node group. It can assign multiple processes to one resource or multiple resources to one process when counts are compatible.
- `NodePlacementStrategy` places hardware-agnostic processes on node ranks. It is used for the reserved `node` group or CPU-only node groups.
- `PackedPlacementStrategy` represents compact contiguous hardware allocation and is used by default when launching a worker group without an explicit strategy on an accelerator cluster.

RLinf unit tests confirm these important parser behaviors:

- `all` expands to all resources in the selected group.
- `actor,inference` shares one strategy object for both components.
- Duplicate resource ranks and non-continuous process ranks raise assertions.
- Node-group-specific allocations keep components on the intended node ranks.
- Multi-node heterogeneous groups can isolate env vars and Python interpreters by group/node.
- A single process may not silently mix incompatible hardware groups.

## Channels and communication

Workers can communicate directly with `send`/`recv` and tensor-specific methods, or indirectly through channels.

Channel basics:

- A worker creates a channel by name with `create_channel(name, node_id=0, maxsize=0)`.
- Other workers connect with `connect_channel(name)`.
- Producers call `put(item, weight=..., key=...)`.
- Consumers call `get(key=...)` or `get_batch(batch_weight, key=...)`.

Channels are useful for asynchronous rollout and load-balancing patterns because they decouple producer and consumer worker rates.

## Setup-focused API checklist

Before diagnosing higher-level training logic, verify:

1. `Cluster` is constructed before direct Ray API use.
2. The Ray namespace is not polluted by previous failed runs; restart Ray if necessary.
3. `component_placement` contains every component required by the selected runner/backend.
4. The chosen placement class matches the workflow: hybrid for embodied/mixed, model-parallel for reasoning/agentic model-parallel pipelines.
5. Worker group names are unique when multiple groups of the same class are launched.
6. Node-group `env_configs` are needed only for real per-node software/env differences; avoid using them to paper over a stale Ray environment.

