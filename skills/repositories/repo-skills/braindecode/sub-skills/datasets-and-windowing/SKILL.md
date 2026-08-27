---
name: datasets-and-windowing
description: "Guides braindecode dataset construction, MNE and array conversion,
  metadata-aware windowing, splitting, and safe serialization for
  electrophysiological signals."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Datasets and windowing

Use this route when the task starts with NumPy arrays, MNE `Raw`/`Epochs`,
BIDS-like recordings, or a braindecode dataset and asks for targets, metadata,
windows, splits, concatenation, or persistence.

## Workflow

1. Normalize `X` as `(trials, channels, time)` and record `sfreq`, channel names,
   units, subject/session identifiers, and target semantics.
2. For local arrays use `create_from_X_y`; for MNE objects use the MNE
   conversion helpers. Inspect one item and its description before windowing.
3. Choose event windows when annotations/events define trial boundaries, fixed
   windows for continuous recordings, and target-channel windows only when the
   target is represented as a channel in the raw object.
4. Split by subject/session before overlapping windows. Use descriptions to
   filter/partition rather than random row splits when assessing generalization.
5. Persist only after validating metadata and choosing a writable, disposable
   path. Treat Hub/BIDS/MOABB/TUH/Sleep integrations as optional data acquisition
   workflows, not offline smoke tests.

Read [API reference](references/api-reference.md) for constructors and shapes,
[workflows](references/workflows.md) for local conversion/windowing and
serialization recipes, and [optional integrations](references/optional-integrations.md)
when a named external dataset or Hub is required. Use
[troubleshooting](references/troubleshooting.md) before retrying a failed
conversion or window operation. Run [the synthetic smoke helper](scripts/smoke_dataset.py)
to validate local behavior without network access.
