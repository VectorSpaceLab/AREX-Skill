---
name: spatial-models
description: "Build Brian2 2.9.0 morphologies and multicompartment SpatialNeuron
  models, attach and index sections, load coordinate data safely, and inspect
  spatial state without confusing current densities with point currents."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Spatial models

Use this route when the task needs a neuronal morphology, a branched or
multicompartment `SpatialNeuron`, geometry-aware compartment state, or spatial
selection such as a soma, branch, distance interval, or morphology index.

## Route

1. Choose the geometry representation and validate its compartment count.
   Use `Soma`, `Cylinder`, and `Section` for small schematic models; use
   `Morphology.from_points` or `Morphology.from_file` for reconstructed
   coordinate data. Follow [morphology-workflows.md](references/morphology-workflows.md).
2. Attach sections only to a `Morphology` object, inspect `topology()`, and use
   `indices` or morphology slices to make selections. Read the API details in
   [api-reference.md](references/api-reference.md).
3. Create `SpatialNeuron` with a model containing one unflagged `Im` equation
   with units of `amp/meter**2`, and pass explicit, unit-bearing `Cm` and `Ri`
   values for a reproducible workflow. Brian2 2.9.0 supplies defaults for
   `Cm`/`Ri`, but this route treats them as required model inputs. Distinguish
   distributed surfacic current from an `amp` point current; see the current
   and unit checks in [troubleshooting.md](references/troubleshooting.md).
4. Initialize `v` and per-compartment parameters, then run a short bounded
   simulation. For spatial traces, use a recording tool such as
   `StateMonitor`; detailed monitor selection and analysis belong to the
   [recording](../recording/SKILL.md) route.
5. Check `area`, `distance`, `diameter`, `length`, `volume`, `space_constant`,
   and `time_constant` on the exact compartment or subgroup being interpreted.
   Remember that varying quantities are reported at compartment midpoints.

For a safe end-to-end smoke check, run:

```bash
python scripts/spatial_smoke.py --help
python scripts/spatial_smoke.py --constructor-only
python scripts/spatial_smoke.py
```

The script is intentionally tiny and CPU-oriented. `--constructor-only` checks
morphology, `Im`, explicit `Cm`/`Ri`, and derived geometry without SciPy; the
full invocation additionally requires the SciPy-backed NumPy diffusion path.
Neither mode replaces a backend-aware validation run, a Rallpack benchmark, or
an external morphology review.

## Scope boundaries

- Generic unit syntax, equation parsing, state updaters, and differential
  equation design route to [units-and-equations](../units-and-equations/SKILL.md).
- Monitor classes, recording schedules, and trace analysis route to
  [recording](../recording/SKILL.md) after this route supplies the spatial
  selection.
- Large Rallpack runs, external morphology repositories, native backends, and
  long simulations are explicit gaps: do not silently launch them from this
  route.

## Failure-first checks

- Missing `Im` is a construction error, not a default passive model. The
  constructor does not reliably reject an `Im` written with total-current
  dimensions, so validate that `Im` is `amp/meter**2` rather than assuming a
  failed constructor is the unit check.
- `Im` is a **current density**; a total current must be declared as
  `amp (point current)` so Brian2 divides it by `area`.
- Pass `Cm` as specific capacitance (`farad/meter**2`) and `Ri` as shared
  intracellular resistivity (`ohm*meter`) with explicit unit-bearing values;
  finalize `Ri` before the first run.
- A child section must be attached before the neuron is constructed. After
  construction, use the copied neuron morphology. `neuron.branch` includes a
  branch's descendants, while `neuron[morph.branch]` selects only that
  section's own compartments; do not mutate the source tree and expect the
  neuron to change.
- SWC/points input must be ordered parent-before-child and use seven fields;
  file input currently supports SWC only.
- If a NumPy-target spatial run reports missing SciPy, install/enable the
  required package in the active Brian2 environment or choose an explicitly
  supported backend; do not hide the dependency by changing equations.
