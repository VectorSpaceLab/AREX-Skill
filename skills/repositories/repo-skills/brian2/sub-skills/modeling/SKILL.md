---
name: modeling
description: "Build and validate Brian2 2.9.0 neuron populations, equations,
  thresholds, resets, refractoriness, events, state initialization, subgroups,
  and shared or linked variables."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Modeling

Use this route when a task defines neuron state or neuron-local behavior in
Brian2 2.9.0: `NeuronGroup`, model equations, parameters and subexpressions,
threshold/reset/refractory behavior, custom events, initialization, subgroups,
`run_regularly`, shared variables, or linked variables. Start with the smallest
explicit `Network` and a NumPy run before adding connectivity, monitors, or a
device target.

## Route map

- Constructor arguments, equation flags, state views, events, and links: read
  [the API reference](references/api-reference.md).
- Construction recipes and validation gates: read
  [the workflows](references/workflows.md).
- Install/import, optional dependency, data/configuration, API misuse, and
  workflow recovery: read [troubleshooting](references/troubleshooting.md).
- Run a plotting-free heterogeneous LIF fixture with a custom event:
  `python scripts/model_smoke.py --help`, then
  `python scripts/model_smoke.py --target numpy`.

## Operating contract

1. Declare every heterogeneous parameter in the model (`tau : second`,
   `drive : 1`, etc.). A Python value outside the model is a scalar namespace
   value, not a per-neuron parameter. Assign state immediately after creating
   the group, with units unless the raw underscore view is intentional.
2. Make the model contract explicit: differential equations, compatible units,
   a boolean threshold, reset statements, and a refractory rule when repeated
   threshold crossings must be suppressed. A threshold with no reset is legal
   only when counting events or when the state naturally exits the condition.
3. Treat model strings and state-assignment strings as Brian abstract code, not
   arbitrary Python. Use Brian-supported functions and vectorizable statements;
   do not put imports, comprehensions, object methods, I/O, or general Python
   control flow in them. A user-defined function must have a Brian unit contract
   and an explicit namespace entry; target-specific implementations are a
   separate code-generation concern.
4. Use `Network(group, ...)` for validation and run it for `0*ms` before a tiny
   positive duration. Constructor success alone does not prove that namespace,
   units, parser, event, or code-generation checks will pass.
5. Subgroups are contiguous views, not copies. Assigning through `G[:k]`
   changes the parent. Their `i` is subgroup-relative; use parent state or an
   explicit parameter when an absolute identity is required.
6. `(shared)` means one scalar value for the complete group. `(linked)` means
   live reference storage and must be bound with `linked_var`; check dimensions,
   source/target sizes, and any integer mapping before running.
7. Keep external names reproducible: prefer a group `namespace={...}` or an
   explicit `Network.run(..., namespace={...})`. Do not rely on a coincidental
   caller local or leave competing definitions across namespaces.
8. Keep custom event conditions and side effects model-local. Event recording,
   synaptic pathways, physical-unit/parser depth, monitor details, execution or
   device selection belong to the routes named below.

## Boundaries

Route synaptic connectivity, pre/post code, delays, inputs, and plasticity to
[synapses-and-inputs](../synapses-and-inputs/SKILL.md); monitor selection and
monitor data to [recording](../recording/SKILL.md); and detailed unit/parser,
state-updater, or unit-aware function questions to
[units-and-equations](../units-and-equations/SKILL.md). Route network lifecycle,
cross-object scheduling, and multiple-run behavior to
[simulation-and-recording](../simulation-and-recording/SKILL.md); route devices,
compiler setup, and code-generation target selection to
[code-generation](../code-generation/SKILL.md). Keep only the neuron-local
construction contract here and follow the linked route rather than duplicating
those APIs.
