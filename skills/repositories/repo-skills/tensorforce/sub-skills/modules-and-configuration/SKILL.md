---
name: modules-and-configuration
description: "Configure Tensorforce networks, layers, memories, policies,
  objectives, optimizers, parameters, preprocessing, and config dictionaries."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Modules and Configuration

Use this sub-skill when a task asks how to express Tensorforce module specifications, choose network/layer/preprocessing/memory/objective/optimizer/policy/parameter components, translate JSON/dict configs, or debug unknown module `type` values.

## Route by need

- Read [module reference](references/module-reference.md) for registry names and where each module family is used.
- Read [network and layer recipes](references/network-and-layer-recipes.md) for `network='auto'`, layered networks, register/retrieve DAGs, preprocessing, and Keras-layer boundaries.
- Run [scripts/inspect_module_registry.py](scripts/inspect_module_registry.py) in the user's Tensorforce environment to print installed registry names.
- Use [troubleshooting](references/troubleshooting.md) for unknown module names, invalid shorthand, shape issues, TensorFlow Addons/Keras surprises, or debug/eager mode confusion.

## Boundaries

This sub-skill owns configuration shape and component selection. Route agent lifecycle, action masks, and `act`/`observe` loops to [agents-and-specifications](../agents-and-specifications/SKILL.md); route environment state/action discovery to [environments-and-interaction](../environments-and-interaction/SKILL.md); route full training loops to [runner-and-cli-workflows](../runner-and-cli-workflows/SKILL.md).

## Minimal pattern

```python
agent = dict(
    agent='ppo',
    network=[dict(type='dense', size=64, activation='tanh')],
    batch_size=10,
    update_frequency=2,
    learning_rate=3e-4,
    baseline=dict(type='auto', size=32, depth=1),
    state_preprocessing='linear_normalization',
    config=dict(device='CPU', seed=7),
)
```

Before a long run, instantiate the agent with the target environment and call `agent.get_specification()` or `agent.get_architecture()` to verify Tensorforce accepted the config.
