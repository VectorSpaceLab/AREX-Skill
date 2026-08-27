---
name: brian2
description: "Use Brian2 for clock-driven spiking-neural-network modeling,
  simulation, synaptic connectivity, input generation, recording, physical-unit
  equations, spatial neurons, runtime code generation, and C++ standalone
  workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Brian2

Brian2 is a Python simulator for spiking neural networks. Use this skill when a
request names Brian2, `NeuronGroup`, `Synapses`, `Network`, monitors, Brian
units/equations, `set_device`, `cpp_standalone`, or a related simulation error.
This skill is a self-contained operating guide for Brian2 2.9.0-style APIs; it
does not require reopening the source repository.

## Start safely

1. Establish an isolated Python environment with Python >=3.12.
2. Install the public distribution with `python -m pip install brian2` (or use
   the documented Conda package). Install optional packages only for a selected
   workflow: a C++ compiler for Cython/standalone, GSL for GSL state updaters,
   and plotting/scientific packages only when needed.
3. Verify the installation from a neutral working directory:
   `python -c "import brian2; print(brian2.__version__)"`.
4. For a read-only environment report, run
   [`scripts/check_brian2_env.py`](scripts/check_brian2_env.py). It reports
   package/import/compiler/optional-dependency signals without changing files.
5. Begin with `prefs.codegen.target = "numpy"` and a tiny model when compiler
   availability is unknown. Move to Cython or C++ standalone only after reading
   the code-generation route and its limitations.

## Choose the route

- **Neuron equations, thresholds, resets, refractory behavior, subgroups, or
  custom events:** read [`modeling`](sub-skills/modeling/SKILL.md).
- **Units, equation-string grammar, namespaces, stochastic terms, or state
  updaters:** read [`units-and-equations`](sub-skills/units-and-equations/SKILL.md).
- **Synapses, connectivity, delays, STDP, Poisson input, replay, or
  `TimedArray`:** read [`synapses-and-inputs`](sub-skills/synapses-and-inputs/SKILL.md).
- **`run`, `Network`, clocks, scheduling, snapshots, repeated trials, or
  progress/profile diagnostics:** read
  [`simulation-and-recording`](sub-skills/simulation-and-recording/SKILL.md).
- **Spike/state/rate/event monitors, subset recording, export, or memory
  control:** read [`recording`](sub-skills/recording/SKILL.md).
- **Cython/NumPy targets, `set_device`, C++ standalone, compiler/cache issues,
  or GSL:** read [`code-generation`](sub-skills/code-generation/SKILL.md).
- **Morphology, compartments, `SpatialNeuron`, or SWC/section geometry:** read
  [`spatial-models`](sub-skills/spatial-models/SKILL.md).
- **Installation, preferences, cache, logging, missing dependencies, or a
  cross-cutting failure:** read
  [`configuration-and-troubleshooting`](sub-skills/configuration-and-troubleshooting/SKILL.md).

Most real tasks cross routes: define and validate equations first, create
synapses and inputs second, assemble an explicit `Network` for nontrivial
lifecycle control, add monitors before running, and choose a device only after
the CPU/NumPy behavior is understood. Follow the links above rather than
copying every API table into this router.

## Core invariants

- A model equation is a Brian expression string, not arbitrary Python. Use
  Brian's bare supported functions (`sin`, `exp`, `clip`, `rand`, etc.) and
  declare dimensions explicitly.
- `Synapses(...)` defines pathways but does not create connections; call
  `connect(...)` before assigning synaptic state.
- A `StateMonitor` records at its configured schedule (default `when="start"`),
  and its array index is relative to the selected recording indices.
- Magic `run` collects visible objects only. Prefer `Network(...)` when objects
  are in containers, runs are staged, or train/test snapshots must be exact.
- A CPU/NumPy smoke does not prove Cython or C++ standalone. Those require a
  compiler-aware check and, for a standalone claim, an actual temporary build.
- Keep optional GSL, plotting, notebook, SciPy, Pandas, and multiprocessing
  capabilities explicit; absence of an optional package is not a core Brian2
  import failure.

## Shared references

- Read [`references/repo-provenance.md`](references/repo-provenance.md) before
  deciding whether this graph matches a checkout or needs refreshing.
- Read [`references/troubleshooting.md`](references/troubleshooting.md) for
  cross-cutting installation, import, dependency, cache, and lifecycle triage.
- Use the bundled smoke scripts in the owning sub-skill only after checking
  their `--help` output and selecting a tiny, bounded fixture.
