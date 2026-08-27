# Keyboard and mouse control

IR-SIM's GUI helpers are Matplotlib integrations with an optional global
keyboard backend. Treat live input as reference-only unless a desktop backend
has been independently tested. Headless training and extension tests should
use `display=False`, `MPLBACKEND=Agg`, mocked event objects, or direct
controller calls.

## Enable keyboard control

Set the world control mode and put keyboard options under the root `gui`
section:

```yaml
world:
  control_mode: keyboard

gui:
  keyboard:
    backend: mpl       # mpl or pynput
    global_hook: false
    key_id: 0
    key_lv_max: 3.0
    key_ang_max: 1.0
    key_lv: 0.0
    key_ang: 0.0
```

`KeyboardControl(env_ref=None, **keyboard_kwargs)` accepts these values. The
source default is `backend="pynput"`; if `pynput` is unavailable, import
fails, or the backend name is invalid, it warns and uses Matplotlib (`mpl`).
Install the optional package only for a live global hook:

```bash
python -m pip install pynput
```

The `mpl` backend needs a focused Matplotlib figure and has no extra Python
input dependency. A `pynput` listener is also gated by figure focus unless
`global_hook: true`; operating-system permissions and desktop security policy
still apply. For `display=False`, IR-SIM does not start an OS listener, even if
`pynput` is installed. The event handlers remain callable for tests and
programmatic integration.

Keyboard input is used when `world.control_mode` is `keyboard`; configured
behaviors are not the source of the robot command in that mode. IR-SIM maps the
internal three-component keyboard vector to the selected robot's kinematics:
`diff`/`acker` receive `[linear, angular]`, `omni` receives
`[forward, lateral]`, and `omni_angular` receives `[forward, lateral, yaw_rate]`.
For omni variants, A/D lateral speed is rescaled from `key_ang_max` to
`key_lv_max`.

## Key actions

The two backends expose the same intent. Key release is significant for
stopping motion and changing limits.

| Input | Effect |
| --- | --- |
| `w` / `s` | forward / backward |
| `a` / `d` | turn for `diff`/`acker`; strafe for omni variants |
| `q` / `e` | positive / negative yaw for `omni_angular` |
| `z` / `c` | decrease / increase angular speed limit |
| `shift+z` / `shift+c` | decrease / increase linear speed limit |
| `alt+number` | select the controlled robot id |
| `r` | set the environment reset flag |
| `space` | pause or resume |
| `x` | toggle keyboard and auto control modes |
| `l` | set the reload flag |
| `v` | set the save-figure flag |
| `y` | toggle display state |
| `F5` | enter or advance debug single-step mode |
| `esc` | set the quit flag |

Use `env.key_vel`, `env.key_id`, and `env.status` for observable control
state. In a multi-environment process, only one keyboard instance is active at
a time when focus gating is enabled; switching focus deactivates the previous
instance. Do not assume a global hook is safe for parallel training.

## Mouse helper

`MouseControl(ax, zoom_factor=1.1)` attaches Matplotlib motion, click, release,
and scroll callbacks. The environment exposes the latest values as
`env.mouse_pos`, `env.mouse_left_pos`, and `env.mouse_right_pos`:

- moving inside an axes records `(xdata, ydata)`; moving outside clears
  `mouse_pos`;
- left and right clicks store rounded two-decimal coordinates until their
  corresponding release;
- scroll up zooms in around the cursor and scroll down zooms out;
- middle click calls `reset_zoom()`;
- `set_zoom_factor(factor)` clamps the factor to at least `1.1`.

A click-driven goal workflow is an application pattern, not an automatic
controller. For example, in internal mode a caller can read
`env.mouse_left_pos`, call `robot.set_goal(...)`, and then allow a compatible
behavior to act. The callback itself does not change robot state.

## Safe GUI workflow

1. Start with `display=False` and `backend: mpl`; verify import and scene
   construction without opening a window.
2. Test handlers with small mocked objects carrying `event.key`,
   `event.inaxes`, `event.xdata`, `event.ydata`, `event.step`, and
   `MouseButton` values. Assert key vectors, flags, click coordinates, and
   axis limits rather than relying on OS input.
3. Only then use a desktop backend, a focused figure, and a single short run.
   Always call `env.end(0)`/`env.close(...)` in cleanup.

The native GUI and keyboard examples are evidence for these mappings, not
runtime dependencies. The bundled custom registration helper deliberately does
not start `KeyboardControl` or `MouseControl`.
