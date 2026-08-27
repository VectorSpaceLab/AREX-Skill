---
name: evolvable-modules
description: "Use AgileRL evolvable modules, networks, architecture configs,
  custom network wrappers, and mutation-compatible model building blocks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# AgileRL Evolvable Modules

Use this sub-skill when a task asks for AgileRL `EvolvableModule`, `EvolvableNetwork`, `net_config`, MLP/CNN/LSTM/MultiInput/SimBa configuration, Q/value/actor networks, custom architectures, or wrapping ordinary PyTorch modules for AgileRL mutation compatibility.

## Read First

- `references/modules-and-networks.md` for conceptual relationships and build patterns.
- `references/api-reference.md` for key classes and config objects.
- `references/configuration.md` for `encoder_config`, `head_config`, image/recurrent/multi-input settings.
- `references/troubleshooting.md` for shape, mutation, and custom module errors.
- `scripts/inspect_evolvable_builders.py --help` for safe tiny builder checks.

## Boundaries

- Use `../training-workflows/SKILL.md` for full Gymnasium training loops.
- Use `../hpo-and-mutation/SKILL.md` for mutation probabilities and tournament selection.
- Use `../multi-agent-and-wrappers/SKILL.md` for grouped multi-agent `net_config` and PettingZoo agent IDs.
- This sub-skill owns architecture selection, config validation, custom wrappers, and network construction.

## Common Routes

| Task | Guidance |
| --- | --- |
| Vector observation to discrete action values | Use `QNetwork` with MLP encoder/head config. |
| Image observation policy/value network | Use CNN encoder config and verify channels/order. |
| Dict/Tuple observations | Use MultiInput config with MLP/CNN/LSTM sub-configs as needed. |
| Recurrent/partially observable workflow | Use LSTM config and read training recurrent notes. |
| Custom PyTorch module | Inherit `EvolvableModule` when architecture should mutate, or use `DummyEvolvable` when only RL hyperparameters/weights should mutate. |
| SimBa/ResNet style architecture | Use the corresponding module/network configs and validate dimensions before training. |

## Safe Validation

```bash
python scripts/inspect_evolvable_builders.py --mode mlp
python scripts/inspect_evolvable_builders.py --mode dict
```

The helper constructs tiny Gymnasium spaces and config objects. It does not train.
