# JAX troubleshooting and recovery

Use the symptom, confirm with the smallest safe check, then repair only the
affected component. A CPU check proves only the CPU path. It does not prove
CUDA, multi-process, simulator, or performance behavior.

## Failure matrix

| Symptom | Likely cause | Safe confirmation | Recovery |
|---|---|---|---|
| `ModuleNotFoundError` for `jax`, `flax`, or `optax` | JAX extra is absent or installed in another interpreter | `python -c 'import jax, flax, optax; print(jax.devices())'` | Run the JAX extra in the same interpreter; install the desired JAX/JAXLIB variant first when GPU is required. |
| JAX imports but only lists `CpuDevice` | CPU `jaxlib` or no usable accelerator backend | print `jax.default_backend()` and `jax.devices()` | Treat the run as CPU. Install the matching accelerator JAX/JAXLIB build using current JAX guidance; do not claim CUDA from host hardware. |
| `config.jax.parse_device("cuda:0")` warns and returns CPU | CUDA backend/index is unavailable to this JAX process | call `parse_device("cuda:0")` and inspect returned device | Fix the JAXLIB/backend installation or explicitly request `"cpu"`; do not suppress the warning and assume acceleration. |
| device parser rejects an odd string | parser expects a backend plus optional ordinal | compare against `jax.devices()` and retry `None`, `"cpu"`, or a known device | Use a string like `"cpu"`/`"cuda:0"` or pass the actual `jax.Device`; invalid specifications fall back to the first JAX device. |
| `AttributeError: ... state_dict` during `.act()` | A JAX model was constructed but not initialized | inspect `hasattr(model, "state_dict")` before calling `.act()` | Call `model.init_state_dict(role=<exact key>)` after constructing every model. |
| Flax `TypeError` says a constructor argument is missing | A custom Flax module has a required non-space/device argument | inspect the custom `__init__` | Give all custom constructor arguments defaults; keep only spaces and device required, as the public JAX model docs require. |
| Flax reserved/post-init error | Mixins or base constructor were called in the wrong order | compare class and constructor order | Define `class X(Mixin, Model)`; call `Model.__init__` before `Mixin.__init__`; do not override Flax post-init casually. |
| JIT error refers to missing `observations`, `states`, or `taken_actions` | Model input expression and agent role do not agree | call the model with a small explicit input dict before JIT | Use the public input keys; asymmetric value models consume `states`, critics consume `taken_actions`, and policies normally consume `observations`. |
| Agent accepts models but fails during `init`/`act` with a missing role | The model dictionary key is wrong or the role passed to `act` is wrong | compare keys with the algorithm table and agent docs | Use exact keys such as PPO `policy`/`value`, DQN `q_network`/`target_q_network`, or SAC's five keys; initialize with the same role. |
| Categorical policy returns the wrong action width | A discrete and a multi-discrete policy were mixed | inspect `action_space` and the final network width | Use `CategoricalMixin` for `Discrete`; use `MultiCategoricalMixin` with total `nvec` width for `MultiDiscrete`. |
| Gaussian policy raises a missing `log_std` key | `__call__` returned only a mean action | inspect auxiliary outputs | Return `{"log_std": ...}` from the policy; tune clipping/reduction through the mixin constructor. |
| `ValueError` for a reduction | Unsupported mixin reduction string | check `reduction` | Use exactly `"mean"`, `"sum"`, `"prod"`, or `"none"`. |
| DQN/DDQN action/value shape is inconsistent | Q network was written as an action policy or has a scalar output | compare action-space cardinality to final output | Use a deterministic Q model with one value per discrete action and exact Q model keys. |
| Continuous DDPG/SAC/TD3 critic sees only observations | Critic omitted `taken_actions` | run one critic call with observation plus action | Concatenate/use `inputs["taken_actions"]` and return one scalar per sample. |
| `Memory` is empty or tensors are absent | Memory is an empty shell until the agent initializes algorithm tensors | inspect `memory.get_tensor_names()` after construction | Use a trainer (it initializes the agent) or call `agent.init(trainer_cfg=...)` before direct memory operations. |
| Memory tensor size/dtype mismatch | A tensor was created twice with incompatible shape/dtype | inspect `memory.get_tensor_names()` and the spaces | Let the selected agent own standard tensor creation; use a unique name and matching flattened space for custom tensors. |
| PPO update samples too little data or an empty batch | `rollouts`, `num_envs`, `batch_size`, and `mini_batches` are incompatible | inspect `len(memory)` and `RandomMemory.sample(...)` inputs | Start with `rollouts >= mini_batches` and a batch size supported by the valid memory; defer update until `learning_starts` and enough samples. |
| `PPO_CFG`/other config constructor rejects a field | Wrong framework field, typo, or version drift | inspect `inspect.signature(PPO_CFG)` or `dataclasses.fields(PPO_CFG)` | Use the installed `*_CFG` field names. Do not paste Torch-only fields into JAX configs. |
| A dictionary config fails in a nested experiment field | `experiment` is not shaped as the expected nested dataclass/dict | print `cfg.experiment` after construction | Prefer `cfg = PPO_CFG()` and mutate known fields; otherwise supply a correctly nested `experiment` mapping. |
| scheduler construction fails | Scheduler class/kwargs belong to another framework or kwargs contain unsupported fields | inspect the JAX scheduler signature | Import `KLAdaptiveLR` or an Optax schedule from JAX/Optax, set `learning_rate_scheduler_kwargs`, and omit unsupported constructor keys. |
| `sample_space` rejects backend | The explicit backend is not `"numpy"` or `"native"` | call it with a tiny `Box` and the two supported values | Pass the explicit `backend`; do not rely on `config.jax.backend`, which is assigned in examples but not consumed by the inspected 2.1.0 helper. |
| NumPy arrays reach a JAX model unexpectedly | Data was sampled with the NumPy space backend or wrapper conversion was skipped | inspect `type(x)` and `x.device` | Convert at the environment boundary with the JAX wrapper or `jnp.asarray` on the intended device; keep model/memory data native. |
| reproducibility check changes between calls | JAX keys are functional and mixins fold in an internal call counter | set `config.jax.key`/use `set_seed` and reset model instances | For a fixture, pass explicit initialization keys and create a fresh policy; do not reuse a stochastic call as a fixed-output assertion. |
| `SequentialTrainer` rejects the environment | A raw Gymnasium env was passed instead of a skrl JAX wrapper | inspect the object's wrapper/device/space attributes | Route wrapping to environment integration and pass the returned wrapper. |
| trainer constructor appears to create work before training | Trainer construction initializes agents and may JIT model apply functions | run the bundled no-loop smoke | Keep this initialization check separate from training; set `close_environment_at_exit=False` in bounded fixtures and close a manually-created env. |
| checkpoints are missing | Experiment intervals are `0`/nonpositive, or the trainer has not reached an interval | inspect `cfg.experiment` and resolved `agent.checkpoint_interval` | Set a positive interval or `"auto"`, call `agent.init` through a trainer, and inspect the experiment `checkpoints` directory. |
| `agent.load` warns/skips modules or fails deserialization | Architecture/model keys differ from the saved agent | compare `checkpoint_modules` and model definitions | Reconstruct the same model shapes and registered resources before loading; load an agent checkpoint into an agent, not a raw model. |
| evaluation is stochastic when deterministic output was expected | `stochastic_evaluation=True` or the caller used the sampled action directly | inspect trainer config and `outputs["mean_actions"]` | Use `stochastic_evaluation=False` for the sequential trainer or consume `mean_actions` explicitly. |
| GPU OOM appears with an NVIDIA simulator | PyTorch and JAX may both preallocate GPU memory | inspect process memory and the simulator/JAX integration boundary | Before importing JAX, lower its allocation fraction, for example `XLA_PYTHON_CLIENT_MEM_FRACTION=.50`, and coordinate simulator/PyTorch allocation. This is an integration mitigation, not a proof of JAX CUDA support. |
| CPU smoke passes but an accelerator run fails | Backend, driver, wheel, device ordinal, or simulator transfer differs | compare per-process `jax.devices()` and environment device | Classify CUDA/simulator execution as a separate verification target; keep the CPU result and record the optional backend as unverified. |

