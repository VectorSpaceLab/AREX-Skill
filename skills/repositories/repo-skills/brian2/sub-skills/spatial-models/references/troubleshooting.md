# Spatial-model troubleshooting

Use the smallest failing morphology and a short CPU run to isolate failures.
Keep the original input, selected indices, units, and Brian2 version in the
working notes. Do not “fix” a spatial error by removing units or by silently
reducing a morphology that the scientific result requires.

## Install and import

**Symptoms:** `ImportError` during `import brian2`, a missing compiled dynamic
array, or a spatial class that cannot be imported.

**Checks:**

1. Confirm the active interpreter is Python 3.12 or newer and that the imported
   package reports Brian2 2.9.0.
2. Confirm the package's normal runtime dependencies are installed, including
   the compiled components required by the installed distribution.
3. Run `python scripts/spatial_smoke.py --help` first; this checks the script
   parser without importing Brian2. Then run
   `python scripts/spatial_smoke.py --constructor-only` for a bounded
   constructor/geometry check before attempting the SciPy-backed simulation in
   the same environment.
4. If import fails, repair/reinstall Brian2 in the active environment using
   the environment's package manager. Do not mix a source checkout with a
   different installed version, and do not proceed to interpret spatial traces
   until import is clean.

A development tree may lack generated extensions even when the package
version is correct. Treat that as an environment block rather than editing
spatial code.

## Optional dependency: SciPy

**Symptoms:** a NumPy-target spatial run is skipped or fails because SciPy is
not available; a solver operation complains about a SciPy routine.

**Checks and recovery:**

- Probe `import scipy` in the same environment used for Brian2.
- Spatial diffusion with the NumPy runtime has a SciPy dependency in the
  supported test configuration. Install/enable a compatible SciPy package in
  the active environment, or use a backend whose documented runtime includes
  the required solver support.
- Do not interpret “Brian2 imports” as proof that a spatial simulation can run;
  import and execution are separate gates.
- Keep a SciPy-dependent test explicitly marked/skipped when the environment
  cannot provide SciPy. Do not launch a large fallback run.

## Missing `Im` or incorrect surfacic-current units

**Symptoms:** construction raises that transmembrane current `Im` must be
defined; dimension mismatch reports `amp` versus `amp/meter**2`; a point
injection changes voltage by an area-dependent amount unexpectedly.

**Checks:**

- Define one unflagged line named exactly `Im` with result units
  `amp/meter**2`:

  ```text
  Im = gL * (EL - v) : amp/meter**2
  ```

- Pass explicit `Cm` (`farad/meter**2`) and `Ri` (`ohm*meter`) values to
  `SpatialNeuron` for reproducibility. Brian2 provides defaults, but this
  route's model contract requires those inputs; `Ri` is shared and must be
  finalized before the first run.
- Treat leak/channel expressions in `Im` as current densities. A conductance
  density times a voltage is a density.
- Declare an electrode or synaptic total current as `amp (point current)`:

  ```text
  Iinj : amp (point current)
  ```

  Brian2 adds `Iinj/area` to `Im` automatically.
- Do not declare `Im : amp`, do not add an `amp` point-current expression to
  `Im` without dividing by `area`, and do not put a density under the point
  current flag. Brian2 2.9.0 may accept a wrongly dimensioned `Im` at
  construction, so a successful constructor is not proof of this invariant.
- Debug total versus density explicitly:

  ```python
  total_from_density = neuron.Im * neuron.area
  ```

  Compare `total_from_density` with a total point current only after selecting
  the same compartment and sign convention. Summing an unweighted density over
  compartments is dimensionally wrong.

A missing `Im` is never repaired by relying on a default leak. Add the equation
and then re-run the constructor-only check before running the network.

## Morphology attachment, topology, or indexing errors

**Symptoms:** an attribute lookup says a section does not exist; a branch has
unexpected descendants; a selected index points into another branch; a slice
raises `TypeError` or `IndexError`.

**Checks:**

1. Build the root and attach every child before creating `SpatialNeuron`.
2. Print `str(morph.topology())`, `morph.total_sections`, and
   `morph.total_compartments`.
3. Check `morph.branch.parent`, `morph.branch.n`, and
   `morph.branch.indices[:]`. Remember that indices are absolute in the
   flattened tree.
4. Use `.main` for only the named section; `neuron.branch` includes all
   descendants.
5. Use either integral indices or length-valued slices, not a mixture. Slices
   must be contiguous and cannot specify a step. Use `neuron.branch` for a
   full subtree selection; `neuron[morph.branch]` selects only the named
   section's own compartments.
6. Recreate the neuron after changing the source morphology. The neuron keeps
   a copy and does not gain newly attached sections.

For a branch recording bug, record the root, one distal compartment per branch,
and their `morphology.indices` values. If two branches share an index, the
construction or selection is wrong before any numerical interpretation.

## SWC and points path/data validation

**Symptoms:** file-not-found, unsupported extension, malformed-line, missing
parent, duplicate-index, self-parent, or three-point-soma geometry errors.

**Checks and recovery:**

