# External control and state ownership

Use external mode when another simulator, estimator, or controller owns the
object state. Use internal mode when IR-SIM should integrate a kinematics model
from a behavior or action. Do not mix the two ownership models in one step.
For ordinary scene/state dimensions, route to
[scene configuration](../../scene-configuration/SKILL.md); for lifecycle and
clock details, route to [simulation environments](../../simulation-environments/SKILL.md).

## Select the mode

Set the mode in YAML:

```yaml
world:
  step_mode: external
```

or override it at construction:

```python
env = irsim.make("scene.yaml", step_mode="external", display=False)
```

The public `irsim.make` signature accepts `step_mode="internal"` or
`"external"`; an explicit constructor override takes precedence over the YAML
value. The default is internal.

## The external tick

For each tick, update every externally owned dynamic object before calling
`env.step()`:

```python
for obj, state, velocity in incoming_states:
    obj.set_state(state)
    obj.set_velocity(velocity)

env.step()  # no action and no action_id
```

`set_state()` validates the configured state shape, copies the state, updates
the object's transformed geometry, and invalidates reactive caches.
`set_velocity()` validates the kinematics velocity shape, copies the velocity,
and invalidates the same caches. Update both values: if velocity is omitted,
IR-SIM retains the previous velocity, so downstream velocity projections,
collision-avoidance observations, logs, and controllers can describe the wrong
motion even though the pose changed.

In external mode, `env.step()`:

1. rejects any non-`None` action with `ValueError` rather than integrating a
   second command;
2. refreshes every object and rebuilds the collision spatial index;
3. updates all attached sensors from the consistent refreshed snapshot;
4. advances world time/status and collision/arrival bookkeeping.

It does **not** run IR-SIM kinematics or behavior generation. A controller that
passes an action to `env.step(action)` in this mode is mixing ownership and
will fail by design. If objects are static or intentionally omitted from the
external update, document that policy explicitly; a dynamic object still
retains its previous pose/velocity.

## Refresh after direct mutation

If code mutates a state through a public setter and needs derived data before
the next tick, call:

```python
robot.set_state(new_state)
robot.set_velocity(new_velocity)
env.refresh()  # no clock advance; rebuilds geometry/tree, sensors, status
```

`env.refresh()` calls the object refresh path, rebuilds the collision tree,
updates sensors, and re-evaluates status without advancing the simulation.
Calling `set_state()` alone updates that object's geometry but does not rebuild
the environment-wide spatial index. Never write `_state`, `_velocity`, or
`_geometry` directly. If a wrapper has already updated all objects and only
needs the normal external tick, call `env.step()` and let its ordered refresh
perform the synchronization.

Sensor ordering matters: all object poses are refreshed before sensors run.
This prevents one sensor from seeing a mixture of old and new externally
supplied states. See [sensing and mapping](../../sensing-and-mapping/SKILL.md)
for scan payloads and explicit sensor timing.

## Internal controller boundary

A controller that computes a kinematics-compatible action can stay in internal
mode and pass its result directly:

```python
env = irsim.make("scene.yaml", display=False)
for _ in range(100):
    action = controller(robot, env.obstacle_list)
    env.step(action, action_id=robot.id)
```

The action's shape and meaning are kinematics-specific: differential and
Ackermann robots use two controls, while `omni_angular` uses three. IR-SIM
clips commands to the object's configured limits and acceleration range. If a
controller owns the pose update itself, use external mode instead of both
calling `env.step(action)` and setting the pose.

## CBF/QP integration boundary

The repository documents CBF and collision-cone CBF examples as standalone
controller integrations, not as a registry or core dependency. The general
pattern is:

```python
# internal mode: controller returns an IR-SIM action
action = controller.get_action(env.robot, env.obstacle_list)
env.step(action)
```

The documented examples use `cvxpy`, support `omni` and `diff` action
semantics, and are designed primarily around circular obstacles with position,
radius, and velocity information. A QP that cannot find a feasible solution
returns zero control in those examples; zero can mean a safety fallback rather
than successful progress. Polygon/rectangle handling is not geometrically
exact in that example family. Install and probe the solver separately; do not
make `cvxpy` a requirement for ordinary IR-SIM operation.

A CBF/QP controller can instead be wrapped around an external simulator, but
then it must provide the next state **and** velocity to IR-SIM and call
`env.step()` without an action. Do not infer that a paper-specific CBF,
look-ahead mapping, solver choice, or obstacle approximation is a general
IR-SIM API. Keep those equations and external dependencies in the controller
project, and use this reference only for the IR-SIM ownership boundary.

## Verification boundary

A safe synthetic check should use a tiny headless scene and assert that
external `env.step()` advances time after `set_state`/`set_velocity`, while
`env.step(action)` raises `ValueError`. It should also compare geometry or a
sensor reading after `env.refresh()`. Do not run a live CBF/QP, desktop GUI, or
long external co-simulation as part of the bundled skill smoke.
