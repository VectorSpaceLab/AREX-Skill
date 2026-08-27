---
name: architecture-configuration
description: "Explains VAD's registered detector, head, transformer, dataset,
  coder, and loss components and guides safe edits to VAD configuration
  families."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# VAD architecture and configuration

Use this route for model internals, plugin registration, config inheritance, stage selection, model variants, or VADv2 integration questions.

## Route

1. Read [configuration-reference.md](references/configuration-reference.md) to select tiny/base and stage-1/stage-2/e2e.
2. Read [model-and-plugin-api.md](references/model-and-plugin-api.md) before changing a registered component or tensor contract.
3. Run `python scripts/check_config_contract.py CONFIG --check-plugin` for a safe config-only check. It does not build a model or access data.
4. Keep `plugin=True` and the plugin directory importable before OpenMMLab builders resolve custom registry names.
5. For data files and temporal annotations, use [data-preparation](../data-preparation/SKILL.md); for launch/checkpoint behavior use [training-evaluation](../training-evaluation/SKILL.md).

Actual VAD model execution is CUDA/native-extension dependent. A config parse is not proof that the detector can be built.

## Scope boundaries

- Data roots, converter, and CAN-bus: [data-preparation](../data-preparation/SKILL.md).
- Train/eval CLI and released-weight normalization: [training-evaluation](../training-evaluation/SKILL.md).
- Prediction rendering: [visualization](../visualization/SKILL.md).

See [troubleshooting.md](references/troubleshooting.md) for registry, compiler, shape, and stage failures.
