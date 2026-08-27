---
name: simulation-and-recording
description: "Assemble and run Brian2 simulations with explicit or magic
  networks, clocks, snapshots, scheduling, progress, and runtime diagnostics."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Simulation and recording

Use this route to control a Brian2 simulation after its model objects have been
specified. Prefer an explicit `Network` for reusable experiments, objects held
in containers, staged construction, train/test loops, or any run that must be
unambiguous. Use magic `run` only for a small, visible, single-scope model.

- Build the network, choose clocks and scheduling, run, snapshot, restore, seed
  trials, and diagnose progress/profile/schedule here.
- Send monitor construction, recording variables, and monitor result access to
  [recording](../recording/SKILL.md); send equations and units to
  [modeling](../modeling/SKILL.md) and [units-and-equations](../units-and-equations/SKILL.md);
  send devices, code-generation targets, and standalone builds to
  [code-generation](../code-generation/SKILL.md).
- A `network_operation` is a control callback boundary: create/configure and
  schedule it here, but keep model/monitor implementation details in their
  owning routes.
- Use `collect()` to inspect magic membership, but construct
  `Network(collect())` and add hidden containers before the first run; it is not
  a transfer mechanism for objects that have already been simulated.

Read only the reference needed for the operation:

- [API reference](references/api-reference.md) — objects, arguments, and
  invariants.
- [Workflows](references/workflows.md) — explicit/magic construction,
  clocks, scheduling, progress, and diagnostics.
- [Multiple runs](references/multiple-runs.md) — `start_scope`, trials, and
  store/restore/randomness.
- [Troubleshooting](references/troubleshooting.md) — install/import,
  optional dependencies, data/configuration, API misuse, and workflow errors.

For a tiny local smoke of explicit `Network` and snapshot/restore, use
`scripts/network_smoke.py`. It is intentionally small and does not replace
project-level verification.
