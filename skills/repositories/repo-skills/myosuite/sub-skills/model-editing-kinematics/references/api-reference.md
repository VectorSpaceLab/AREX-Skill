# API reference: editing, kinematics, and representations

This reference is self-contained around the public names needed for model
transformation and site-pose solving. It describes the base CPU implementation
first. `mujoco-mjx`, JAX, and CUDA are optional accelerators and are not
required by any contract here; the JAX quaternion module is a separate parity
concern.

## ModelEditor

Import:

```python
from myosuite.envs.myo.myoedits.model_editor import ModelEditor
```

Contract:

```python
editor = ModelEditor(model_path: str)
editor.edit_model(edit_fn: Callable[[mujoco.MjSpec], None] | None = None) -> None
artifact = editor.create_edited_xml() -> str
editor.delete_edited_xml() -> None
```

`ModelEditor` loads `model_path` with `mujoco.MjSpec.from_file`. Its `spec` is
therefore the editable object. `edit_model` calls the supplied function with
that spec; `None` does nothing. The edit function should mutate the spec and
return `None`, rather than returning a replacement spec. `spec.compile()` is
the compile gate, and `spec.to_xml()` is the serialization source.

`create_edited_xml` compiles and writes a timestamped sibling XML file. Its
return value is the artifact to compile or inspect. It is not a context
manager, and its cleanup method calls `os.remove` without an existence check.
Call cleanup from `finally` and guard it with `os.path.exists` when failure can
occur before the artifact path is usable. Keep the original model path
immutable. A caller that needs stronger cleanup should create its own
`TemporaryDirectory`, track the returned path, and remove only that path.

A compiled model is the handoff to `Robot`:

```python
from myosuite.robot.robot import Robot
robot = Robot(mj_model=compiled_model)
```

`Robot` creates `mujoco.MjData`, forwards it, and configures default or
explicit sensor/actuator mappings. Supplying `mj_model` avoids a second XML
load. Supplying `model_path` makes `Robot` load a fresh model. Hardware setup
is outside this sub-skill; for CPU simulation keep `is_hardware` unset/false.

## Base environment edit hook

The base environment constructor accepts `model_path`, optional
`obsd_model_path`, `seed`, and `edit_fn`. When a path is supplied, the base
implementation obtains an `MjSpec`, calls `edit_fn(spec)` when it is not
`None`, and compiles the resulting spec into `mj_model` (and into the observed
model when a separate observed path is supplied). This is the model-editing
boundary only: reset, stepping, reward, observations, viewer setup, and
Gymnasium lifecycle remain owned by the environment skill. `BaseV0` builds on
that boundary and may add named tip/target site IDs or actuator-condition
changes during its own setup; do not conflate those task options with
`ModelEditor`'s XML artifact API.

## Edit functions and `MjSpec`

Common `MjSpec` operations used by MyoSuite edit functions are:

- `spec.body(name)`, `spec.site(name)`: lookup by model name;
- `body.first_body()`: walk a body-child chain;
- `spec.delete(element)`: remove a spec element;
- `body.add_body(name=..., pos=...)`;
- `body.add_geom(meshname=..., name=..., type=...)`;
- `body.add_site(name=..., type=..., size=..., pos=..., rgba=...)`.

Use `.copy()` for NumPy-valued properties when taking a snapshot. Verify
lookups are non-`None` before reading properties. If an edit replaces a body
chain, snapshot names, positions, mesh references, and any sites that must
survive before deletion. Compile after rebuilding and query the compiled model
with MuJoCo's name lookup APIs to verify the intended body/geom/site exists.

## Inverse kinematics

Import:

```python
from myosuite.utils.inverse_kinematics import (
    IKResult, nullspace_method, qpos_from_site_pose,
)
```

`qpos_from_site_pose` expects a RoboHive-compatible `physics` facade, not a
bare `(MjModel, MjData)` pair. The facade must expose the model/data handles,
MuJoCo library calls, site lookup, state snapshot/restore, forward propagation,
and (when `joint_names` is used) a named DOF indexer. The bundled smoke
provides a small standard-MuJoCo facade so the base algorithm can be checked
without rendering or an external asset.

Inputs and outputs:

