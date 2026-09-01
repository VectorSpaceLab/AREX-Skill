---
name: lifelong_stream_protocol
description: Build one-pass lifelong language-learning streams without exposing dataset identifiers to the model.
---

# Lifelong Stream Protocol

## When To Use
Use this skill when reconstructing the episodic-memory lifelong language learning method from de Masson d'Autume et al. without relying on an original implementation repository.

## Inputs
- Small text examples represented as dictionaries.
- Deterministic configuration values such as memory probability, replay interval, K, and adaptation steps.

## Outputs
- Auditable Python objects or JSON-serializable dictionaries matching the module contract.
- Logs that expose mechanism execution rather than only final metrics.

## Workflow
1. Group examples by dataset order only outside model-visible fields.
2. Emit stream rows containing id, text, and label but no dataset/domain key.
3. Keep a separate audit table for retention probes and reporting.

## Validation
Run `python tests/test_lifelong_stream_protocol.py` from this skill directory.

## Limitations
The scripts are deterministic proxy utilities for bounded recovery. They do not train BERT or reproduce the full paper-scale datasets.
