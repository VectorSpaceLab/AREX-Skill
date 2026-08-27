# JAX Experiment Workflows

Acme JAX experiments are organized around builders, networks, environment specs, and experiment configs. Online agents use `ExperimentConfig`; offline agents use `OfflineExperimentConfig` or a manual learner/evaluator loop.

## Online Single-Process Experiment

Use this shape for SAC, TD3, D4PG, DQN, IMPALA, R2D2, PPO, MPO, WPO, ARS, imitation wrappers around direct RL builders, learning-from-demonstrations wrappers, RND, and decentralized multiagent agents.

```python
from acme import specs
from acme.agents.jax import sac
from acme.jax import experiments


def build_experiment_config(env_name: str, seed: int, num_steps: int):
    environment = make_environment(env_name, seed=seed)
    environment_spec = specs.make_environment_spec(environment)

    network_factory = lambda spec: sac.make_networks(
        spec,
        hidden_layer_sizes=(256, 256, 256),
    )
    config = sac.SACConfig(
        learning_rate=3e-4,
        n_step=2,
        target_entropy=sac.target_entropy_from_env_spec(environment_spec),
    )

    return experiments.ExperimentConfig(
        builder=sac.SACBuilder(config),
        environment_factory=lambda seed: make_environment(env_name, seed=seed),
        network_factory=network_factory,
        seed=seed,
        max_num_actor_steps=num_steps,
        environment_spec=environment_spec,
    )

experiment = build_experiment_config("gym:HalfCheetah-v2", seed=0, num_steps=1_000_000)
experiments.run_experiment(
    experiment=experiment,
    eval_every=50_000,
    num_eval_episodes=10,
)
```

What `run_experiment` builds:

- a PRNG key from `experiment.seed`;
- one environment and `EnvironmentSpec`;
- networks via `network_factory(environment_spec)`;
- behavior and evaluation policies via `builder.make_policy(...)` unless deprecated policy factories are supplied;
- replay tables and a local Reverb server from `builder.make_replay_tables(...)`;
- a dataset iterator from `builder.make_dataset_iterator(replay_client)`;
- learner, adder, actor, training `EnvironmentLoop`, default evaluator loop, and optional checkpointing.

## Online Distributed Experiment

Most JAX examples expose a `run_distributed` flag that switches between local `experiments.run_experiment(...)` and Launchpad distributed execution:

```python
from acme.jax import experiments
from acme.utils import lp_utils
import launchpad as lp

config = build_experiment_config()
program = experiments.make_distributed_experiment(
    experiment=config,
    num_actors=4,
)
lp.launch(program, xm_resources=lp_utils.make_xm_docker_resources(program))
```

Important parameters of `make_distributed_experiment`:

| Parameter | Use |
| --- | --- |
| `num_actors` | Total actor processes/threads collecting environment experience. |
| `num_learner_nodes` | Multiple learners for multi-host accelerators; the learner must correctly use pmap/pmean-style synchronization. |
| `num_actors_per_node` | Colocate multiple actors per Launchpad node. |
| `multiprocessing_colocate_actors` | Use multiprocessing colocation instead of multithreading when actor nodes are colocated. |
| `multithreading_colocate_learner_and_reverb` | Put learner and Reverb in one process; not supported with `num_learner_nodes > 1`. |
| `inference_server_config`, `num_inference_servers`, `num_tasks_per_inference_server` | Route `ActorCore` policy inference through Acme JAX inference servers. Policy must be an `actor_core.ActorCore`. |
| `make_snapshot_models` | Add a model saver node if `experiment.checkpointing` is enabled. |
| `program`, `name` | Add nodes to an existing Launchpad program or create a named program. |

The distributed layout builds replay, counter, learner, actors, evaluators, and optional snapshotter nodes. Actor variables normally come from learners through `VariableClient`; inference-server mode swaps actor variable sources to `ReferenceVariableSource`.

## Offline ExperimentConfig Pattern

Use `OfflineExperimentConfig` when training should not collect new environment interaction. The training data enters through `demonstration_dataset_factory(random_key)`.