| Input | Contract |
|---|---|
| `site_name` | Existing site name; lookup failure is an input/model error. |
| `target_pos` | Optional finite numeric array of exact shape `(3,)`. |
| `target_quat` | Optional finite numeric array of exact shape `(4,)`, `(w,x,y,z)`. |
| `joint_names` | `None`, list, tuple, or NumPy array; restricts movable DOFs. |
| `tol`, `max_steps` | Residual threshold and hard iteration bound. |
| `inplace` | `False` restores state; `True` leaves solved data in place. |
| return | `IKResult(qpos, err_norm, steps, success)`. |

At least one target must be present. Position-only and orientation-only solves
use a three-row Jacobian; supplying both uses six rows. The residual combines
translation with weighted rotation. The method uses a site Jacobian, damped
least-squares-like regularization above a residual threshold, a step norm cap,
and a progress-stall stop. It does not handle joint limits.

`nullspace_method(jac_joints, delta, regularization_strength=0.0)` accepts a
Jacobian of shape `(ndelta, nv)` and delta shape `(ndelta,)`, returning an
`(nv,)` joint update. Positive regularization solves a regularized normal
system; zero regularization uses least squares.

## Quaternion and vector helpers

Import from `myosuite.utils.quat_math`:

- `mulQuat(qa, qb)`: quaternion product, four-vector result;
- `negQuat(quat)`: conjugate for the `(w,x,y,z)` convention;
- `diffQuat(quat1, quat2)`: `quat2 * conjugate(quat1)`;
- `quat2Vel(quat, dt=1)` and `quatDiff2Vel(quat1, quat2, dt)`: angular
  velocity representation;
- `axis_angle2quat(axis, angle)`; Euler/matrix conversions listed in the
  router; `rotVecMat`, `rotVecMatT`, and `rotVecQuat`.

Conversion helpers accept NumPy arrays with a final dimension of three for
Euler/vector inputs, four for quaternions, and `(3, 3)` for matrices. The
implementation uses assertions for several shape checks; callers should
validate with explicit `np.asarray(...).shape` and finite-value checks first.
A zero quaternion is treated as an identity matrix by `quat2mat`; do not use
that behavior to hide malformed orientation input. `mat2quat` chooses the
positive-w scalar representative when the rotation permits both signs.

`myosuite.utils.vector_math.calculate_cosine(vec1, vec2)` requires exactly
matching shapes, including batch dimensions, and contracts the last axis.
Zero-norm vectors are guarded internally but remain semantically ambiguous;
reject them when a direction is required.

## XML and tensor helpers

`myosuite.utils.xml_utils` provides:

- `parse_xml_with_comments(xml_path=..., xml_str=...) -> ElementTree`;
- `get_xml_str(tree=..., node=..., pretty=False) -> str`;
- `merge_xmls(receiver_xml, donor_xml, receiver_node=None,
  donor_node=None, destination="str")`;
- `reassign_parent(xml_path=... | xml_str=..., receiver_node=...,
  donor_node=..., donor_override=None, destination="str")`.

Pass exactly one XML source to the parser. `merge_xmls` appends donor-root
children to the receiver node. `reassign_parent` moves a named body, applies
optional `quat`/`euler`/`axisangle` overrides exclusively, and returns either a
string or tree. These are structural XML helpers; MuJoCo compilation remains a
separate validation step.

`myosuite.utils.tensor_utils` has NumPy-only bookkeeping helpers. The most
relevant contracts are `flatten_tensors(tensors) -> 1-D array`,
`unflatten_tensors(flattened, tensor_shapes) -> list`,
`stack_tensor_list(list) -> array`, `concat_tensor_list(list) -> array`, and
recursive dictionary variants. `pad_tensor` pads along the first axis with
zeros or the last item. They do not interpret `qpos`, `qvel`, quaternions, or
joint names; preserve the shape metadata yourself.

## Verification commands

Use commands that do not assume a viewer or accelerator:

```bash
python scripts/ik_smoke.py
python scripts/ik_smoke.py --max-steps 40
pytest test_editor.py -q
```

The last command is a native candidate when run from the repository's test
layout; the runtime skill itself does not depend on that checkout path. A
minimal API probe should compile a generated XML, resolve `world` and a known
site/body, and then remove its temporary artifact.
