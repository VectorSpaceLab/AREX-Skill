# Ray, RLlib, and optional RL frameworks

## Availability boundary

The prepared SMARTS core environment verified CPU SMARTS, Gymnasium, scenario
and interface APIs, but it did **not** install `ray`, `ray.rllib`, `torch`, or
`tensorflow`. Those integrations are optional and unverified here. Do not
claim that an RLlib import, rollout, training run, checkpoint load, Torch
inference path, or TensorFlow inference path works until the user supplies a
compatible environment and performs a bounded check.

The package metadata separates the optional groups: `ray` supplies a bounded
Ray release; `rllib` adds Ray/RLlib-related packages and TensorFlow Probability;
`torch` supplies Torch and torchvision; `train` supplies TensorFlow. Choose a
version set deliberately for the SMARTS release and the model artifact. Do not
install the broad `all` extra or the repository's old pinned requirements file
as a shortcut. Installation is user-controlled and outside the bundled
locator checker.

## RLlibHiWayEnv contract

`smarts.env.rllib_hiway_env.RLlibHiWayEnv` subclasses RLlib's
`MultiAgentEnv`, so importing it itself requires Ray/RLlib. Its constructor
accepts one `config` object and requires:

- `agent_specs`: a mapping from agent id to `AgentSpec`; every spec must have
  an interface for environment construction.
- `scenarios`: a list of scenario directories visible to the worker.

Useful optional keys include `seed`, `sim_name`, `headless`,
`envision_endpoint`, `envision_record_data_replay_path`,
`num_external_sumo_clients`, `sumo_headless`, `sumo_port`, `sumo_auto_start`,
and `fixed_timestep_sec` (the older `timestep_sec` name is deprecated). For a
Ray worker config, `worker_index` and `vector_index` are read to derive a
worker-specific seed. A plain dict without those Ray fields is not a drop-in
constructor fixture.

At construction, the environment builds multi-agent action and observation
formatters from each `AgentSpec.interface`, and exposes mapping spaces. Its
`reset` returns `(observations, infos)`. Its `step` expects a dict of actions
for currently active agents and returns:

```text
(observations, rewards, terminateds, truncateds, infos)
```

The termination dictionaries include the RLlib `"__all__"` key. A done agent
is expected to send a final observation on its transition; subsequent action
dicts omit it. SMARTS filters returned observations/rewards/infos to the agent
ids present in the submitted actions. Keep action keys, observations, rewards,
and infos aligned for every active id.

The environment's action formatter checks each action against the per-agent
space before converting it. The RLlib policy declaration must therefore use
the same action space as the `AgentSpec.interface`, or an explicit adapter
must translate the model output. The same rule applies to observations: an
adapter or preprocessor must emit exactly the declared keys, shape, dtype, and
bounds. A model space that merely has the same number of scalars is not enough.

## Space alignment procedure

For each policy id:

1. Choose the `AgentInterface` and its `ActionSpaceType`.
2. Build the formatter or a small core environment and inspect
   `action_space[agent_id]` and `observation_space[agent_id]`.
3. Define the RL policy's spaces from those actual values, or document an
   adapter. For a structured observation, flatten only after declaring the
   flattened space and applying the identical transformation at runtime.
4. Test a representative model output with `space.contains(output)` and test
   one transformed observation with `observation_space.contains(value)`.
5. Only then configure RLlib's `multi_agent` policy map and mapping function.

The reference RLlib example declares one policy tuple per agent, uses a
flattened observation space, maps `AGENT-i` to the matching policy, and uses
`RLlibHiWayEnv` with `disable_env_checking=True`. Disabling checks does not
repair a mismatch; it only removes an early diagnostic.

## Ray worker and sensor distribution

Ray is used in two related but distinct places:

- RLlib creates rollout workers and vector environments. Scenario paths in
  `config["scenarios"]` must be readable by every worker. Use deterministic
  base seeds and let the worker/vector indices differentiate instances.
- SMARTS can use `RaySensorResolver` for serializable sensor observations. It
  initializes Ray, creates named `RayProcessWorker` actors, serializes the
  simulation frame and local constants, partitions agent ids across workers,
  collects futures, and merges physics/rendered observations. This path also
  requires Ray and is not verified in the core environment.

Avoid worker-only relative paths, non-picklable lambdas that capture live
resources, local-only model files, and fixed ports shared by all workers.
Use one scenario path convention visible from the driver and workers. Camera
or Envision behavior adds separate rendering/service prerequisites.

## Training and inference patterns (reference only)

The repository examples show PPO with `PPOConfig`, an environment config
containing `agent_specs` and scenario paths, multi-agent policy tuples, a
policy mapping function, rollout worker counts, and optional callbacks. A
separate example adds Population Based Training and Tune checkpoint handling.
These are configuration patterns, not a claim that training is runnable here.

For inference, an `Agent` can load a model in its constructor and convert the
SMARTS observation before calling the framework. The adapter must reverse the
model's action representation into the selected SMARTS action. TensorFlow
SavedModel examples use a framework-specific session, tensor names, and a
preprocessor; those names are artifact-specific and must not be copied blindly.
Torch/Stable-Baselines examples similarly require their exact model and package
versions.

## Resume and checkpoint caveat

`resume_training=True` in the reference RLlib workflow resumes the prior
experiment configuration. It is not a general permission to alter the
interface, action/observation spaces, policy map, scenario contract, or model
architecture. The documented caveat is that a resumed run continues with the
same configuration recorded by the experiment. If configuration must change,
start a new experiment or use the framework's explicit checkpoint-loading path
and validate compatibility first. Treat a checkpoint loaded under altered
spaces or altered preprocessing as invalid until checked.
