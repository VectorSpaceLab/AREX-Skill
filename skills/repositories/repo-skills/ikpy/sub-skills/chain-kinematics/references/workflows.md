# Chain kinematics workflows

These recipes use only public IKPy APIs and small in-memory fixtures. They are
intended to be copied into a user's own program after installing `ikpy`.
Keep all vectors in the link order, including the origin/support links and the
inactive terminal link.

## 1. Build and validate a tiny NumPy chain

A two-segment planar fixture makes frame order and masks visible without a
robot file. The first moving link translates one unit along its origin X axis
and rotates about Z; the fixed tip translates one more unit along the rotated X
axis.

```python
import numpy as np
from ikpy.chain import Chain
from ikpy.link import OriginLink, URDFLink

links = [
    OriginLink(),
    URDFLink(
        name="planar_joint",
        origin_translation=np.array([1.0, 0.0, 0.0]),
        origin_orientation=np.zeros(3),
        rotation=np.array([0.0, 0.0, 1.0]),
        bounds=(-np.pi, np.pi),
        use_symbolic_matrix=False,
        joint_type="revolute",
    ),
    URDFLink(
        name="tool_tip",
        origin_translation=np.array([1.0, 0.0, 0.0]),
        origin_orientation=np.zeros(3),
        bounds=(-np.inf, np.inf),
        use_symbolic_matrix=False,
        joint_type="fixed",
    ),
]
chain = Chain(
    links=links,
    active_links_mask=[False, True, False],
    name="planar-demo",
)
assert len(chain.links) == 3
assert not bool(chain.active_links_mask[-1])

q0 = [0.0, 0.0, 0.0]             # full vector, not only active values
T0 = chain.forward_kinematics(q0)
np.testing.assert_allclose(T0[:3, 3], [2.0, 0.0, 0.0])

q90 = [0.0, np.pi / 2, 0.0]
T90 = chain.forward_kinematics(q90)
np.testing.assert_allclose(T90[:3, 3], [1.0, 1.0, 0.0], atol=1e-12)
frames = chain.forward_kinematics(q90, full_kinematics=True)
assert len(frames) == len(chain.links)
assert all(np.asarray(frame).shape == (4, 4) for frame in frames)
```

Use `np.asarray(frame)` if a DH link returns a `numpy.matrix`; the shape is
still `(4, 4)`. FK is a transform composition operation, not an optimizer: it
requires the complete vector and returns the end frame (or all intermediate
frames) deterministically.

## 2. Solve a reachable position target

Construct a homogeneous target when using the frame API, or use the compact
position API. Pass a full initial vector even though only one entry is active.

```python
target_position = np.array([1.0, 1.0, 0.0])
initial = np.zeros(len(chain.links))
solution = chain.inverse_kinematics(
    target_position=target_position,
    initial_position=initial,
)
assert solution.shape == (len(chain.links),)
np.testing.assert_allclose(
    chain.forward_kinematics(solution)[:3, 3], target_position, atol=1e-6
)
assert solution[0] == initial[0] and solution[-1] == initial[-1]
```

The returned vector contains inactive values from `initial_position`, not just
the optimizer's active variables. For repeated targets, use the previous full
solution as the next `initial_position` (warm starting can reduce local-minimum
jumps).

Equivalent frame-target form:

```python
frame_target = np.eye(4)
frame_target[:3, 3] = target_position
solution = chain.inverse_kinematics_frame(
    frame_target, initial_position=initial
)
```

`inverse_kinematics_frame` rejects anything other than a `(4, 4)` target. Use
it when a complete homogeneous frame is already available or when combining
position with a hand-built orientation block.

## 3. Add one-axis, all-axis, and orientation-only objectives

The compact method constructs the target frame from the arguments:

