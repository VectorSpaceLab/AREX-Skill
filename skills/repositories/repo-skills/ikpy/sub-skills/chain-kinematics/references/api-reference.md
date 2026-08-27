# Chain and link API reference

Read this file when exact argument names, array shapes, or v4.0.0 behavior
matter. The signatures below are verified against the package at the pinned
snapshot and the installed import. Angles and distances are plain NumPy/Python
values; angles are radians unless a caller's model explicitly uses another
unit consistently.

## Imports and core objects

```python
import numpy as np
from ikpy.chain import Chain
from ikpy.link import Link, OriginLink, URDFLink, DHLink
```

| API | Verified signature | Important result/contract |
|---|---|---|
| `Chain` | `Chain(links, active_links_mask=None, name="chain", urdf_metadata=None, jax_precompile=True, **kwargs)` | `links` is an ordered list. The stored mask has one entry per link. `name` is display/serialization metadata. |
| `Chain.forward_kinematics` | `forward_kinematics(self, joints: List, full_kinematics=False, backend: str="numpy")` | Requires `len(joints) == len(chain.links)`. Default returns one homogeneous `(4, 4)` end frame; `full_kinematics=True` returns a list of `len(chain.links)` `(4, 4)` frames. |
| `Chain.inverse_kinematics` | `inverse_kinematics(self, target_position=None, target_orientation=None, orientation_mode=None, backend: str="numpy", **kwargs)` | Returns a full joint vector with shape `(len(chain.links),)`, including inactive values. Position is `(3,)`; orientation is `(3,)` for `X`, `Y`, or `Z`, and `(3, 3)` for `all`. |
| `Chain.inverse_kinematics_frame` | `inverse_kinematics_frame(self, target, initial_position=None, backend: str="numpy", **kwargs)` | `target` must have shape `(4, 4)`. `initial_position` is a full vector; omitted means zeros. Returns a full vector. `orientation_mode` and `no_position` are passed through as optimizer kwargs. |
| `Chain.active_from_full` | `active_from_full(self, joints)` | Compresses along axis 0 using `active_links_mask`; a full `(n,)` vector becomes `(n_active,)`. It also works on an `(n, 2)` bounds array, producing `(n_active, 2)`. |
| `Chain.active_to_full` | `active_to_full(self, active_joints, initial_position)` | Copies the full initial vector and places active values into masked positions. Output is a float64 NumPy array with shape `(n,)`; inactive values remain from `initial_position`. |
| `Chain.concat` | `Chain.concat(chain1, chain2)` | Intended to concatenate links and masks, but v4.0.0 adds the two stored NumPy masks elementwise. It commonly creates a mask-length error or an invalid mask. Prefer the explicit safe recipe in [workflows.md](workflows.md). |
| `Chain.from_json_file` | `Chain.from_json_file(json_file)` | Reads the JSON metadata and resolves its `urdf_file` relative to the JSON file before delegating to the URDF importer. Returns a `Chain`. |
| `Chain.to_json_file` | `chain.to_json_file(force=False)` | Returns the written JSON path. Only chains carrying URDF metadata (normally created by `from_urdf_file`) have the fields required by this method. Refuses an existing output unless `force=True`. |
| `Chain.from_urdf_file` | `Chain.from_urdf_file(urdf_file, base_elements=None, last_link_vector=None, base_element_type="link", active_links_mask=None, name="chain", symbolic=True, jax_precompile=True)` | Creates a chain with an added `OriginLink`. Parsing and model-tree selection belong to the robot-model-import route. |
| `Chain.from_mjcf_file` | `Chain.from_mjcf_file(mjcf_file, base_elements=None, last_link_vector=None, active_links_mask=None, name="chain", symbolic=True)` | Creates a chain from MJCF and adds an `OriginLink`; use the robot-model-import route for file/model discovery. |

### Mask and terminal-link invariants

Use a boolean mask of exactly `len(chain.links)` entries. The first
`OriginLink` normally has `False`; fixed support links and the terminal link
should also be `False`. Active values are optimized and bounded; inactive
values are copied from the supplied full initial vector. Always pass a terminal
value anyway, usually `0.0`:

```python
full_q = [0.0] * len(chain.links)
full_q[active_index] = 0.25
assert len(full_q) == len(chain.links)
assert not bool(chain.active_links_mask[-1])
```

The constructor warns for an active fixed link and is intended to force the
last mask entry inactive, but its `numpy.bool_ is True` identity test is
brittle in this release. Treat the last-link rule as caller responsibility and
check it after construction.

## Link constructors and frame conventions

### Base and origin links

```python
Link(name, length, bounds=None, is_final=False)
OriginLink()
```

`Link` is the base class and does not implement
`get_link_frame_matrix(actuator_parameters)`. `bounds=None` means
`(-np.inf, np.inf)`. `OriginLink()` is fixed and returns `np.eye(4)` for any
parameter; its nominal length is `1` for chain bookkeeping.

