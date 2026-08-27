---
name: synapses-and-inputs
description: "Define Brian2 2.9.0 synaptic connectivity, event pathways, delays,
  plasticity, and explicit or stochastic input sources."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Synapses and inputs

Use this route when the task connects spike-producing groups, applies synaptic
code, configures delays or plasticity, or supplies Poisson, timed, or explicit
spike input in Brian2 2.9.0. The route is deliberately workflow-oriented:
first define the source/target and synaptic equations, then create connections,
assign existing synapse state, and only then run and inspect event effects.

## Route map

- API signatures, indexing, pathway names, and input-class boundaries: [api-reference.md](references/api-reference.md)
- End-to-end construction, timing, replay, and validation recipes: [workflows.md](references/workflows.md)
- Conditional/probabilistic connectivity, event-driven traces, STDP, and summed variables: [connectivity-and-plasticity.md](references/connectivity-and-plasticity.md)
- Install/import, optional dependency, data/configuration, API misuse, timing, and workflow recovery: [troubleshooting.md](references/troubleshooting.md)
- Run a tiny deterministic connectivity and delayed-spike assertion: [connectivity_smoke.py](scripts/connectivity_smoke.py)

## Operating contract

1. Keep neuron equation semantics, units, thresholds, resets, and state-updater
   choice with [modeling](../modeling/SKILL.md) and
   [units-and-equations](../units-and-equations/SKILL.md). This route consumes a
   valid spike source and target variable.
2. A `Synapses` constructor defines model/pathways; it does **not** create
   synapses. Call `connect(...)` before indexing or assigning synaptic arrays.
3. Use explicit `_pre`/`_post` suffixes when a name could be ambiguous. Assign
   `w`, `delay`, and other synapse state after the relevant connections exist.
4. Treat event-driven variables as values updated at event times, not as
   continuously observable traces. Ensure their dependencies remain compatible
   with event-driven integration.
5. Choose `PoissonGroup` when individual spikes matter, `PoissonInput` when only
   aggregate independent input matters, `SpikeGeneratorGroup` for reproducible
   event schedules, and `TimedArray` for sampled time functions.
6. Validate units, `dt`/delay alignment, event binning, and output timing with a
   small fixture before scaling. Monitor analysis belongs to
   [recording](../recording/SKILL.md); device and standalone restrictions belong
   to [code-generation](../code-generation/SKILL.md).

The bundled smoke script is read-only with respect to the repository and uses
only a tiny in-memory runtime simulation; it does not download data or run
native repository tests.
