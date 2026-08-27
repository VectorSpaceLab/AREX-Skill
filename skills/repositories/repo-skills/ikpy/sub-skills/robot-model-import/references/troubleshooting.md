# Import troubleshooting

Diagnose model import in this order: filesystem path, XML well-formedness,
root/schema shape, selected traversal path, joint attributes and units, then
chain mask/vector shape. Keep a failing model in a minimal temporary fixture and
print names before attempting IK.

## Files and XML

### `FileNotFoundError`, permission errors, or an unexpected model

- Resolve the path before loading: `Path(path).expanduser().resolve()`.
- Check that the caller passed the model file, not a directory, archive, or
  simulator package descriptor.
- For JSON metadata, resolve `urdf_file` relative to the JSON file's directory;
  do not resolve it relative to the process current directory.
- Avoid shell-relative paths in long-running agents. Pass a stable absolute path
  selected by the caller, or generate a temporary fixture with
  `scripts/make_tiny_models.py`.
- Confirm the file is the intended version. IKPy does not inspect a model's
  package/mesh URI dependencies as part of these loaders.

### `xml.etree.ElementTree.ParseError`

This means the XML is not well formed, before IKPy has interpreted the robot.
Typical causes are an unclosed tag, an unescaped `&`, duplicate/invalid
quotation, or a truncated download. Read the line and column in the exception,
then validate with a standard XML parser. Do not try to fix it by changing
`base_elements`; traversal begins only after parsing succeeds.

A well-formed XML file can still be the wrong format:

- MJCF must have root tag `<mujoco>`; otherwise the parser raises
  `ValueError: Expected MJCF file (root element 'mujoco'), got ...`.
- MJCF requires `<worldbody>` and at least one descendant body. Missing
  `worldbody` or body raises an explicit `ValueError`.
- URDF loading does not perform a strict root-tag check. Use `<robot>` with
  direct root-level `<link>` and `<joint>` elements. Nested links/joints from a
  different XML dialect will not participate in the normal URDF traversal.

## URDF traversal failures

### `base_link` not found or no chain entries

`Chain.from_urdf_file` defaults to `base_elements=["base_link"]`. If the model
uses another root name, pass that exact link name. The name is case-sensitive.
Use `ikpy.urdf.utils` only after confirming the link exists; for tree inspection,
`get_urdf_tree(..., root_element=...)` raises `ValueError` when the root is
missing.

If the direct helper `URDF.get_urdf_parameters` is called with `None`, pass an
explicit list in IKPy 4.0.0. Its implementation attempts to copy
`base_elements` before its fallback branch, while `Chain.from_urdf_file` handles
its own omitted value. An empty list is also invalid for that helper:
`base_elements can't be the empty list []`.

### `Error: joint ... given but not found in the URDF`

The named item was expected to be a joint at the next alternating step, but no
root-level joint with that exact `name` exists. Check spelling and whether the
list starts with a link or joint. With `base_element_type="link"`, use
`[link, joint, link, ...]`; with `"joint"`, use `[joint, link, joint, ...]`.
`base_element_type` must be exactly one of those two strings.

### `Error: link ... given but not found in the URDF`

The named item was expected to be a child link but no root-level `<link>` has
that name. Check the alternating path and the joint's `<child link="...">`.
A source link name is not interchangeable with its joint name.

### The wrong branch is imported

When the explicit list ends, URDF traversal finds the first root-level child
joint/link in declaration order. A branching robot can therefore produce a
valid but unintended chain. Supply every link and joint name through the
intended tip. `get_chain_from_joints` can expand a joint-only list to
parent-link/joint pairs, but it does not prove that the selected joints form a
single connected route.

### Missing parent/child or malformed joint children

The parser assumes each traversed joint has `<parent link="...">` and
`<child link="...">`. If either is absent, an `AttributeError` may occur while
searching rather than a friendly validation error. Repair the XML or validate
that every joint has exactly one parent and child before loading.

### `Unknown joint type: ...`

This IKPy URDF parser accepts only `revolute`, `prismatic`, and `fixed`.
`continuous`, `planar`, and `floating` need an explicit conversion to a model
that expresses one supported degree of freedom, or they must be excluded from
the selected chain. Do not relabel a multi-DOF joint as revolute without
checking its axis and limits.

### `Joint type is 'revolute' ... rotation axis ...` or prismatic analogue

A revolute joint needs `<axis xyz="x y z">`; a prismatic joint also needs an
axis, which becomes its translation direction. Fixed joints must not provide a
rotation or translation axis. Ensure each axis has three numeric components and
is not accidentally placed on a different joint. Fixed-joint axes are ignored
with a warning, not used for motion.

### Unexpected length or end-effector offset

Remember the chain layout:

1. an `OriginLink` is prepended;
2. every parsed URDF joint becomes an IKPy `URDFLink`;
3. `last_link_vector` appends a fixed `last_joint`.

A tip offset changes both `len(chain.links)` and the required vector/mask length.
It is a translation in the parent frame, not another actuated joint. Validate
`len(values) == len(chain.links)` before FK/IK.

## MJCF traversal failures

### Missing `worldbody` or starting body

`MJCF.get_mjcf_parameters` requires a `<worldbody>` element and a body below
it. With no `base_elements`, it chooses the first direct worldbody body. With a
path, the first name is searched below `worldbody`; a missing first name raises
`Starting body '...' not found in MJCF`.

Later names are matched against direct children of the current body. A typo or
wrong nesting level can stop traversal early without raising. Always compare:

```python
from ikpy.mjcf import MJCF
print(MJCF.get_body_names("robot.xml"))
print(MJCF.get_joint_names("robot.xml"))
```

