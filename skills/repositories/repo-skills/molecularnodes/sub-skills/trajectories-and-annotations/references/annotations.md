# Annotations: dynamic manager, visibility, and lifecycle

This reference is for the annotation implementation in MolecularNodes 5.2.0. It
covers `MoleculeAnnotationManager`, the bundled molecule/trajectory annotations,
and custom `MoleculeAnnotation` subclasses. It does not replace Blender's
context requirements: annotation creation and viewport drawing are Blender-host
operations.

## Dynamic `add_*` contract

A `MoleculeAnnotation` subclass is registered by
`MoleculeAnnotation.__init_subclass__`. Registration is performed by
`MoleculeAnnotationManager.register_class()` and has these effects:

1. The class is checked to be a `BaseAnnotation` subclass, to define a unique
   `annotation_type`, and to override `draw()`.
2. The class is added to the manager registry and a method named
   `add_<annotation_type>` is attached to the manager class.
3. The method signature is generated from annotations collected through the
   class MRO. Annotation inputs, including common `name`, are keyword-only.
   Class attributes provide defaults; an annotated input without a class default
   is required.
4. Blender property types for the annotation are registered dynamically. The
   returned value from `add_<annotation_type>(...)` is a dynamic
   `AnnotationInterface`, not the raw annotation instance.

For example, the bundled trajectory manager exposes methods including
`add_atom_info`, `add_com`, `add_com_distance`,
`add_canonical_dihedrals`, `add_universe_info`, `add_simulation_box`,
`add_label_2d`, and `add_label_3d` (plus `add_molecule_info` for the molecule
annotation class). Inspect the installed manager rather than hard-coding a
future registry:

```python
manager = mol.annotations
available = [name for name in dir(manager) if name.startswith("add_")]
annotation = manager.add_com(selection="protein", name="Protein COM")
annotation.text = "Protein|COM"
```

Creation validates required and unknown keyword inputs before the interface is
committed to the Blender collection. Annotation-specific `validate()` is also
called during creation when present; an exception or false result prevents a
valid instance from being created. Keep the returned interface if inputs will
be edited later. The manager supports name lookup, integer index lookup, and
iteration:

```python
manager["Protein COM"]
manager[0]
list(manager)
manager.remove("Protein COM")  # removes every matching name
manager.clear()                 # removes all instances
```

`remove()` raises for an unknown name or an object that is not an
`AnnotationInterface`; integer indexing raises for an invalid index. Annotation
names are labels stored with the object; if no `name` is passed, the manager
creates labels such as `Annotation` and then increments its next-index state.

## Inputs and selections

Bundled selection inputs accept either an MDAnalysis selection string or an
`MDAnalysis.AtomGroup`, depending on the annotation. Strings are resolved by
`Universe.select_atoms()` with the annotation's `periodic` and `updating`
values. A syntactically valid selection can still contain zero atoms. That is
not automatically converted into a useful COM, distance, or atom label; check
atom counts before relying on a drawn result.

For `AtomGroup` values, validation retains the group in the running Python
annotation instance. A Blender property representation exists for persistence
and UI purposes, but it is not a guarantee that an arbitrary Python
`AtomGroup` object will be reconstructed after a session round trip. Prefer a
re-creatable selection string when the annotation must survive save/reload, or
rebuild the group after reload.

An invalid input changed through the interface is handled by the property
callback: the input is validated, its error is recorded on the annotation
instance, and the exception is propagated to the caller. During drawing, an
annotation with `_invalid_inputs` is skipped. Repair the input and confirm that
validation succeeds; do not treat a hidden annotation as a successful result.

## Visibility and draw eligibility

There are two visibility controls:

```python
annotation.visible = False  # one annotation
mol.annotations.visible = False  # all annotations for this entity
```

`mol.annotations.visible` maps to the entity object's
`mn.annotations_visible` property. Setting it also tags Blender viewports for
redraw. The per-annotation `visible` property is stored in the object's
`mn_annotations` collection. For an annotation to draw, all of the following
must be true:

- the manager is visible;
- the entity object is visible and belongs to the current scene;
- the individual annotation is visible;
- its inputs are not marked invalid; and
- a valid Blender drawing context is available.

The manager records exceptions raised by `draw()` in the instance's
`_draw_error` and continues with other annotations. `_draw_error` is diagnostic;
it is not a successful render assertion. A non-empty `_draw_error` or skipped
invalid input should be investigated explicitly.

