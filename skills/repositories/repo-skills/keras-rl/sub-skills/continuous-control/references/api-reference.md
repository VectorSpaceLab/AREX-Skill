# continuous-control API reference

This reference is for keras-rl's continuous-action agents and their immediately required collaborators. It assumes an installed keras-rl package with standalone Keras 2.x-style APIs.

## Agent signatures

| API | Signature | Key contract |
| --- | --- | --- |
| `rl.agents.ddpg.DDPGAgent` | `DDPGAgent(nb_actions, actor, critic, critic_action_input, memory, gamma=0.99, batch_size=32, nb_steps_warmup_critic=1000, nb_steps_warmup_actor=1000, train_interval=1, memory_interval=1, delta_range=None, delta_clip=inf, random_process=None, custom_model_objects={}, target_model_update=0.001, **kwargs)` | Deterministic actor plus critic Q-function for continuous actions. `critic_action_input` must be the exact Keras `Input` object contained in `critic.inputs`. |
| `DDPGAgent.compile` | `compile(optimizer, metrics=[])` | Pass one optimizer to clone for actor/critic, or pass exactly two optimizers as `[actor_optimizer, critic_optimizer]`. Metrics apply to the critic; `mean_q` is added internally. |
| `rl.agents.dqn.NAFAgent` / `ContinuousDQNAgent` | `NAFAgent(V_model, L_model, mu_model, random_process=None, covariance_mode='full', *args, **kwargs)` | Continuous DQN / Normalized Advantage Function. Inherited args include `nb_actions`, `memory`, `gamma`, `batch_size`, `nb_steps_warmup`, `train_interval`, `memory_interval`, `target_model_update`, `delta_clip`, and `custom_model_objects`. |
| `NAFAgent.compile` | `compile(optimizer, metrics=[])` | Builds a combined Q model from action input, observation input(s), `V_model`, `mu_model`, and `L_model`. A single optimizer is expected. |
| `rl.memory.SequentialMemory` | `SequentialMemory(limit, **kwargs)` | Use with `window_length=1` for Pendulum-style examples unless the model is explicitly built for longer observation windows. |
| `rl.random.OrnsteinUhlenbeckProcess` | `OrnsteinUhlenbeckProcess(theta, mu=0.0, sigma=1.0, dt=0.01, size=1, sigma_min=None, n_steps_annealing=1000)` | Temporally correlated exploration noise; commonly used for physical control. `sample()` must produce shape `(nb_actions,)`. |
| `rl.random.GaussianWhiteNoiseProcess` | `GaussianWhiteNoiseProcess(mu=0.0, sigma=1.0, sigma_min=None, n_steps_annealing=1000, size=1)` | Independent Gaussian exploration noise; also must match `(nb_actions,)`. |

## DDPG model contracts

| Component | Required shape/wiring | Notes |
| --- | --- | --- |
| `actor` | Single output tensor. Per sample, output flattens to `(nb_actions,)`. | A Pendulum-style actor often uses `Flatten(input_shape=(window_length,) + observation_shape)`, dense hidden layers, then `Dense(nb_actions)` with `linear` or environment-bounded activation such as `tanh`. |
| `critic` | Single output tensor, usually scalar Q value `(None, 1)`. Inputs include the action input plus observation input(s). | The action input should have `Input(shape=(nb_actions,), name=...)`. Concatenate action and flattened observation features before dense Q layers, or insert action after a first observation feature block. |
| `critic_action_input` | The exact action `Input` tensor object passed into the critic `Model`. | Passing a different `Input` object with the same shape fails; identity matters. |
| multi-input observations | Actor observation inputs and critic non-action inputs must correspond in number and order. | DDPG compile replaces the critic's designated action input with `actor(state_inputs)` and calls the critic on that combined input list. |
| replay memory | `SequentialMemory(limit=..., window_length=...)`. | `window_length` must match model input shapes. The examples and compile smokes use `window_length=1`. |

### DDPG compile behavior

- `compile('sgd')` or `compile(Adam(...))` uses one optimizer and clones it for the other network.
- `compile([actor_optimizer, critic_optimizer])` uses separate optimizers; this is the common actor/critic learning-rate pattern.
- A list or tuple must have exactly two entries. More or fewer entries raise a `ValueError` about optimizer count.
- `target_model_update < 1` means soft target updates; `target_model_update >= 1` means hard update every integer number of steps.

## NAF / CDQN model contracts

NAF decomposes the Q-function into `Q(s, a) = V(s) + A(s, a)`, where `mu_model` produces the greedy continuous action and `L_model` parameterizes a positive-definite matrix used by the advantage term.

| Component | Required shape/wiring | Notes |
| --- | --- | --- |
| `V_model` | Observation input(s) only; output shape `(None, 1)`. | Learns the state-value term. |
| `mu_model` | Observation input(s) only; output shape `(None, nb_actions)`. | Produces deterministic continuous action before noise is added. |
| `L_model` | Inputs are `[action_input] + observation_inputs`; output shape depends on covariance mode. | Build it with an action `Input(shape=(nb_actions,))` plus observation input(s), even though the mathematical role is to parameterize the advantage term. |
| `covariance_mode='full'` | `L_model` output units must be `(nb_actions * nb_actions + nb_actions) // 2`. | Parameterizes a lower-triangular matrix. Best for low-dimensional actions. |
| `covariance_mode='diag'` | `L_model` output units must be `nb_actions`. | Cheaper diagonal approximation; useful for debugging or larger action dimensions. |
| random process | Optional, but if present `sample()` must match `(nb_actions,)`. | Same sizing rule as DDPG. |

## Continuous action assumptions

- These agents expect continuous, vector-valued actions. If the environment action space is discrete, route to a discrete-control agent instead.
- Assert or check that the action space shape has one dimension before deriving `nb_actions`.
- The agent does not automatically scale actions to Gym action bounds. Use output activations, wrappers, or a `Processor.process_action` implementation when action bounds require clipping/scaling.
- `Agent.fit`, `Agent.test`, custom processors, callbacks, and logging are shared core topics, not owned by this sub-skill.
