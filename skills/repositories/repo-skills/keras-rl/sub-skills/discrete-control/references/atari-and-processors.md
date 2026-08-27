# Atari and processor concepts for discrete DQN

This is reference-only guidance for adapting discrete DQN patterns to Atari-style pixel observations. It is not a full Atari runner and does not download ROMs, install extras, launch rendering, or perform long training.

## When to use this reference

Use this when a task mentions Atari DQN, frame stacking, reward clipping, 84x84 grayscale preprocessing, `LinearAnnealedPolicy`, `EpsGreedyQPolicy`, or `SequentialMemory(window_length=4)`.

Route detailed custom `Processor` base-class design, callback wiring, logging, and `Agent.fit`/`Agent.test` lifecycle mechanics to the core-extension-and-logging sub-skill.

## Atari-style preprocessing contract

A typical Atari DQN processor performs three transformations:

| Hook | Concept | Expected result |
| --- | --- | --- |
| `process_observation` | Convert RGB frame to grayscale, resize to 84x84, store as `uint8` | memory-efficient single frame with shape `(84, 84)` |
| `process_state_batch` | Convert a stacked batch from `uint8` to `float32` and divide by `255.` | normalized batch for the neural network |
| `process_reward` | Clip reward into `[-1., 1.]` | stabilizes value targets in long Atari training |

Do not store normalized `float32` frames in replay memory unless memory use is acceptable. The common pattern stores compact `uint8` frames and normalizes only batches passed into the model.

## Frame stack and model shape

Atari-style DQN commonly uses:

```python
INPUT_SHAPE = (84, 84)
WINDOW_LENGTH = 4
memory = SequentialMemory(limit=1000000, window_length=WINDOW_LENGTH)
```

The model sees a state stack shaped like `(WINDOW_LENGTH, 84, 84)` before any backend-specific dimension ordering adjustment. A convolutional model then permutes or interprets axes according to the configured Keras image dimension ordering.

Conceptual model outline:

1. Optional permutation for backend image ordering.
2. Convolution with 32 filters and an 8x8 kernel / stride 4.
3. Convolution with 64 filters and a 4x4 kernel / stride 2.
4. Convolution with 64 filters and a 3x3 kernel / stride 1.
5. Flatten.
6. Dense 512 + ReLU.
7. Dense `nb_actions` + linear activation.

The final output remains one Q value per discrete action.

## Atari-style policy and DQN parameters

Common Atari-style choices:

```python
policy = LinearAnnealedPolicy(
    EpsGreedyQPolicy(),
    attr='eps',
    value_max=1.,
    value_min=.1,
    value_test=.05,
    nb_steps=1000000,
)

dqn = DQNAgent(
    model=model,
    nb_actions=nb_actions,
    policy=policy,
    memory=memory,
    processor=processor,
    nb_steps_warmup=50000,
    gamma=.99,
    target_model_update=10000,
    train_interval=4,
    delta_clip=1.,
)
```

Interpretation:

- `nb_steps_warmup=50000`: collect enough replay before learning starts.
- `train_interval=4`: train every fourth environment step.
- `target_model_update=10000`: hard-copy target weights every 10,000 steps.
- `delta_clip=1.`: use clipped Huber loss, common for high-variance pixel tasks.
- `value_test=.05`: preserve a small amount of random exploration during evaluation.

## Heavy workflow exclusions

Atari training is intentionally excluded from the bundled smoke helper because it typically requires optional packages, a legal ROM setup, large replay memory, long training, and sometimes display/rendering concerns. For this generated skill:

- Use the bundled smoke helper for compile/build checks on lightweight vector-shaped models.
- Treat Atari guidance as a shape, memory, policy, and processor design reference.
- Do not assume `gym[atari]`, ALE/ROM packages, Pillow, or rendering support are installed.
- Do not attempt to auto-download ROMs or run long Atari training as a routine verification step.

## Compatibility checkpoints

Before adapting this to a real Atari run:

- Confirm the installed Gym/ALE version and legal ROM availability.
- Confirm the environment's reset/step API shape. keras-rl expects legacy Gym-style `reset() -> observation` and `step(action) -> observation, reward, done, info`; newer Gym/Gymnasium APIs often need wrappers.
- Confirm Keras image dimension ordering helpers are available in the chosen Keras version.
- Confirm a legacy Keras backend can compile the convolutional model and DQN target model.
- Keep any processor implementation self-contained in the consuming project; do not depend on source-checkout examples.