```python
from acme import specs
from acme.agents.jax import cql
from acme.jax import experiments


def build_offline_config(dataset_name: str, env_name: str, seed: int):
    environment = make_environment(env_name, seed=seed)
    environment_spec = specs.make_environment_spec(environment)

    def demonstration_dataset_factory(key):
        transitions = load_fixed_transitions(dataset_name, env_spec=environment_spec)
        return make_random_sample_iterator(transitions, key=key, batch_size=256)

    return experiments.OfflineExperimentConfig(
        builder=cql.CQLBuilder(cql.CQLConfig(batch_size=256)),
        network_factory=cql.make_networks,
        demonstration_dataset_factory=demonstration_dataset_factory,
        environment_factory=lambda seed: make_environment(env_name, seed=seed),
        max_num_learner_steps=100_000,
        seed=seed,
        environment_spec=environment_spec,
    )

experiment = build_offline_config("fixed-dataset", "HalfCheetah-v2", seed=0)
experiments.run_offline_experiment(
    experiment=experiment,
    eval_every=1_000,
    num_eval_episodes=10,
)
```

What `run_offline_experiment` builds:

- one evaluation environment and `EnvironmentSpec`;
- networks from `network_factory`;
- a parent counter;
- a dataset from `demonstration_dataset_factory(dataset_key)`;
- an offline learner through `builder.make_learner(...)`;
- optional evaluation actor/loop using `builder.make_policy(..., evaluation=True)` and `builder.make_actor(...)`;
- optional learner/counter checkpointing;
- a loop of `learner.step()` calls, with evaluation every `eval_every` learner steps.

Set `num_eval_episodes=0` or `evaluator_factories=[]` when no environment evaluation is desired. If `evaluator_factories` is not specified, `OfflineExperimentConfig` requires `environment_factory` so it can create the default evaluator; set `evaluator_factories=[]` to disable evaluation entirely.

## Offline Distributed Experiment

Offline distributed execution uses a separate runner:

```python
program = experiments.make_distributed_offline_experiment(experiment=offline_config)
lp.launch(program, xm_resources=lp_utils.make_xm_docker_resources(program))
```

`make_distributed_offline_experiment` creates counter, learner, evaluator, and optional snapshotter nodes. It does not create replay or actor nodes for training because offline training reads fixed demonstrations through `demonstration_dataset_factory`.

## Manual Offline Learner/Evaluator Loop

Some examples bypass `OfflineExperimentConfig` and instantiate the learner directly. This is useful when the dataset requires custom preprocessing or when the algorithm exposes learner arguments not captured by the builder.

Typical CQL shape:

1. Build an environment only for `EnvironmentSpec` and evaluation.
2. Load a fixed dataset such as a TFDS/RLDS/D4RL transition stream.
3. Wrap it in a random-sample iterator with a JAX key and batch size.
4. Create networks, for example `cql.make_networks(environment_spec)`.
5. Create `cql.CQLLearner(...)` with optimizers, coefficients, random key, and demonstrations iterator.
6. Build an evaluation `ActorCore` from `networks.policy_network.apply` and `networks.sample_eval`.
7. Use `variable_utils.VariableClient(learner, 'policy', device='cpu')` and `actors.GenericActor(...)` for evaluation only.
8. Loop over `learner.step()` and periodically run `acme.EnvironmentLoop` for evaluation episodes.

Typical BC shape is similar, but creates `bc.BCLearner(...)`, passes a BC loss such as `bc.logp()` or `bc.mse()`, and uses a supervised demonstration iterator.

## Converting Local SAC To Distributed D4PG

When a user wants to convert a local continuous-control SAC example to distributed D4PG:

1. Keep the `environment_factory`, `seed`, `max_num_actor_steps`, eval cadence, and JAX experiment runner structure.
2. Replace `from acme.agents.jax import sac` with `from acme.agents.jax import d4pg`.
3. Replace `sac.SACConfig(...)` and `sac.SACBuilder(...)` with `d4pg.D4PGConfig(...)` and `d4pg.D4PGBuilder(...)`.
4. Replace `sac.make_networks(...)` with a `d4pg.make_networks(...)` factory that sets `policy_layer_sizes`, `critic_layer_sizes`, and reward-scale-aware `vmin`/`vmax`.
5. Enable distributed execution with `experiments.make_distributed_experiment(experiment=config, num_actors=...)` and `lp.launch(...)`.
6. Add `experiments.CheckpointingConfig(...)` to `ExperimentConfig.checkpointing` if default checkpointing directory/timing is not appropriate; pass `make_snapshot_models` only if you have a model snapshot factory.
7. Do not install TF agent extras just because Launchpad/Reverb/TensorFlow imports appear: `dm-acme[jax]` already includes the shared TensorFlow/Reverb/Launchpad stack needed by JAX experiment runners.

