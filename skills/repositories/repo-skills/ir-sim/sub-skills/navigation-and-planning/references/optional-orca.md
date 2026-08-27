# Optional ORCA group behavior

## Status and gate

ORCA is a group-level behavior implemented by `OrcaGroupBehavior`, not an
individual `behavior` value. The source registers it for `("omni", "orca")`
and `("diff", "orca")`, but its constructor imports the optional compiled
`pyrvo` package and creates a `pyrvo.RVOSimulator`. This graph does not claim
that ORCA is verified; it is reference-only until the local dependency is
independently probed and a bounded run succeeds.

Probe the dependency independently:

```bash
python - <<'PY'
try:
    import pyrvo
except ImportError as exc:
    print(f"ORCA unavailable: {exc}")
else:
    print(f"pyrvo importable: {pyrvo!r}")
PY
```

Install only after accepting the platform/build risk:

```bash
python -m pip install ir-sim[all]
# or, in an environment where the compiled wheel/build is supported:
python -m pip install pyrvo
```

An import probe is not a behavior verification. Independently test a tiny
headless group only when the import succeeds, and record its package/platform
result. Never claim ORCA worked merely because a YAML file parsed or because
RVO/SFM passed.

## Configuration shape

Put `group_behavior` on a group of same-role objects, commonly a multi-robot
YAML item:

```yaml
robot:
  - number: 3
    kinematics: {name: omni}
    shape: {name: circle, radius: 0.25}
    distribution: {name: circle, radius: 2.0, center: [4, 4]}
    group_behavior:
      name: orca
      neighborDist: 15.0
      maxNeighbors: 10
      timeHorizon: 20.0
      timeHorizonObst: 10.0
      safe_radius: 0.1
      maxSpeed: 1.0
```

The live `OrcaGroupBehavior` signature is:

```text
OrcaGroupBehavior(
  members, neighborDist=15.0, maxNeighbors=10,
  timeHorizon=20.0, timeHorizonObst=10.0,
  safe_radius=0.1, maxSpeed=None, **kwargs
)
```

`neighborDist` limits agent-neighbor search, `maxNeighbors` caps the number of
neighbors, and the two time horizons control the agent/obstacle horizons passed
to the simulator. `safe_radius` is added to each member's radius when the
agent is registered. `maxSpeed=None` uses each member's speed; a numeric value
overrides it. The YAML examples also use `wander`, `loop`, `range_low`, and
`range_high` for goal lifecycle behavior; those are not `pyrvo` simulator
parameters.

`omni` members consume the returned world-frame `(vx, vy)` action. For `diff`
members the source derives a goal-bearing preferred velocity, runs ORCA
holonomically, then converts the returned pair to `(linear, angular)` with the
IR-SIM differential adapter. This conversion is an integration detail, not
proof that a nonholonomic robot has the same guarantees as an omni agent.

## Group semantics and limits

An `ObjectGroup` evaluates one `GroupBehavior` and aligns its returned actions
with members. Individual actions take precedence when present; group actions
fill `None` entries during environment action assignment. If group membership
changes, the group wrapper updates its members; the ORCA handler rebuilds its
simulator when its member count changes.

Do not assume individual linestring handling carries over to ORCA. The built-in
ORCA handler shown in this source initializes `pyrvo` agents from group member
positions and does not expose the individual RVO line-segment list as a
portable configuration contract. Use individual RVO/SFM or a separately
verified controller when wall/linestring behavior is required.

For a no-`pyrvo` environment, use `behavior: {name: rvo}` or `behavior: {name:
sfm}` on `diff`/`omni` robots, or use `dash` for direct motion. Those are
fallback algorithms, not ORCA verification. See
[behaviors.md](behaviors.md), and use
[extension-and-control](../../extension-and-control/SKILL.md) for custom group
registrations.
