# Multi-agent and Runner troubleshooting

Use this matrix before changing the algorithm or launching a long run. First
inspect the wrapped environment contract, then the nested dictionaries, then
the framework/config boundary.

| Symptom | Likely cause | Check | Recovery |
|---|---|---|---|
| `KeyError` for an agent ID while constructing/acting/updating | `models`, `memories`, spaces, or config mapping omits a `possible_agents` key | Compare `set(mapping)` with `set(env.possible_agents)`; do not compare only with current `env.agents` | Create every outer entry, or provide a complete scalar-broadcastable config; preserve exact string IDs |
| `KeyError`/`None` for `policy` or `value` | Inner role key is wrong, or a value model was omitted during training | Require `models[uid]["policy"]` and training `models[uid]["value"]` for every UID | Rename roles exactly; use `memories=None` only for evaluation/direct no-update use |
| A single-agent `models = {"policy": ..., "value": ...}` is rejected or acts strangely | Multi-agent algorithms require `dict[agent_id][role]`, not the single-agent role dictionary | Expected outer keys are possible-agent IDs | Wrap role dictionaries once per UID and pass per-agent spaces |
| Policy action shape/distribution error | Model mixin does not match `action_spaces[uid]`, or a model was built with another UID's space | Inspect each action space and model instantiator; check `Box` vs `Discrete` vs `MultiDiscrete` | Use Gaussian/multivariate Gaussian, categorical, or multi-categorical as appropriate; rebuild with that UID's action space |
| MAPPO value receives `None`, wrong shape, or local observations | No state space/state value exists, or value network input uses the wrong token | Check `env.state_spaces`, `env.state()`, and value network input | Expose a centralized state through the environment wrapper; use `STATES` and matching state space, or choose IPPO/local value semantics |
| MAPPO state appears duplicated for all agents | PettingZoo/global-state wrapper behavior is being mistaken for a bug | `state()` intentionally returns a global state under each possible-agent key | Keep the common state if centralized training is intended; do not concatenate it per agent again |
| JAX Runner unexpectedly does not share models | JAX Runner forces `models.separate` to true and does not implement the Torch shared branch | Inspect the resolved backend and config | Use separate policy/value model instantiators; use direct custom JAX composition if another sharing scheme is required |
| Torch shared model has mismatched roles | `models.separate: false` has not exactly two role entries or role ordering/parameters do not match | Runner reports shared-model cardinality or missing class errors | Set `separate: true` for independent role models, or provide exactly policy/value-compatible structures and alias both roles |
| Runner says `agent`/`models`/`memory`/`trainer` is missing | Required top-level configuration section is absent | Check the loaded object before constructing Runner | Add the required mapping and its `class`; for direct evaluation omit memory only when bypassing Runner and constructing directly |
| `Component 'X' is not supported in the runner cfg` | Wrong spelling/case is not the issue if the name is outside the backend map; trainer may not be a Runner entry | Compare against the framework's component table in [runner-configuration.md](runner-configuration.md) | Use `IPPO`, `MAPPO`, `RandomMemory`, model mixin strings, and `SequentialTrainer` where supported; construct `ParallelTrainer`/`StepTrainer` directly |
| Runner says `models.<role>.class` is not defined | A role mapping lacks its instantiator `class` | Inspect each role under `models` | Add the appropriate `GaussianMixin`, `CategoricalMixin`, `MultiCategoricalMixin`, or `DeterministicMixin` |
| Runner returns `{}` from `load_cfg_from_yaml` | PyYAML unavailable, file unreadable, or YAML syntax invalid | Call the loader on a trusted fixture and inspect the logged error; check `isinstance(cfg, dict)` and non-empty | Install the optional PyYAML dependency if permitted, fix path/syntax, and reload; do not pass `{}` into a long debugging chain |
| `yaml.safe_load` returns `None` | Empty YAML document | Check raw file content | Add a top-level mapping; treat `None` as invalid Runner input |
| `lambda` warning or missing `gae_lambda` | Deprecated Runner key | Run compatibility pass or inspect the resolved agent config | Write `gae_lambda` in new YAML; old `lambda` is migrated but should not be retained |
| `clip_predicted_values` warning | Deprecated value clipping flag | Check resolved `value_clip` | Replace with `value_clip > 0` or `0.0` |
| `state_preprocessor` moved unexpectedly | It was supplied without an explicit `observation_preprocessor` | Inspect the compatibility result | Set `observation_preprocessor: null` to intentionally retain only state preprocessing, or write both new keys |
| `shared_state_preprocessor` warning | Removed legacy name | Inspect resolved state preprocessor and kwargs | Rename it to `state_preprocessor` and its kwargs |
| Config migration appears not to modify caller data | Runner checks a deep copy | Compare the Runner's resolved config, not the original dictionary | Treat warnings as migration evidence and update the source YAML explicitly |
| Per-agent scalar config does not behave per-agent | Mapping is incomplete, or scalar expansion was expected but a malformed mapping was passed | Check exact key set; `MultiAgentCfg.expand` requires all possible-agent keys in a supplied mapping | Pass a scalar for broadcast, or a complete mapping keyed by every UID |
| `TypeError` from config constructor | Unknown field or wrong nested config type | Compare against `IPPO_CFG`/`MAPPO_CFG` fields and `ExperimentCfg` | Remove misspellings; use dataclass field names and a nested experiment mapping |
| Scheduler constructor complains about `optimizer` | `learning_rate_scheduler_kwargs` included a reserved automatically supplied arg | Inspect scheduler kwargs | Remove `optimizer`; Runner/algorithm supplies it for Torch schedulers |
| Checkpoint loads only some agents or warns about skipped modules | Checkpoint and current `possible_agents`/inner roles differ | Compare checkpoint outer keys, role keys, and architecture with current agent | Recreate the same agent IDs and role structure; only intentionally accept warnings for removed agents/modules |
| Torch checkpoint extension or JAX checkpoint extension seems wrong | Backend-specific serialization was mixed | Torch writes `.pt`; JAX writes `.pickle` module bytes | Use the matching framework's `save`/`load` and a matching model construction |
| No TensorBoard/checkpoints on a distributed worker | Nonzero rank intentionally sets write/checkpoint interval to zero | Inspect `config.<framework>.rank` and agent init | Read artifacts from rank zero; do not re-enable all ranks without a duplication plan |
| Duplicate or corrupt logs/checkpoints | Multiple ranks/processes are writing the same experiment path | Check rank ownership and `experiment.directory`/name | Keep rank-zero artifact ownership; use distinct experiment names for genuinely separate jobs |
| Trainer says number of agents and scopes do not match | `len(scopes) != len(agents)` | Print list lengths before trainer construction | Provide one environment-count scope per list agent or omit scopes for equal generation |
| Trainer says scopes do not cover environments | Scope counts sum to something other than `env.num_envs` | Sum the supplied counts; remember they are counts, not endpoints | Correct counts; final generated scope receives remainder |
| Trainer says too many simultaneous agents | More list agents than vectorized environments | Compare `len(agents)` with `env.num_envs` | Reduce simultaneous list agents or increase vectorization; do not use a single non-vectorized env |
| Simultaneous execution raises on a single environment | Sequential/parallel simultaneous branch requires `env.num_envs > 1` | Inspect `env.num_envs` | Vectorize the environment or use one agent object/direct loop |
| Simultaneous list of `MultiAgent` objects mishandles dictionaries | Generic trainer slices array-like tensors; native test branch is skipped/not implemented | Check whether the task is a list of multi-agent agents versus one multi-agent object | Keep one IPPO/MAPPO object for all possible agents, or write/verify a custom trainer; do not claim generic simultaneous support |
| `ParallelTrainer` hangs or child processes fail | Pickling, barrier, shared-memory, spawn, or device issue | Use `SequentialTrainer` first; check `env.num_envs`, CPU/GPU memory, and picklability | Diagnose with a bounded constructor/import check; use sequential execution unless parallel process behavior is required and approved |
| Parallel Torch run uses more GPU memory than expected | Each worker initializes Torch CUDA kernels and models | Review worker count and device placement | Reduce worker count, use sequential trainer, or budget the documented per-process overhead |
| JAX distributed launch cannot initialize | Wrong rank/world size/coordinator or unreachable host/port | Run `python -m skrl.utils.distributed.jax --help`; verify launcher arguments and environment variables on every host | Correct `--nnodes`, `--nproc-per-node`, `--node-rank`, and coordinator address/port; do not fake distributed success from a single process |
| Warp Runner rejects IPPO/MAPPO | Warp Runner component table has no multi-agent algorithms | Inspect `Runner._component` mapping | Route to a supported Torch/JAX IPPO/MAPPO backend or keep Warp single-agent |
| A CPU import is mistaken for distributed/GPU proof | Import and signature checks do not exercise collectives, CUDA, XLA multi-host, or Warp kernels | Record the exact check scope | State the unverified boundary and request a bounded backend-specific run separately |

## A bounded diagnostic sequence

1. Load or inspect config without running training. Reject `{}`/`None` YAML.
2. Check `env` is a framework wrapper and print the multi-agent properties.
3. Compare all outer dictionary keys with `possible_agents`.
4. Compare every model's role and input/output space with its UID.
5. Run the Runner compatibility pass on a copy and inspect deprecation changes.
6. Validate trainer scope counts with a vectorized environment.
7. Use `Runner._component` only for safe, known strings or construct directly.
8. Run a no-training import/signature/parser check. Only after the whole skill
   integration and explicit approval should a short training smoke be considered.