- Validate the path and `.swc` extension before calling `from_file`; currently
  SWC is the supported file format.
- Remove only comments/blank lines from the mental model: every data line must
  have seven whitespace-separated fields.
- SWC fields are `index type x y z radius parent`; Brian2 converts radius to
  diameter. `from_points` instead expects
  `(index, type, x, y, z, diameter, parent)` and interprets numeric geometry as
  micrometers.
- Ensure the first point is the root with parent `-1`, and list every parent
  before its children. IDs must be unique and a point cannot parent itself.
- Print the loaded topology and counts. Check for NaN coordinates and
  implausible diameters before allocating a neuron.
- A three-point soma is collapsed only when its diameters and geometry satisfy
  the spherical-soma checks. Use `spherical_soma=False` for a deliberate
  non-spherical interpretation; do not alter source data merely to suppress a
  validation error.

For an external morphology, retain the source provenance and processing choices
outside this skill. Large databases or full external morphology pipelines are
out of scope for a tiny smoke run.

## Too many compartments or unstable spatial execution

**Symptoms:** construction consumes unexpected memory, the run becomes very
slow, or the diffusion solver fails after a morphology was refined.

**Checks:**

- Compute `morph.total_compartments` before constructing the neuron. A tree's
  total is the sum of every section, not just `morph.n`.
- Reduce a diagnostic fixture to a soma plus one or two short branches and a
  few compartments. Keep the scientifically required mesh for the real run;
  do not claim the reduced fixture validates convergence.
- Compare each compartment length to its local `space_constant`; refine based
  on spatial convergence rather than a guessed universal threshold.
- Check `dt` against the fastest `time_constant` and channel kinetics. A small
  `dt` with thousands of compartments can be expensive; a large `dt` can hide
  diffusion or gating errors.
- If a reconstructed tree has accidental duplicate/zero-length points, fix the
  input data and re-check lengths before blaming the solver.
- Use only short, bounded CPU smoke runs here. Rallpack, long cables, external
  data downloads, and native standalone benchmarks are explicit gap work.

## Coordinate and geometry surprises

**Symptoms:** lengths differ from expected values; coordinates are `None` or
NaN; branches appear visually disconnected; a spatial constant seems
unreasonable.

**Checks:**

- Length mode and coordinate mode cannot be combined.
- Coordinate endpoints/nodes are relative to the parent endpoint. A missing
  axis is zero, and coordinate properties exposed on compartments are midpoint
  values.
- A soma is modeled electrically as one spherical compartment and as a point
  for distance continuation; a child starts at the parent's endpoint for
  distance calculations.
- `generate_coordinates()` returns a morphology with filled coordinates; use
  the returned object. It does not silently make an existing neuron acquire
  coordinate state.
- `space_constant` and `time_constant` use local total conductance and are
  approximate for strongly tapering or spherical geometry. Check area and
  conductance units before comparing them with cylindrical theory.

## Data and configuration mismatches

**Symptoms:** a morphology has an unexpected size, coordinates are incomplete,
`Cm`/`Ri` produce implausible scales, or changing `n` changes the result for a
reason that is not spatial convergence.

**Checks:**

- Log the Brian2 version, active code-generation target, `dt`, `Cm`, `Ri`,
  `morph.total_sections`, and `morph.total_compartments` alongside the model.
- Confirm that `n` is the number of compartments in one section, while
  `total_compartments` includes every attached descendant. Do not compare two
  meshes without holding physical lengths, diameters, units, and solver choice
  fixed.
- Confirm that `Cm` is a specific capacitance and that `Ri` is a shared
  resistivity. Per-compartment `Cm` changes are state assignments; `Ri` is not
  a per-compartment morphology parameter.
- Keep coordinate-bearing and length-bearing construction choices explicit.
  Coordinate mode derives lengths, so a changed endpoint can change the cable
  even when `n` is unchanged.
- If a preference or backend change is involved, reproduce the tiny passive
  fixture first and route target/compiler configuration issues to the
  configuration/code-generation owner rather than changing the morphology to
  mask them.

## Workflow failures

**Symptoms:** a script runs but records the wrong branch, a model changes after
morphology edits, or a result cannot be reproduced.

**Recovery sequence:**

1. Freeze the Brian2 version, backend, `dt`, `Cm`, `Ri`, morphology counts, and
   equation text.
2. Run the constructor-only checks: topology, counts, branch indices, units,
   and `Im` presence.
3. Run a short passive model with `v=EL`, one bounded point injection, and
   three explicit recording indices (soma, branch A distal, branch B distal).
4. Verify selected state arrays and midpoint geometry before plotting or
   aggregating.
5. Only then hand monitor scheduling and trace analysis to the recording route.

Do not combine an import repair, a morphology rewrite, and an equation rewrite
in one debugging step. A clear failure category is more valuable than a
long-running simulation with uncertain inputs.

## Evidence basis

This guide was cross-checked against Brian2 2.9.0's public multicompartmental
user chapter, API docstrings, and focused morphology/spatial-neuron tests. A
missing optional dependency remains an environment gate; do not claim a
completed spatial simulation until the selected runtime path has executed.
