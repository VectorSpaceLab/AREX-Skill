# Model-import API reference

This reference describes the public import surface in IKPy 4.0.0. Importing a
model creates a `Chain`; it does not validate meshes, simulator assets, or the
physical correctness of the robot. Validate the XML and the resulting chain
names/types before using FK or IK.

## Loader selection

```python
from ikpy.chain import Chain

urdf_chain = Chain.from_urdf_file(
    "robot.urdf",
    base_elements=["base_link"],
    last_link_vector=[0.0, 0.0, 0.1],
    active_links_mask=[False, True, False],
    symbolic=True,
)
mjcf_chain = Chain.from_mjcf_file("robot.xml", base_elements=["base"])
json_chain = Chain.from_json_file("saved_chain.json")
```

| Loader | Path argument | Path unit | Important defaults |
|---|---|---|---|
| `Chain.from_urdf_file` | `urdf_file` | filesystem path | `base_elements=None` is converted by `Chain` to `["base_link"]`; `base_element_type="link"`, `symbolic=True` |
| `Chain.from_mjcf_file` | `mjcf_file` | filesystem path | `base_elements=None` starts at the first body in `worldbody`; `symbolic=True` |
| `Chain.from_json_file` | JSON path | filesystem path | JSON supplies an URDF path and chain metadata, then delegates to `from_urdf_file` |

`from_urdf_file` accepts `base_elements`, `last_link_vector`,
`base_element_type`, `active_links_mask`, `name`, `symbolic`, and
`jax_precompile`. `from_mjcf_file` accepts `base_elements`,
`last_link_vector`, `active_links_mask`, `name`, and `symbolic`. The loader
prepends an `OriginLink`, so `len(chain.links)` is normally one greater than
the parsed model entries (and one more if a tip offset is appended).

A safe first inspection is:

```python
for i, link in enumerate(chain.links):
    print(i, link.name, link.joint_type, tuple(link.bounds))
print("active:", chain.active_links_mask.tolist())
```

Joint values passed to FK/IK must have one value per `chain.links`, including
the origin and inactive/fixed entries. `active_links_mask` only controls which
entries an optimizer changes; it does not remove links. Its length must equal
`len(chain.links)`. Give the origin and final fixed tip entries explicit
`False` values. In IKPy 4.0.0 the constructor checks the last NumPy boolean
with an identity comparison, so its warning/intended override is not a
substitute for supplying a correct mask.

## URDF: flat link/joint traversal

IKPy reads direct root-level `<link>` and `<joint>` elements in a URDF-like
XML document. A URDF path alternates source link and source joint names. With
the default `base_element_type="link"`:

```text
[base_link, shoulder_joint, upper_arm_link, elbow_joint, forearm_link]
```

With `base_element_type="joint"` the pattern begins with a joint:

```text
[shoulder_joint, upper_arm_link, elbow_joint, forearm_link]
```

The first item identifies the starting point; the source link itself is not
turned into an IKPy chain link. At each step, if the supplied list is exhausted,
the parser automatically chooses the first matching child joint or link in
source declaration order. This is useful for a simple chain, but is ambiguous
at a branching link. Supply the complete path when a tree has branches.

Use `base_elements=["base_link"]` to start at a link and auto-follow, or use an
explicit alternating list to pin the route. An empty list is rejected by the
URDF helper. Explicit names are checked while traversing and failures identify
the missing joint or link. `base_element_type` must be exactly `"link"` or
`"joint"`.

The parser implementation has these helpers (the leading underscore means
that the first three are diagnostics/internal helpers rather than stable user
entry points):

- `ikpy.urdf.URDF._find_next_joint(root, current_link, next_joint_name)`
- `ikpy.urdf.URDF._find_next_link(root, current_joint, next_link_name)`
- `ikpy.urdf.URDF._find_parent_link(root, joint_name)`
- `ikpy.urdf.URDF.get_chain_from_joints(urdf_file, joints)`
- `ikpy.urdf.URDF.get_urdf_parameters(urdf_file, base_elements, last_link_vector, base_element_type, symbolic)`

`get_chain_from_joints` turns a list such as `["m1", "m2"]` into alternating
parent-link/joint names such as `["base_link", "m1", "link1", "m2"]`. It is
useful when another tool exposes joints only. It does not append the terminal
child link. A missing joint raises `ValueError("Unable to locate the parent
link")`.