Then inspect `[(x.name, x.joint_type) for x in chain.links]` and make the body
path explicit. `base_elements=[]` behaves like an omitted path for MJCF; this
is different from the URDF helper, where an empty list is rejected.

### Wrong body/joint count

MJCF is hierarchical: a body with no joint contributes a fixed link, a body with
one joint contributes one mapped joint link, and multiple joints in one body
contribute multiple links sharing that body frame. Geoms and sites are not
IKPy chain links. A `site` named `tip` does not automatically become the
end-effector; use `last_link_vector` when a fixed offset is needed.

The default path follows the first child body, not all children. A branched
world must be narrowed with a body-name path.

### Joint type mapped to fixed

Mapping is intentional for `ball` and `free`, but those joints are warned and
then treated as fixed because they are not fully supported. Unknown MJCF types
fall back to fixed in this implementation. Check the resulting `joint_type`
and do not assume that a parsed element is actuated merely because it has a
`name`.

### Default class did not apply

A joint's explicit `class` or its enclosing body's `childclass` selects a
`<default class="...">` entry. Put the intended axis and range there, or make
critical attributes explicit on the joint. The supported default data is joint
`axis` and `range`; other MuJoCo defaults are not imported into IKPy. The
parser's implicit fallback is axis `[0, 1, 0]` and unbounded range.

Do not rely on unnamed top-level `<default><joint ...>` or deep inheritance as
if a full MuJoCo compiler were running. Verify the resulting `URDFLink.rotation`,
`translation`, and `bounds` after import.

## Degrees, radians, and orientation

### Ranges or poses are off by about 57.3

IKPy's revolute joint values and imported RPY orientations are radians. MJCF
has a different default: `_get_compiler_settings` uses `angle="degree"` unless
`<compiler angle="radian">` is present. In degree mode, an explicitly written
MJCF hinge `range` and body Euler/axis-angle angle are converted to radians;
slide ranges stay linear model units. A hinge range inherited from a default
class is copied as provided by this IKPy implementation, so verify
`link.bounds` or write the critical range directly on the joint. URDF `rpy`,
revolute limits, and FK/IK joint values are already expected in radians.

Do not convert a quaternion's components or `xyaxes`/`zaxis` values as degrees.
MJCF quaternions use `(w, x, y, z)`. If using helpers directly, pass
`axisangle_to_rpy(axis, angle)` and `euler_to_rpy(euler, sequence)` angles in
radians; the parser performs the compiler conversion before calling them.

### Euler orientation differs from a simulator

Check `<compiler eulerseq="...">` and the exact representation used by the
body (`quat`, `axisangle`, `euler`, `xyaxes`, or `zaxis`). IKPy converts these to
RPY using its own helper conventions. Compare a single body with
`ikpy.mjcf.utils` numerically before debugging the whole chain. Near gimbal lock,
multiple RPY triples may represent the same rotation; compare rotation matrices
rather than component-wise angles.

## Active masks, symbolic mode, and validation

### `active_links_mask` length mismatch

The mask must have one boolean per chain entry, including `OriginLink` and any
`last_joint`. A mask for only the actuated source joints is too short. Build it
from the imported chain:

```python
mask = [False] + [link.joint_type not in ("fixed",) for link in chain.links[1:]]
mask[-1] = False
```

For a mask passed to the loader, count the expected origin, parsed entries, and
tip offset first. Keep inactive values in every FK/IK input vector; use
`chain.active_to_full` and `chain.active_from_full` when converting optimizer
subvectors.

### `symbolic=True` import is slow or fails around SymPy

Symbolic mode is the default and prebuilds lambdified transforms while each
`URDFLink` is constructed. Ensure the base `sympy` dependency is installed.
For a diagnostic numeric import, pass `symbolic=False` to
`from_urdf_file`/`from_mjcf_file` or the lower-level parameter helper. This does
not change units or joint semantics. If later FK receives non-numeric objects,
fix the caller's input rather than changing model parsing.

### `forward_kinematics` rejects the vector

`Chain.forward_kinematics` requires `len(joints) == len(chain.links)`, even for
fixed or inactive links. A 4x4 FK matrix is returned by default; with
`full_kinematics=True`, a list of one 4x4 matrix per chain link is returned.
Route FK strategy and target setup to `chain-kinematics`, but use this shape
check to separate an import/layout error from a kinematics error.

## URDF tree and Graphviz

### `ImportError: graphviz` or render executable failure

`ikpy.urdf.utils.get_urdf_tree` imports the optional Python `graphviz` package.
Rendering also invokes the external `dot` executable. The model parser itself
does not require Graphviz. Install the `plot` extra only when tree rendering or
plotting is needed, check `dot -V`, and write output to an isolated caller-owned
path. If no renderer is available, use the returned names/children or the
no-write inspector instead. Route presentation/layout mechanics to
`visualization-geometry`.

## JSON metadata errors

- `KeyError`: add `urdf_file`, `elements`, `active_links_mask`,
  `last_link_vector`, and `name` with the expected JSON types.
- Wrong model loaded: the `urdf_file` value is relative to the JSON file, not
  the current shell directory.
- Unexpected defaults: JSON loading delegates to URDF loading with its default
  `base_element_type="link"` and `symbolic=True`; JSON cannot preserve those
  choices.
- Mask mismatch: update the JSON mask after changing `elements` or adding a
  `last_link_vector`.

Do not repair a malformed metadata file by pointing it at an unrelated large
robot. Generate a tiny model, reproduce the path and mask, then apply the same
change to the caller's model.
