# State, reset, action, and reward semantics

## 24-value state

For the repository's `environment_dim=20`, use this layout:

| Index range | Meaning | Units/range implied by code |
| --- | --- | --- |
| `0..19` | minimum 3-D Velodyne distance in each angular bin | initialized at `10`; no explicit normalization |
| `20` | x/y Euclidean distance to goal | non-negative distance in world units |
| `21` | relative goal heading `theta` | approximately `[-pi, pi]` |
| `22` | linear action used for the transition | environment action, `[0, 1]` |
| `23` | angular action used for the transition | environment action, `[-1, 1]` |

`reset` uses zeros at indices 22 and 23. It does not prepend a batch axis and
does not return a dictionary. A caller that supplies 23 or 25 values has a
contract violation; do not fix the mismatch by truncation or padding.

The first sensor callback starts with all bins at 10. Each callback resets all
20 bins to 10 before processing its current message, so a bin is not a
persistent obstacle memory. A point with a smaller distance replaces the
current bin minimum. A point with distance above 10 cannot increase a bin
above its default 10. `PointCloud2` is read with `skip_nans=False`; the
callback itself has no explicit finite-value or zero-horizontal-range guard.
For offline validation, reject non-finite values and zero horizontal range
rather than reproducing an exception or silently accepting a corrupted scan.

## Reset randomization

The reset path first calls `/gazebo/reset_world`. It samples a robot yaw
uniformly over `[-pi, pi]` and samples x/y uniformly in `[-4.5, 4.5]` until
`check_pos(x, y)` accepts the location. `check_pos` rejects a set of hard-coded
axis-aligned obstacle rectangles and rejects points outside the same `[-4.5,
4.5]` square. The accepted pose is published as model `r1` through
`gazebo/set_model_state`.

`change_goal` expands its sampling bounds by `0.004` per call toward `[-10,
10]` (starting at `[-5, 5]`), samples offsets from the current robot position,
and retries until `check_pos` accepts the goal. The goal is therefore not a
fixed point and is not guaranteed to be reachable by a straight line.

`random_box` repeats four times. Each `cardboard_box_0` through
`cardboard_box_3` receives a random x/y sample in `[-6, 6]` that passes
`check_pos` and is at least 1.5 units from both the robot and goal. The checks
are geometric filters, not collision proofs for the full box footprint.

The reset code then publishes a zero-action marker, advances physics for
`TIME_DELTA = 0.1`, pauses physics, and builds the observation from the latest
sensor bins and the reset pose. If callbacks or services did not work, this
can be stale or fail; an offline shape check cannot certify reset freshness.

## Strict event thresholds

`observe_collision(laser_data)` takes the minimum bin:

```text
collision = (min_laser < 0.35)
done      = collision
```

The inequality is strict: `min_laser == 0.35` is not a collision. An empty
laser array is invalid because taking its minimum fails. Non-finite values are
not a meaningful sensor observation for this contract.

After odometry is read, `step` computes distance to the current goal. It sets
`target=True` and `done=True` only when:

```text
distance < 0.30
```

Thus `distance == 0.30` is not a goal hit. If both collision and target are
true, `get_reward` gives target priority.

## Reward function

For `target`, `collision`, action `[linear, angular]`, and `min_laser`:

```text
if target:
    reward = 100.0
elif collision:
    reward = -100.0
else:
    r3 = (1 - min_laser) if min_laser < 1 else 0.0
    reward = linear / 2 - abs(angular) / 2 - r3 / 2
```

The shaping term is proximity pressure: below one unit, closer readings incur
a larger penalty; at or above one unit it contributes zero. There is no
explicit clipping. For valid non-collision inputs, `min_laser >= 0.35`; do not
invent an additional threshold or normalize the reward. The validator can
recompute this expression without ROS.

## Tiny synthetic fixture

For a 20-bin reduction, the points below are useful for an offline check:

```json
[[1.0, 0.0, 0.0], [2.0, 0.0, 0.0], [0.0, -1.0, 0.0], [1.0, 0.0, -0.2]]
```

The first two points fall in the bin containing angle zero (bin 10 with the
repository's gaps), so its minimum is `1.0`; the negative-z boundary point is
excluded because the test is `z > -0.2`; the point at negative pi/2 updates bin
0 to `1.0`. Unobserved bins remain `10.0`. A 0.349 laser minimum is a
collision, while 0.35 is not. A distance of 0.299 is a target, while 0.30 is
not.