### `URDFLink`

```python
URDFLink(
    name: str,
    origin_translation: np.ndarray,
    origin_orientation: np.ndarray,
    rotation: Optional[np.ndarray] = None,
    translation: Optional[np.ndarray] = None,
    bounds=None,
    angle_representation="rpy",
    use_symbolic_matrix=True,
    joint_type: str = "revolute",
)
```

The constructor sets `length = np.linalg.norm(origin_translation)`. Use exactly
one actuator description for a moving link:

- `joint_type="revolute"`: provide `rotation=[x, y, z]` and omit
  `translation`; the parameter is an angle in `get_link_frame_matrix(theta)`.
- `joint_type="prismatic"`: provide `translation=[x, y, z]` and omit
  `rotation`; the parameter is a displacement in
  `get_link_frame_matrix(mu)`.
- `joint_type="fixed"`: omit both axes; the parameter is ignored.

The constructor raises `ValueError` if the axes do not match the declared
joint type or if the type is unknown. `use_symbolic_matrix=False` is a useful
small-fixture/debug setting and returns ordinary NumPy calculations. The
`angle_representation` argument is accepted for compatibility; the verified
implementation applies the package's RPY convention.

The frame product for one URDF-style link is, in order:

1. translation by `origin_translation`;
2. orientation from `origin_orientation=[roll, pitch, yaw]` using
   `Rz(yaw) @ Ry(pitch) @ Rx(roll)`;
3. an axis rotation for a revolute joint, or axis translation for a prismatic
   joint.

The axis is used as supplied by the implementation; pass a unit axis for
physically meaningful rotation/translation. `get_rotation_axis()` and
`get_translation_axis()` return homogeneous `(4,)` vectors in the link's
origin frame and raise `ValueError` when the relevant actuator is absent.

### `DHLink`

```python
DHLink(
    name=None, d=0, a=0, alpha=0, theta=0, bounds=None,
    use_symbolic_matrix=True, length=0,
)
```

`get_link_frame_matrix(parameters)` returns a `(4, 4)` `numpy.matrix` using
`theta + parameters`:

```text
[ cos(t)  -sin(t) cos(alpha)   sin(t) sin(alpha)   a cos(t) ]
[ sin(t)   cos(t) cos(alpha)  -cos(t) sin(alpha)   a sin(t) ]
[   0          sin(alpha)          cos(alpha)          d     ]
[   0              0                  0                1     ]
```

Build a DH chain by passing one `DHLink` per row and use `length=abs(a)` (or a
model-specific display length) for chain geometry/bookkeeping. The source
constructor accepts `name`, but v4.0.0 passes `use_symbolic_matrix` into the
base `Link` name slot; if labels matter, set `link.name` explicitly after
construction and do not assume the constructor preserved it. DH links are
still usable for FK/IK; set explicit finite bounds when the model has joint
limits.

## Homogeneous geometry helpers

The most useful NumPy helpers are:

```python
from ikpy.utils import geometry

T = geometry.to_transformation_matrix(
    [x, y, z], orientation_matrix=np.eye(3)
)                                  # (4, 4)
translation4, rotation3 = geometry.from_transformation_matrix(T)
R = geometry.axis_rotation_matrix([0, 0, 1], theta)  # (3, 3)
Tt = geometry.get_translation_matrix([dx, dy, dz])   # (4, 4)
```

`from_transformation_matrix` follows the implementation and returns the last
column with shape `(4,)`, including the homogeneous trailing `1`, plus the
upper-left `(3, 3)` rotation. Strip `translation4[-1]` when a Cartesian `(3,)`
position is needed. Supplying the default `orientation_matrix` to
`to_transformation_matrix` produces an all-zero rotation block, so pass
`np.eye(3)` (or a real rotation) explicitly.

## NumPy IK options and residuals

`Chain.inverse_kinematics(..., **kwargs)` and
`Chain.inverse_kinematics_frame(..., **kwargs)` delegate NumPy solving to the
package optimizer. The supported direct optimizer arguments are:

```python
regularization_parameter=None
max_iter=None                 # compatibility warning; no longer used
orientation_mode=None        # None, "X", "Y", "Z", or "all"
no_position=False             # useful with inverse_kinematics_frame
optimizer="least_squares"   # or "scalar"
```

`least_squares` calls SciPy least-squares with active-link bounds and is the
default. `scalar` calls SciPy minimize on the norm of the residual. A result is
returned even when the target is only approximated; IKPy does not return the
SciPy result object or a convergence flag. Validate by recomputing FK and
measuring the residual.

The position residual is `fk[:3, 3] - target_position`. Orientation residuals
compare the selected end-frame column (`X`, `Y`, or `Z`) or the entire upper-
left `(3, 3)` block. `orientation_mode=None` with no position raises an error;
orientation-only work therefore needs a target orientation and a non-`None`
mode. IK uses the active portion of `initial_position` as the optimizer start,
then restores all inactive entries in the returned full vector.
