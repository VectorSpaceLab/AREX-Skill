# Module Reference

## Specification forms

Tensorforce module arguments generally accept:

- a dictionary with `type` plus keyword arguments;
- a JSON file path from the user's project;
- a Python import path to a Tensorforce-compatible module class;
- a class/callable for advanced users;
- default shorthand where a list or scalar is interpreted by the owning module.

Do not point users at benchmark JSON files from a source checkout. Copy the needed structure into their project.

## Important module families

| Family | Common registry names | Used in |
|---|---|---|
| Networks | `auto`, `layered`, `keras` | `network`, policy/baseline network specs |
| Layers | `dense`, `conv1d`, `conv2d`, `flatten`, `embedding`, `linear`, `register`, `retrieve`, `reuse`, `lstm`, `gru`, `self_attention`, `linear_normalization`, `exponential_normalization`, `clipping`, `sequence`, `image`, `keras` | network and preprocessing specs |
| Memories | `recent`, `replay`, `minimum`/default behavior depending on agent | trainable agent memory/update behavior |
| Objectives | `policy_gradient`, `deterministic_policy_gradient`, `value`, `plus` | generic `tensorforce` agent objective specs and algorithm internals |
| Optimizers | TensorFlow optimizer wrapper names plus `adam`/`tf_optimizer` style specs, `multi_step`, `subsampling_step`, `linesearch_step`, `natural_gradient`, `evolutionary`, `synchronization`, `clipping_step` | `optimizer`, `baseline_optimizer`, algorithm kwargs |
| Parameters | `constant`, `linear`, `exponential`, `piecewise_constant`, `decaying`, `ornstein_uhlenbeck`, `random` | exploration, learning-rate-like schedules, noise |
| Policies/distributions | stochastic/value/action-value policy internals; categorical, gaussian, beta, and bernoulli distributions inferred from action specs | algorithm policy behavior |

Run the bundled registry script for exact names in the installed runtime:

```bash
python scripts/inspect_module_registry.py
```

## Config dictionary

`config` is passed to the agent, not to every module. Useful fields include `device`, `eager_mode`, `seed`, `create_debug_assertions`, and `tf_log_level`. Use CPU and low log verbosity for smoke checks; enable eager/debug assertions only when diagnosing TensorFlow graph behavior.
