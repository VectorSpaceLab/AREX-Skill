# Spatial-model API reference

This reference describes the Brian2 2.9.0 public spatial-model API. Import
these names from `brian2`:

```python
from brian2 import Cylinder, Morphology, Section, Soma, SpatialNeuron
```

## Morphology classes

### `Soma(diameter, x=None, y=None, z=None, type="soma")`

Creates exactly one iso-potential compartment. `diameter` is a scalar length;
its surface area is the sphere area `pi * diameter**2`, its volume is
`pi * diameter**3 / 6`, and its morphology `length` is the diameter. Optional
coordinates are scalar values. A soma has effectively negligible axial
resistance to its center for the cable solver.

### `Cylinder(diameter, n=1, length=None, x=None, y=None, z=None, type=None)`

Creates `n` equal-diameter compartments. With `length`, the value is the total
section length and each compartment receives `length/n`; with coordinates,
provide a two-point start/end sequence for at least one of `x`, `y`, or `z`,
and lengths are derived from the Euclidean distances. Do not pass coordinates
and `length` together. Coordinates not supplied are treated as zero. A
cylinder's lateral compartment area is `pi * diameter * compartment_length`.

### `Section(diameter, n=1, length=None, x=None, y=None, z=None, type=None)`

Creates `n` unbranched truncated-cone compartments. `diameter` must be a
one-dimensional sequence of `n+1` node diameters. `length` must be a
one-dimensional sequence of `n` compartment lengths, or a coordinate mode must
provide at least one of `x`, `y`, and `z` as an `n+1` sequence. Coordinate mode
and length mode are mutually exclusive.

For a section, `start_diameter` and `end_diameter` are the node values for
each compartment, while `diameter` is their midpoint average. Lateral surface
area and volume account for tapering. Coordinates supplied to a child section
are relative to the end of its parent; midpoint coordinate properties are
computed after this translation.

## Attachment, names, and topology

A morphology is a tree. Attach a child with either attribute or item syntax:

```python
morph = Soma(20 * um)
morph.axon = Cylinder(diameter=1 * um, length=40 * um, n=4)
morph["dendrite"] = Section(
    diameter=[2, 1.8, 1.5] * um,
    length=[10, 15] * um,
    n=2,
)
morph.dendrite.branch = Cylinder(diameter=0.8 * um, length=20 * um, n=2)
```

Names are user-defined. Single-character/number names made from `L`, `R`, and
`1`-`9` support compact navigation (`morph.LR` means `morph.L.R`), but names
that themselves look like a compact path can be ambiguous. Prefer descriptive
names when compact navigation is not needed. `children`, `parent`, `n`,
`total_sections`, and `total_compartments` expose the tree size. `str(morph.topology())`
is the quickest structural check.

A child's first coordinate is normally `[0, ...]` so it continues from the
parent endpoint. To visually connect a child cylinder to a spherical soma,
use a nonzero start coordinate only when that visual offset is intentional;
coordinates do not alter the electrical cable geometry beyond the lengths they
imply.

## Geometry, indexing, and views

Every section provides per-compartment `length`, `diameter`, `area`, `volume`,
`distance`, `r_length_1`, and `r_length_2`. With coordinates it also provides
`start_x/y/z`, midpoint `x/y/z`, and `end_x/y/z`; without coordinates those
properties are `None`. Values that vary across a compartment represent its
midpoint. For a soma, distance is zero at the root. Child distances continue
from the parent's endpoint.

Use these selection forms on a morphology:

```python
morph.axon[2]                 # one compartment
morph.axon[2:4]               # contiguous integer view
morph.axon[10 * um : 30 * um] # contiguous distance view
morph.axon.indices[:]         # absolute flattened indices
morph["axon"]                # named subtree
```

Integer slices must be contiguous and unit slices cannot have a step. A length
index must have length units and an integer index must be integral. Single
out-of-range indices raise `IndexError`; slice bounds use Brian2's clipping and
search behavior, so validate the resulting `indices[:]` rather than assuming a
slice failed. Bad units, mixed slice modes, and non-contiguous integer steps
raise `TypeError`. `morph.axon.indices` reports absolute indices in the
flattened tree, not indices starting at zero within the branch.

## Reconstructed morphologies

`Morphology.from_points(points, spherical_soma=True)` consumes seven-value
records `(index, type, x, y, z, diameter, parent)`. Values are unitless and
interpreted as micrometers; the sixth value is a **diameter**, not a radius.
The first record must be the root with parent `-1`, and every parent must have
already appeared. Duplicate indices, self-parents, missing parents, records
with the wrong field count, and a non-root first record are rejected.

