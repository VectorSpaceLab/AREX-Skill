# Morphology and SpatialNeuron workflows

## 1. Pick a representation

Use the smallest representation that preserves the evidence needed by the
model:

- **Soma + Cylinder:** a spherical root and equal-diameter cables. `n` is the
  number of compartments and `length` is the total section length.
- **Section:** a tapering or irregular unbranched cable. Pass `n+1` node
  diameters and `n` lengths, or pass `n+1` coordinate nodes and let Brian2
  calculate the lengths.
- **Points/SWC:** a reconstructed tree with coordinates. Validate and inspect
  the resulting tree before constructing a neuron.

Start with `n=1` or a few compartments while debugging equations, then refine
only after the short model runs. A very fine mesh increases flattened state
size and diffusion-solver work; there is no universal safe compartment limit,
so budget from `total_compartments`, memory, the spatial scale of the channels,
and the desired time step. Do not use a large morphology or Rallpack as a smoke
check.

## 2. Build and inspect a branched schematic tree

```python
from brian2 import *

morph = Soma(diameter=20 * um)
morph.axon = Cylinder(diameter=1 * um, length=40 * um, n=4)
morph.dend = Section(
    diameter=[3, 2.5, 2, 1.5] * um,
    length=[10, 12, 15] * um,
    n=3,
)
morph.dend.left = Cylinder(diameter=1 * um, length=15 * um, n=2)
morph.dend.right = Cylinder(diameter=0.8 * um, length=20 * um, n=2)

print(morph.topology())
assert morph.total_compartments == 1 + 4 + 3 + 2 + 2
```

Attachment is tree construction: `morph.dend.left = child` and
`morph["dend"]["left"] = child` are equivalent. Attach all sections before
passing the root to `SpatialNeuron`. The neuron stores a copy of the
morphology; later changes to the source tree do not retroactively add
compartments to an existing neuron.

Use `total_sections` and `total_compartments` before allocation. For every
branch, check the intended parent, `n`, `start_diameter`, `end_diameter`,
`distance`, and `indices[:]`. `topology()` is a human-readable check that the
branch names and nesting are as expected.

## 3. Coordinates and generated coordinates

Length mode and coordinate mode are mutually exclusive. In coordinate mode,
`Cylinder` receives two endpoints and `Section` receives `n+1` nodes. Child
coordinates are relative to the parent's endpoint. Unspecified coordinate
axes are zero. The coordinate arrays are geometric metadata; they are not
used in the cable equations except through the lengths computed from them.

For a schematic tree that needs plotting or coordinate-based selection, use:

```python
with_coords = morph.generate_coordinates()
```

The default deterministic algorithm is adequate for a stable smoke fixture.
Use nonzero `section_randomness` or `compartment_randomness` only when a
controlled random geometry is actually desired. Existing coordinates are
preserved by default. If the tree mixes coordinate-bearing and coordinate-free
sections, call `generate_coordinates` before constructing the neuron when
complete `x/y/z` state is required; otherwise missing coordinates become NaN.

## 4. Load points or SWC defensively

For an in-memory reconstruction:

```python
points = [
    (1, "soma", 0, 0, 0, 20, -1),
    (2, "dend", 10, 0, 0, 4, 1),
    (3, "dend", 20, 0, 0, 3, 2),
    (4, "dend", 10, 8, 0, 3, 1),
]
morph = Morphology.from_points(points)
```

Each record has seven values `(index, type, x, y, z, diameter, parent)` and
coordinates/diameters are interpreted as micrometers without unit wrappers.
The root record must come first with parent `-1`; parents must precede children.
The sixth field is diameter. The library rejects duplicate IDs, self-parenting,
missing parents, malformed records, and invalid roots.

For a file:

```python
morph = Morphology.from_file("cell.swc")
```

SWC data lines are `index type x y z radius parent`; comments and blank lines
are ignored and radius is doubled. Only the `.swc` format is currently
supported by `from_file`. Validate path existence, extension, line count, and
field count before a long run. If the soma is encoded as three points, the
default spherical normalization requires equal diameters and approximately
radius-length geometry; set `spherical_soma=False` when that normalization is
not appropriate.