## Focused safe checks

### Check package and device facts

```bash
python - <<'PY'
import jax, flax, optax, skrl
from skrl import config
print(skrl.__version__)
print(jax.default_backend(), jax.devices())
print(config.jax.parse_device(None))
print(config.jax.parse_device("cpu"))
PY
```

### Check a model before an agent

```python
import gymnasium
from skrl.models.jax import DeterministicMixin, Model

# Define a complete Flax model first; then:
model.init_state_dict(role="value")
assert hasattr(model, "state_dict")
value, extra = model.act({"observations": observations, "states": states}, role="value")
assert value.shape[-1] == 1
```

Use real JAX arrays and the correct model input keys in this check. Do not use a
full environment loop to diagnose a constructor problem.

### Check the bundled smoke

```bash
python sub-skills/jax-agent-training/scripts/jax_ppo_components.py --help
python sub-skills/jax-agent-training/scripts/jax_ppo_components.py --num-envs 1 --backend numpy
```

The script's `--backend` option records the example-level NumPy/JAX selection;
model initialization still uses native JAX by the package contract.

## Scope-specific escalations

- Installation, root framework choice, and cross-framework import failures:
  [framework selection](../../../references/framework-selection.md) and the
  [root troubleshooting guide](../../../references/troubleshooting.md).
- Raw Gymnasium/Gym, vectorized envs, Isaac Lab, ManiSkill, or `wrap_env`:
  [environment integration](../../environment-integration/SKILL.md).
- IPPO/MAPPO, scopes, Runner YAML, or multi-agent checkpoints:
  [multi-agent and Runner](../../multi-agent-and-runner/SKILL.md).

## Evidence anchors

- `[Config]` public `skrl.config.jax` implementation and the JAX config test.
- `[Spaces]` public JAX `sample_space` contract.
- `[Models]` JAX model/mixin docs and model-instantiator tests.
- `[Agents]` public JAX agent docs, configurations, and agent test fixtures.
- `[Trainer]` public JAX trainer implementation and trainer tests.
- `[Install]` public installation troubleshooting note for JAX/simulator GPU
  preallocation.
- `[Example]` bounded construction adapted from the JAX Gymnasium Pendulum PPO
  example.
