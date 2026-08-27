---
name: optimizer-networks
description: "Guide creation, selection, inspection, serialization, and
  troubleshooting of optimizer network modules and preprocessing modules."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# optimizer-networks

Use this sub-skill when the task is to choose, inspect, serialize, or debug optimizer network modules and preprocessing modules.

## Include
- `networks.factory` and `networks.save`
- `StandardDeepLSTM`, `CoordinateWiseDeepLSTM`, `KernelDeepLSTM`
- `Sgd` and `Adam`
- initializer forms, saved `.l2l` network state, and `net_path` loading
- `preprocess.Clamp` and `preprocess.LogAndSign`

## Route elsewhere
- Variable-to-net assignment and meta-optimizer wiring: `meta-optimizer-api`
- Problem factories and data side effects: `problem-factories`
- `train.py` / `evaluate.py` workflows: `training-evaluation`

## Use the references
- [Network API](references/network-api.md)
- [Preprocessing](references/preprocessing.md)
- [Troubleshooting](references/troubleshooting.md)
- [Config inspector](scripts/inspect_network_config.py)
