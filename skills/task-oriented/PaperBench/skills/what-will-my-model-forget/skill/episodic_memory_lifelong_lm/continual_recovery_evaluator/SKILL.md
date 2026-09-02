---
name: continual_recovery_evaluator
description: Evaluate mechanism-faithful continual-learning recovery metrics and gate proxy evidence.
---

# Continual Recovery Evaluator

## When To Use
Use this skill when reconstructing the episodic-memory lifelong language learning method from de Masson d'Autume et al. without relying on an original implementation repository.

## Inputs
- Small text examples represented as dictionaries.
- Deterministic configuration values such as memory probability, replay interval, K, and adaptation steps.

## Outputs
- Auditable Python objects or JSON-serializable dictionaries matching the module contract.
- Logs that expose mechanism execution rather than only final metrics.

## Workflow
1. Compute baseline and episodic retained accuracy on the same labels.
2. Report gain over baseline as the proxy metric.
3. Require explicit mechanism booleans before accepting proxy success.

## Validation
Run `python tests/test_continual_recovery_evaluator.py` from this skill directory.

## Limitations
The scripts are deterministic proxy utilities for bounded recovery. They do not train BERT or reproduce the full paper-scale datasets.