```python
# X, Y, and Z each take a vector of shape (3,).
solution_x = chain.inverse_kinematics(
    target_position=[1.0, 1.0, 0.0],
    target_orientation=[0.0, 1.0, 0.0],
    orientation_mode="X",
    initial_position=initial,
)
np.testing.assert_allclose(
    chain.forward_kinematics(solution_x)[:3, 0], [0.0, 1.0, 0.0], atol=1e-5
)

# "all" takes a 3x3 rotation block, not a flattened vector.
R_target = np.array([
    [0.0, -1.0, 0.0],
    [1.0,  0.0, 0.0],
    [0.0,  0.0, 1.0],
])
solution_all = chain.inverse_kinematics(
    target_position=[1.0, 1.0, 0.0],
    target_orientation=R_target,
    orientation_mode="all",
    initial_position=initial,
)
np.testing.assert_allclose(
    chain.forward_kinematics(solution_all)[:3, :3], R_target, atol=1e-5
)

# Omit position to optimize orientation only. A mode is mandatory.
orientation_only = chain.inverse_kinematics(
    target_orientation=np.eye(3),
    orientation_mode="all",
    initial_position=[0.0, np.pi / 2, 0.0],
)
np.testing.assert_allclose(
    chain.forward_kinematics(orientation_only)[:3, :3], np.eye(3), atol=1e-5
)
```

Orientation uses the end-frame columns: `X` is `fk[:3, 0]`, `Y` is
`fk[:3, 1]`, `Z` is `fk[:3, 2]`; `all` compares the complete upper-left
rotation block. IKPy does not validate that an orientation input is a proper
orthonormal rotation, so validate `R.T @ R ≈ I` and `det(R) ≈ 1` before solving.

## 4. Work with active masks and bounds explicitly

The active mask is a projection, not a shortened FK representation:

```python
full_initial = np.array([0.0, 0.1, 0.0])
active = chain.active_from_full(full_initial)
assert active.shape == (1,)
assert active[0] == full_initial[1]

reconstructed = chain.active_to_full([0.2], full_initial)
np.testing.assert_allclose(reconstructed, [0.0, 0.2, 0.0])
```

Every link has `link.bounds`; `None` means `(-np.inf, np.inf)`. The NumPy
least-squares path extracts bounds only for active links. Bounds must have
units matching the actuator and the starting active value must be within them.
The following deliberately asks for an out-of-bound planar angle and shows the
correct validation style:

```python
bounded_links = [
    OriginLink(),
    URDFLink(
        "bounded_joint", [1, 0, 0], [0, 0, 0], rotation=[0, 0, 1],
        bounds=(-0.25, 0.25), use_symbolic_matrix=False,
    ),
    URDFLink(
        "tip", [1, 0, 0], [0, 0, 0], joint_type="fixed",
        use_symbolic_matrix=False,
    ),
]
bounded = Chain(bounded_links, active_links_mask=[False, True, False])
clipped = bounded.inverse_kinematics(
    target_position=[0.0, 2.0, 0.0],
    initial_position=[0.0, 0.0, 0.0],
)
assert -0.25 - 1e-12 <= clipped[1] <= 0.25 + 1e-12
```

Use `optimizer="least_squares"` for the default residual solver or
`optimizer="scalar"` for the legacy scalar-norm minimize path. A target outside
the reachable set is not an exception by itself; inspect the final residual and
report that the result is a best effort.

## 5. Create revolute, prismatic, fixed, and DH links

For a prismatic joint, provide `translation` but no `rotation`:

```python
slide = URDFLink(
    name="slide_x",
    origin_translation=np.zeros(3),
    origin_orientation=np.zeros(3),
    translation=np.array([1.0, 0.0, 0.0]),
    bounds=(0.0, 0.5),
    use_symbolic_matrix=False,
    joint_type="prismatic",
)
np.testing.assert_allclose(slide.get_link_frame_matrix(0.25)[:3, 3], [0.25, 0, 0])
```

For a fixed link, omit both actuator axes and set `joint_type="fixed"`.
For a DH chain, keep one full-vector entry per `DHLink` and make each standard
DH row explicit:

