---
name: data-preparation
description: "Prepares and validates the nuScenes, CAN-bus, and VAD temporal
  annotation inputs required for VAD training, evaluation, and visualization."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# VAD data preparation

Use this route when the task is to prepare nuScenes for VAD, generate temporal info files, validate CAN-bus data, or diagnose missing dataset inputs.

## Route

1. Read [data-contract.md](references/data-contract.md) and choose a canonical data root.
2. Run the bundled, read-only layout checker before invoking any converter:
   `python scripts/check_data_layout.py --data-root DATA_ROOT --canbus-root CANBUS_ROOT --require-train --require-val`.
3. Acquire and unpack nuScenes and the CAN-bus expansion separately; this skill does not download data.
4. Generate VAD-specific temporal annotations with the command contract in the reference. Do not substitute stock MMDetection3D info PKLs.
5. Re-run the checker, then use [training-evaluation](../training-evaluation/SKILL.md) only after the required PKLs and map annotation are present.

The converter is data- and dependency-heavy. Treat a successful argument parse as different from a successful conversion. Full conversion was intentionally not run during construction.

## Scope boundaries

- Model/plugin and config registration: [architecture-configuration](../architecture-configuration/SKILL.md).
- Train/evaluate and checkpoint normalization: [training-evaluation](../training-evaluation/SKILL.md).
- Render an existing result artifact: [visualization](../visualization/SKILL.md).

For symptoms, use [troubleshooting.md](references/troubleshooting.md). The bundled checker is a safe validator, not a downloader or converter.
