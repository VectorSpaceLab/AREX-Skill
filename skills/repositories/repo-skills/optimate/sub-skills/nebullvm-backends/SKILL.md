---
name: nebullvm-backends
description: "Guides NebullVM data/device handling, backend selection, compiler
  lists, and optional dependency troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NO_LICENSE
---

# NebullVM backends

Use this sub-skill when the user is asking about the lower-level NebullVM support layer behind Speedster: data shapes, device parsing, backend lists, optional dependencies, or compiler selection.

## Triggers

- `DataManager` input formats and dataloader conversion.
- `check_device`, `gpu_is_available`, TPU fallback, or AWS Neuron fallback behavior.
- Auto-installer framework/backend/compiler selectors.
- Compiler backend availability questions.
- Optional dependency or platform-specific install failures.

## Read next

- `references/api-reference.md` for the verified enums, dataclasses, and selector functions.
- `references/data-and-devices.md` for the accepted data and device formats.
- `references/compiler-selection.md` for the framework/backend/compiler decision logic.
- `references/troubleshooting.md` for compiler, platform, and optional dependency failures.
- `scripts/nebullvm_backend_probe.py` for a safe selector/device/import smoke probe.
- `../speedster-optimization/SKILL.md` when the question is about the higher-level optimization API rather than the support layer.

## What to include

- Public enums and dataclasses from `nebullvm.core.models`.
- `DataManager` and `PytorchDataset` behavior.
- Backend and compiler selection rules from `auto_installer`.
- Device parsing and accelerator fallback behavior.

## What to exclude

- Direct training workflows or long optimization runs.
- Unsafe shell installer execution unless the user explicitly wants backend installation.

## Quick decision rule

If the user is trying to understand which framework/backend/compiler combination is valid, start here. If they are already calling `optimize_model`, read the Speedster sub-skill first.