```python
from ikpy.link import DHLink

rows = [
    # d, a, alpha, theta_offset, lower, upper
    (0.1, 0.0, np.pi / 2, 0.0, -np.pi, np.pi),
    (0.0, 0.5, 0.0,       0.0, -np.pi, np.pi),
]
dh_links = [
    DHLink(
        name=f"dh_{i}", d=d, a=a, alpha=alpha, theta=theta,
        bounds=(lo, hi), length=abs(a), use_symbolic_matrix=False,
    )
    for i, (d, a, alpha, theta, lo, hi) in enumerate(rows)
]
dh_chain = Chain(
    dh_links,
    active_links_mask=[True, False],  # last link is explicitly inactive
    name="dh-demo",
)
T = dh_chain.forward_kinematics([0.0, 0.0])
assert np.asarray(T).shape == (4, 4)
```

The `DHLink` `name` quirk is documented in [api-reference.md](api-reference.md):
set `link.name` after construction if labels are needed. DH parameters and
joint angles are normally in radians; do not copy degree-valued joint limits
into a radian model.

## 6. Serialize an imported chain safely

Serialization is metadata around a URDF-backed chain; it is not a general
pickle/export format for an arbitrary in-memory custom chain. Use the model
import route to create the chain first, keep the JSON beside the referenced
URDF, then reload it in a process where the pair remains together:

```python
from ikpy.chain import Chain

# `imported` is a Chain returned by the robot-model-import workflow.
json_path = imported.to_json_file(force=False)
restored = Chain.from_json_file(json_path)
assert len(restored.links) == len(imported.links)
np.testing.assert_allclose(
    restored.forward_kinematics([0.0] * len(restored.links)),
    imported.forward_kinematics([0.0] * len(imported.links)),
)
```

`to_json_file` writes `<chain name>.json` next to the original URDF and raises
`OSError` if that file exists unless `force=True`. `from_json_file` resolves the
stored `urdf_file` relative to the JSON location. A custom `Chain([...])` has no
URDF metadata and will fail in `to_json_file`; preserve custom link parameters
in an application-owned schema instead of manufacturing private metadata.

## 7. Concatenate chains without the v4.0.0 mask trap

`Chain.concat(chain1, chain2)` is public, but its implementation adds the two
NumPy masks rather than concatenating them. For robust composition, combine
public link and mask data explicitly:

```python
combined_links = chain1.links + chain2.links
combined_mask = [
    bool(value) for value in chain1.active_links_mask
] + [
    bool(value) for value in chain2.active_links_mask
]
combined = Chain(
    links=combined_links,
    active_links_mask=combined_mask,
    name=f"{chain1.name}+{chain2.name}",
)
assert len(combined.links) == len(combined.active_links_mask)
assert not bool(combined.active_links_mask[-1])
```

Before solving, decide whether the second chain's origin link is a true
physical joint or an unwanted duplicate support frame. If it is only a base
marker, mark it inactive and keep its zero entry in every full vector. Recheck
that the concatenated terminal link is inactive.

## 8. Numerical validation checklist

After every FK/IK operation:

```python
q = np.asarray(solution, dtype=float)
assert q.shape == (len(chain.links),)
T = np.asarray(chain.forward_kinematics(q), dtype=float)
assert T.shape == (4, 4)
assert np.allclose(T[3], [0, 0, 0, 1], atol=1e-8)
assert np.allclose(T[:3, :3].T @ T[:3, :3], np.eye(3), atol=1e-6)

position_error = np.linalg.norm(T[:3, 3] - target_position)
assert position_error < tolerance
```

For a full orientation target, also check
`np.linalg.norm(T[:3, :3] - target_R)`. For one-axis objectives compare only
the selected column. For an unreachable or bounded target, do not assert exact
matching; log the residual, verify every active value is within its declared
bounds, and decide whether the residual is acceptable for the application.