### URDF-to-IKPy mapping

Each traversed URDF **joint** becomes one `ikpy.link.URDFLink`; source URDF
`<link>` elements are used to find the route and then discarded. The resulting
`URDFLink` carries:

- `name`: the URDF joint name;
- `origin_translation`: `<origin xyz="...">`, default `[0, 0, 0]`;
- `origin_orientation`: `<origin rpy="...">`, default `[0, 0, 0]`, in radians;
- `rotation`: `<axis xyz="...">` for `revolute`;
- `translation`: `<axis xyz="...">` for `prismatic`;
- `bounds`: `<limit lower="..." upper="...">`, default `(-inf, inf)`;
- `joint_type`: `revolute`, `prismatic`, or `fixed`.

The accepted URDF joint types in this parser are only `revolute`, `prismatic`,
and `fixed`. A revolute joint needs a rotation axis and a prismatic joint needs
a translation axis. A fixed joint has neither; an axis on a fixed joint is
ignored with a warning. `continuous`, `planar`, and `floating` are not
silently equivalent to revolute/fixed here: they produce an unknown-joint
error. A `last_link_vector` adds a fixed `URDFLink` named `last_joint` with the
provided three-component translation and no joint axis.

### JSON metadata

`Chain.from_json_file` expects these keys:

```json
{
  "urdf_file": "robot.urdf",
  "elements": ["base_link", "joint1", "link1"],
  "active_links_mask": [false, true, false],
  "last_link_vector": [0.0, 0.0, 0.1],
  "name": "arm",
  "version": "v1"
}
```

`urdf_file` is resolved relative to the JSON file's directory. The three
optional fields may be the empty string, which the loader converts to `None`.
The JSON loader does not encode `base_element_type`, `symbolic`, or
`jax_precompile`; use the URDF loader when those settings matter. Missing
required keys surface as `KeyError`, and a bad relative path surfaces as the
usual filesystem error.

## URDF tree inspection

`ikpy.urdf.utils.get_urdf_tree(urdf_path, root_element,
out_image_path=None, legend=False)` returns `(dot, urdf_tree)`. It starts at a
link whose exact name is `root_element`, recursively follows root-level
parent/child joints, and stores nested `URDFTree.children_links`. A missing
root raises `ValueError`. The function imports `graphviz.Digraph`; rendering
with `out_image_path` additionally requires a working Graphviz `dot` executable
and writes a rendered artifact. Use it only for optional inspection, not as a
loader or validation substitute. `legend=True` adds colored link/joint nodes.

The related public utility module is `ikpy.urdf.utils`; its XML tree helpers
are separate from `ikpy.urdf.URDF.get_urdf_parameters`. Keep model inspection
read-only unless a caller explicitly requests an isolated render output.

## MJCF: hierarchical body traversal

MJCF uses nested `<body>` records under `<worldbody>`, rather than root-level
link/joint pairs. `Chain.from_mjcf_file` delegates to
`ikpy.mjcf.MJCF.get_mjcf_parameters`:

1. The root tag must be exactly `mujoco`.
2. `<worldbody>` is required and must contain at least one `<body>`.
3. With `base_elements=None`, traversal starts at the first worldbody body.
4. With a nonempty `base_elements`, the first named body may be found anywhere
   below `worldbody`.
5. After the starting body is selected, the implementation follows the first
   child body when no path names remain. In this release, passing multiple body
   names is not reliable: the remaining list is compared against the starting
   body again and can return an origin-only chain. Treat the documented
   multi-body path form as a version-specific limitation and verify the
   resulting names; use a one-name start plus an unbranched first-child route,
   or normalize/select the XML before import.

`base_elements=["base"]` names a starting body, not a joint. A missing starting
body raises a `ValueError`; a missing later child in an attempted multi-name
path currently ends traversal rather than raising, so inspect the resulting
names and do not assume the requested tip was imported.

Useful helpers are:

- `ikpy.mjcf.MJCF.get_body_names(mjcf_file)` — names below `worldbody`, or `[]`
  when `worldbody` is absent;
- `ikpy.mjcf.MJCF.get_joint_names(mjcf_file)` — joint names below `worldbody`,
  or `[]` when `worldbody` is absent;