A manager installs a `SpaceView3D` draw handler when created unless Blender is
running in background mode. The handler uses a captured Blender context and
requires a usable viewport region and `RegionView3D`; otherwise it returns
without drawing. Creating an annotation does not promise visible output in a
headless/background process, an absent VIEW_3D region, a hidden object, or an
object not linked to the current scene.

## Simulation box annotation

`add_simulation_box()` creates a live annotation whose `draw()` reads the
current `u.trajectory.ts.dimensions` on every annotation-object update. The
six-value MDAnalysis form is `(a, b, c, alpha, beta, gamma)`.

```python
box = mol.annotations.add_simulation_box(
    center_to_origin=False,
    compact=False,
    show_lattice=False,
    name="Cell",
)
```

Defaults set a wireframe mesh, thickness `5.0`, and flat shading. With
`compact=False`, the annotation draws a regular triclinic cell. With
`compact=True`, it calls the Wigner-Seitz-cell path using
`ts.triclinic_dimensions`; the trajectory coordinates must be wrapped in a way
that makes the compact cell meaningful. `show_lattice=True` requests the
3-by-3-by-3 lattice variant. `center_to_origin=True` shifts the regular-cell
origin by half the sum of the triclinic vectors.

If the current timestep has no dimensions, `draw()` emits no box geometry. It
does not invent a unit cell and it does not wrap or otherwise transform atom
coordinates. The annotation follows the current timestep when a normal
trajectory frame update calls `Molecule.set_frame()`; it is not a substitute
for periodic-position correction.

## Custom annotation lifecycle

A minimal custom class must derive from `MoleculeAnnotation`, set a unique
`annotation_type`, and implement `draw()`:

```python
from molecularnodes.entities.molecule.annotations import MoleculeAnnotation

class MyAnnotation(MoleculeAnnotation):
    annotation_type = "my_annotation"
    selection: str

    def validate(self, input_name=None):
        self.atom_group = self.trajectory.universe.select_atoms(
            self.interface.selection
        )
        return True

    def defaults(self):
        self.interface.text_size = 16

    def draw(self):
        for atom in self.atom_group:
            self.draw_text_3d(atom.position, atom.name)
```

Defining the subclass auto-registers `add_my_annotation`. Registration is
process-wide for the molecule annotation manager, so the `annotation_type` must
not collide with an existing type. `unregister_type("my_annotation")` removes
the registry entry and dynamic `add_my_annotation` method; it does not serve as
a safe migration for already-persisted instances. Re-register the class before
restoring objects that need it.

The lifecycle is:

1. `add_*` validates required/unknown inputs and constructs the Python instance
   and dynamic interface.
2. `validate(None)` runs, if defined, after supplied annotation inputs have been
   placed on the interface.
3. `defaults()` runs once after input/common-property interfaces are built.
4. Later interface or Blender-property changes call `validate(input_name)` for
   annotation inputs. A successful ready instance triggers an annotation-object
   update.
5. `draw()` runs repeatedly in the viewport draw path and when geometry or
   render annotation output is assembled.

Use `defaults()` for one-time setup and `validate()` for cheap input checking or
rebuilding cached selections/analyses. Do not write the property being
validated from `validate()`; the source explicitly warns that this recurses.
Keep `draw()` limited to lightweight drawing from already-prepared state. Do
not load files, run expensive analyses, mutate Blender data, or depend on
operator context from `draw()`.

The manager has two draw modes. In normal viewport/render-overlay mode,
`draw_text_2d()` and `draw_line_2d()` can emit 2D overlay output. When the
manager is collecting 3D mesh geometry (`get_geometry=True`), those 2D helpers
return without drawing; use the 3D drawing helpers for mesh geometry. A custom
`draw()` exception is isolated and recorded as `_draw_error`, so test the
instance's diagnostic state rather than assuming the add call proved drawing.

After a `.blend` load, the manager reconstructs instances from the object's
`mn_annotations` properties. If a custom annotation class is not registered,
that property entry is removed because the manager cannot instantiate the
missing class. Keep custom class definitions importable and registered before
recovery if those annotations matter.

## Evidence consulted

- `molecularnodes/annotations/manager.py`
- `molecularnodes/annotations/base.py`
- `molecularnodes/annotations/interface.py`
- `molecularnodes/annotations/props.py`
- `molecularnodes/annotations/utils.py`
- `molecularnodes/entities/molecule/annotations.py`
- `docs/api/annotations.qmd`
- `docs/api/blender.qmd`
- `tests/test_annotations.py` (read only; native tests were not run)