After loading, inspect:

```python
print(morph.topology())
print(morph.total_sections, morph.total_compartments)
print(morph.x is None, morph.distance[-1])
```

Do not infer a biologically meaningful section name from arbitrary SWC type
values. The standard mappings are type 1 `soma`, 2 `axon`, 3 `dend`, and 4
`apic`; other types do not receive a special name.

## 5. Construct and initialize a passive SpatialNeuron

```python
EL = -70 * mV
gL = 1e-4 * siemens / cm**2
eqs = """
Im = gL * (EL - v) : amp/meter**2
I : amp (point current)
"""
neuron = SpatialNeuron(
    morphology=morph,
    model=eqs,
    Cm=1 * uF / cm**2,
    Ri=150 * ohm * cm,
    method="exponential_euler",
)
neuron.v = EL
neuron.I[0] = 0.02 * nA
```

Keep `Im` as a density. Point injection is total `amp` and is converted by
`I/area`; a distributed leak or channel remains `amp/meter**2`. Pass `Cm` and
`Ri` explicitly even though Brian2 supplies defaults: `Cm` is specific
capacitance and can be assigned per compartment as supported by the group API;
`Ri` is uniform and should be finalized before the first run. The constructor
also creates `area`, `length`, `diameter`, `volume`, `distance`, `Cm`, `Ri`,
`space_constant`, and `time_constant` state/derived variables.

A short diagnostic simulation can record soma and branch endpoints:

```python
soma_i = 0
axon_i = morph.axon.indices[-1]
dend_i = morph.dend.right.indices[-1]
mon = StateMonitor(neuron, "v", record=[soma_i, axon_i, dend_i])
run(0.5 * ms)
```

Use a dedicated recording workflow for monitor scheduling and analysis. This
route only owns selection correctness and spatial-state interpretation.

## 6. Branch assignment and distal recording

Attribute selection on a neuron includes descendants. Use `.main` to isolate a
section:

```python
neuron.dend.gbar = 2 * gL             # dend and all descendants
neuron.dend.main.gbar = 2 * gL         # dend's own compartments only
neuron.dend.main.v = EL + 1 * mV       # section-only voltage assignment
neuron[morph.axon].v = EL + 1 * mV     # same section-only selection
# Use neuron.axon.v when the assignment should include axon descendants.
```

For a branched morphology, a robust synthetic check is to record `v` at index 0,
the last compartment of one branch, and the last compartment of another. Set
an initial distal voltage or inject at the soma and confirm the branches are
not accidentally aliased. Use `morphology.indices` rather than hand-counting
flattened indices when the tree changes.

Distance slices are section-relative when taken from a morphology branch. A
subgroup created from a whole neuron must still be contiguous for integer or
distance slicing. For a complete subtree with descendants, select it using
`neuron.branch`; `neuron[morph.branch]` selects only the named section's own
compartments even though the complete subtree occupies one flattened interval.

## 7. Spatial and temporal scale checks

`space_constant` is derived from the local total conductance and geometry;
`time_constant` is `Cm/total_conductance`. These values can change when channel
conductances or voltage-dependent state changes change `Im`. The approximation
is most reliable for cylindrical compartments. Treat values for a soma or
strongly tapering section as diagnostics, not exact cable-theory constants.

Before refining a model:

1. Compare compartment length with the local space constant.
2. Check that branch and soma areas are plausible and positive.
3. Check that the chosen `dt` resolves the fastest time constant and channel
   kinetics.
4. Increase `n` only if spatial convergence is part of the experiment.
5. Compare a distal voltage trace and total injected current after converting
   current densities using compartment area.

## Evidence basis

The workflow is based on Brian2 2.9.0's public multicompartmental user
chapter and the morphology/spatial-neuron API implementation, with topology,
coordinate, and selection details cross-checked against focused native tests.
Large morphologies, Rallpack, and external-data pipelines remain unverified.