- `ikpy.mjcf.MJCF.get_mjcf_parameters(mjcf_file, base_elements, last_link_vector, symbolic)`;
- `ikpy.mjcf.MJCF._get_compiler_settings(root)`;
- `ikpy.mjcf.MJCF._get_default_class(root, class_name)`;
- `ikpy.mjcf.MJCF._parse_body_transform(body_elem, compiler_settings)`;
- `ikpy.mjcf.MJCF._parse_joint(joint_elem, compiler_settings, default_settings)`.

A body with no `<joint>` becomes a fixed `URDFLink` named after the body. For a
body with multiple joints, the first joint includes the body transform plus its
joint `pos`; later joints share that body frame and use their own `pos` with a
zero orientation. `last_link_vector` again adds a fixed `last_joint` entry.

### MJCF joint mapping and defaults

The parser maps:

| MJCF type | IKPy `joint_type` | Axis used | Limits |
|---|---|---|---|
| `hinge` or `revolute` | `revolute` | `rotation` | explicit joint ranges convert to radians in degree mode; inherited default ranges are copied as provided by this implementation |
| `slide` or `prismatic` | `prismatic` | `translation` | linear units, not angle-converted |
| no joint on a body | `fixed` | none | unbounded |
| `ball` or `free` | `fixed` with warning | none | parsed range is retained but no DOF |
| other/unknown type | `fixed` | none | implementation fallback; do not rely on it |

The parser's fallback axis is `[0, 1, 0]` and fallback range is
`[-inf, inf]`. A joint's explicit `axis` or `range` wins. A joint `class` or
enclosing body's `childclass` selects a `<default class="...">` entry; that
entry can provide `joint axis` and `range`. Treat explicit joint attributes as
the portable option: unnamed top-level default settings and deep inheritance
are not a reliable contract in this IKPy parser version.

## MJCF compiler and orientation conventions

`_get_compiler_settings` defaults to `{"angle": "degree", "eulerseq": "xyz"}`.
`<compiler angle="radian">` changes body `euler`/`axisangle` handling and the
conversion of explicitly specified hinge ranges. With degree mode, an explicit
hinge `range` and body Euler/axis-angle angle are converted to radians; slide
ranges remain linear values. A range inherited from `_get_default_class` is
copied without that explicit-range conversion in this IKPy version, so make
critical hinge ranges explicit or verify `link.bounds` after import. Quaternion
components, `xyaxes`, and `zaxis` are not angle scalars.

`ikpy.mjcf.utils` converts MJCF orientations to IKPy RPY radians:

- `quat_to_rotation_matrix(quat)` and `quat_to_rpy(quat)` expect MuJoCo
  `(w, x, y, z)` quaternions;
- `axisangle_to_rotation_matrix(axis, angle)` and `axisangle_to_rpy(axis, angle)`
  expect `angle` in radians;
- `euler_to_rpy(euler, sequence="xyz")` uses the three-letter sequence;
- `xyaxes_to_rotation_matrix(xyaxes)` / `xyaxes_to_rpy(xyaxes)` expect six
  values containing X then Y axes;
- `zaxis_to_rotation_matrix(zaxis)` / `zaxis_to_rpy(zaxis)` expect three values
  and choose the minimal rotation from +Z;
- `rotation_matrix_to_rpy(R)` returns `[roll, pitch, yaw]` in radians.

Malformed vector lengths, zero axes in normalization operations, and degenerate
`xyaxes` are data errors even when XML itself is well formed. Validate numeric
attributes before trusting a recovered chain.

## Symbolic setting and path choices

`symbolic=True` builds SymPy-lambdified transformation functions on each
`URDFLink`; it is the default and requires the base `sympy` dependency. Use
`symbolic=False` to construct numeric NumPy transforms when startup cost or
symbolic compatibility is a concern. This flag changes chain construction, not
the unit convention: joint positions and orientations remain radians for
revolute rotations and meters/scene units for translations.

Do not use `backend="jax"` here to change import behavior. Load and validate the
chain with NumPy-compatible import first; route JAX cache, compilation, and
backend-specific FK/IK to `jax-backend`. Route FK/IK target selection to
`chain-kinematics`.