`Morphology.from_swc_file(filename, spherical_soma=True)` and
`Morphology.from_file(filename, spherical_soma=True)` parse SWC text. Blank and
`#` comment lines are ignored. Each data line is
`index type x y z radius parent`; the parser doubles radius to form diameter.
SWC type 1 is treated as soma; types 2, 3, and 4 are named axon, dendrite, and
apical dendrite respectively; other types do not change the section type.
`from_file` currently supports the `.swc` extension only.

With `spherical_soma=True`, a valid three-point soma can be collapsed into one
spherical soma. Inconsistent soma diameters or geometry produce a validation
error. Set it to `False` when the input should remain cylindrical rather than
being normalized to a sphere.

`generate_coordinates(section_randomness=0, compartment_randomness=0,
overwrite_existing=False)` returns a morphology copy with missing coordinates
filled deterministically by default. Randomness values are angle scales in
degrees. Existing coordinates are preserved unless overwrite is requested.
This is useful for visualization and coordinate-aware recording; inspect the
result rather than assuming the original object was mutated.

## `SpatialNeuron`

The essential constructor is:

```python
neuron = SpatialNeuron(
    morphology=morph,
    model=eqs,
    Cm=1 * uF / cm**2,
    Ri=150 * ohm * cm,
    method="exponential_euler",
)
```

`morphology` is flattened into `morphology.total_compartments` compartments.
Brian2 2.9.0 has defaults for `Cm` and `Ri`, but pass both explicitly here so
that the model contract is visible and reproducible. `Cm` is a per-compartment
specific-capacitance variable initialized from the constructor value and can be
assigned per compartment as supported by the group API. `Ri` is a uniform
shared intracellular resistivity and must be finalized before the first run.
`v` is the membrane potential. Geometry state includes `length`, `diameter`,
`area`, `volume`, `distance`, `r_length_1`, and `r_length_2`; `x`, `y`, and `z`
are available when any morphology coordinates exist. For a partially
coordinate-free tree, missing coordinates are represented as NaN in the
neuron; call `generate_coordinates` before construction when complete
coordinates are required.

### Equation contract

The model must contain exactly an unflagged membrane equation named `Im` with
units of `amp/meter**2`:

```python
eqs = """
Im = gL * (EL - v) : amp/meter**2
I : amp (point current)
"""
```

`Im` is a surfacic (current-density) equation. Brian2 combines it with axial
diffusion calculated from morphology and `Ri`. A scalar total current belongs
in a parameter or subexpression with units `amp (point current)`; the flag
causes Brian2 to add `I/area` to `Im`. Do not put a total `amp` expression in
`Im`, and do not label a current density as a point current. Brian2 requires
that `Im` be present and unflagged, but a wrongly dimensioned `Im` can pass the
constructor; treat `amp/meter**2` as a model invariant and check it explicitly.

The remaining equations follow ordinary group rules: state variables,
parameters, subexpressions, and supported flags may be used subject to unit
consistency. This route does not replace the generic equations route.

### Spatial subgroups and sections

Attribute access on a neuron follows morphology names. `neuron.axon` denotes
the full axon subtree, including descendants; `neuron.axon.main` denotes only
the axon section. `neuron[0]`, `neuron[:3]`, and distance slices select
contiguous flattened compartments. Prefer morphology-derived selections for
branches:

```python
axon_main = neuron[morph.axon]
distal = neuron[morph.axon[20 * um : 40 * um]]
neuron.axon.main.v = -65 * mV
neuron.dendrite.gL = 2 * gL       # branch and all descendants
# Use neuron.axon, not neuron[morph.axon], for the full subtree.
```

A subtree's flattened indices occupy one interval, but
`morph.axon.indices[:]` contains only the named section's own compartments;
its descendants are not included. Use `neuron.axon` for the full subtree, or
`neuron[morph.axon]`/`neuron[morph.axon.indices[:]]` for the main section only.
Use `.main` to make section-only attribute assignments explicit. Do not
assume that `.axon` assignments affect only the named section.

### Spatial constants and current diagnostics

`neuron.space_constant[i]` and `neuron.time_constant[i]` are local derived
values. The conductance used is the local total conductance obtained from
`Im`, not only the leak conductance. The cylindrical approximation is most
meaningful for approximately cylindrical compartments and can be misleading
for strongly tapering or soma compartments. Compare `Im`, `Ic`, `area`, and
point-current values only after converting them to compatible density or total
units; a useful global conservation diagnostic is a sum of density differences
weighted by compartment area, not an unweighted sum of unlike quantities.

## Evidence basis

This reference is grounded in Brian2 2.9.0's public multicompartmental user
chapter and the public `Morphology`/`SpatialNeuron` API docstrings, cross-checked
against the focused morphology and spatial-neuron tests. It intentionally does
not claim validation of large morphology data or Rallpack benchmarks.
