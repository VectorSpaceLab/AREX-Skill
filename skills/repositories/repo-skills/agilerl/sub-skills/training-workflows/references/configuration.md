# Classical Training Configuration

## `INIT_HP` Patterns

PPO/on-policy commonly uses:

- `POP_SIZE`, `BATCH_SIZE`, `LR`, `LEARN_STEP`, `GAMMA`
- `GAE_LAMBDA`, `ACTION_STD_INIT`, `CLIP_COEF`, `ENT_COEF`, `VF_COEF`, `MAX_GRAD_NORM`, `TARGET_KL`, `UPDATE_EPOCHS`
- `CHANNELS_LAST` for image observations

DQN/RainbowDQN/DDPG/TD3 off-policy commonly uses:

- `POP_SIZE`, `BATCH_SIZE`, `LR`, `GAMMA`, `LEARN_STEP`, `TAU`
- DQN/Rainbow fields such as `DOUBLE`, n-step/prioritized replay settings, or distributional settings as required by the selected algorithm
- `LEARNING_DELAY`, `MEMORY_SIZE`, `EVO_STEPS`, and evaluation settings from the distilled patterns in this reference

## `net_config`

A typical MLP config:

```python
NET_CONFIG = {
    "encoder_config": {"hidden_size": [32, 32], "activation": "ReLU"},
    "head_config": {"hidden_size": [32]},
}
```

Use `../evolvable-modules/SKILL.md` for CNN/LSTM/MultiInput/SimBa details.

## YAML Configs

AgileRL commonly uses YAML-style training patterns for PPO, DQN, RainbowDQN, DDPG, TD3, recurrent variants, multi-input, and LLM workflows. When translating a config into code:

- Preserve algorithm-specific hyperparameter names.
- Keep architecture config under the expected `encoder_config`/`head_config` shape.
- Do not copy benchmark-scale `max_steps` into smoke tests.
- Treat paths, logging, and distributed launch settings as environment-specific.

## Logging And Checkpoints

- Set `wb=False` or equivalent when W&B is not configured.
- Decide where checkpoints go before a long run; avoid writing into package install directories.
- For reproducibility, set random seeds in mutation config and environment setup when supported.