## Building Network Factories

`ExperimentConfig.network_factory` and `OfflineExperimentConfig.network_factory` receive an `acme.specs.EnvironmentSpec` and return the algorithm-specific networks dataclass or network structure.

Common factories:

- `sac.make_networks(spec, hidden_layer_sizes=(...))`
- `td3.make_networks(spec, policy_layer_sizes=(...), critic_layer_sizes=(...))`
- `d4pg.make_networks(spec, policy_layer_sizes=(...), critic_layer_sizes=(...), vmin=..., vmax=...)`
- `cql.make_networks(spec)`
- `crr.make_networks(spec)`
- `mbop.make_networks(spec, hidden_layer_sizes=(...))`
- `ppo.make_discrete_networks(spec, ...)` or `ppo.make_continuous_networks(spec, ...)` when action-space-specific helpers are preferred
- `mpo.make_control_networks(...)` and `wpo.make_control_networks(...)` for MPO/WPO-style control networks
- `decentralized.network_factory(environment_spec, agent_types, init_default_network_fn)` for multiagent experiments

Always build networks from the same spec shape the environment or offline dataset uses. For offline training, the dataset sample structure must match the learner's expected transition or sequence sample.

## Policies And Evaluators

`ExperimentConfig.get_evaluator_factories()` returns custom `evaluator_factories` if provided. Otherwise it builds one default evaluator using:

- `environment_factory`
- `network_factory`
- `builder.make_policy(..., evaluation=True)` unless deprecated eval policy factories are supplied
- `builder.make_actor(...)`
- `logger_factory`
- `observers`

For custom evaluators, implement a callable with signature compatible with `EvaluatorFactory`: it receives `random_key`, `variable_source`, `counter`, and `make_actor_fn`, and returns a `core.Worker`, commonly an `EnvironmentLoop`.

## Checkpointing And Snapshotting

`experiments.CheckpointingConfig` fields include:

- `max_to_keep`
- `directory`
- `add_uid`
- `time_delta_minutes`
- `keep_checkpoint_every_n_hours`
- `replay_checkpointing_time_delta_minutes`
- `checkpoint_ttl_seconds`

`ExperimentConfig.checkpointing=None` disables checkpointing and snapshotting. Local online `run_experiment` checkpoints learner and parent counter. Local offline `run_offline_experiment` checkpoints learner and counter. Distributed online can also checkpoint replay periodically via `replay_checkpointing_time_delta_minutes`.

Snapshotting uses `make_snapshot_models(networks, environment_spec)` with `acme.jax.snapshotter.JAXSnapshotter`; it converts JAX functions through `jax2tf` and saves TensorFlow SavedModels. Expect TensorFlow imports even in JAX snapshot paths.

## Multiagent Experiment Shape

For decentralized multiagent experiments:

```python
from acme.agents.jax.multiagent import decentralized
from acme.jax import experiments

agent_types = {str(i): decentralized.DefaultSupportedAgent.PPO for i in range(num_agents)}
config_overrides = {agent_id: {"unroll_length": 16} for agent_id in agent_types}
sub_agent_configs = decentralized.default_config_factory(
    agent_types,
    batch_size=64,
    config_overrides=config_overrides,
)
builder = decentralized.DecentralizedMultiAgentBuilder(
    agent_types=agent_types,
    agent_configs=sub_agent_configs,
)

experiment = experiments.ExperimentConfig(
    builder=builder,
    environment_factory=make_multiagent_environment,
    network_factory=lambda spec: decentralized.network_factory(
        spec,
        agent_types,
        init_default_multigrid_network,
    ),
    seed=0,
    max_num_actor_steps=10_000,
)
```

The environment should expose `num_agents` or an equivalent source of agent IDs, produce dict observations and rewards keyed by agent id, consume dict actions, and share a scalar discount.
