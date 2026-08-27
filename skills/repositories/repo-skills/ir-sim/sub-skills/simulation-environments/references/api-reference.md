# Environment API reference

The signatures below are the public 2.10.2 signatures inspected from the
installed package. `EnvBase3D` inherits the lifecycle and query API from
`EnvBase`; its constructor requires the `world_name` positional slot and
forwards other options to `EnvBase`.

## Construction

```python
irsim.make(
    world_name: str | None = None,
    projection: str | None = None,
    step_mode: Literal["internal", "external"] | None = None,
    **kwargs: Any,
) -> EnvBase

EnvBase(
    world_name: str | None = None,
    display: bool = True,
    disable_all_plot: bool = False,
    save_ani: bool = False,
    ani_kwargs: dict[str, Any] | None = None,
    full: bool = False,
    log_file: str | None = None,
    log_level: str = "INFO",
    seed: int | None = None,
    step_mode: Literal["internal", "external"] | None = None,
)

EnvBase3D(world_name: str | None, **kwargs: Any)
```

`make` chooses the registered projection constructor (`2d` by default,
`3d` for `EnvBase3D`) and passes `kwargs` through. Common kwargs are shown
in the constructor, not an unrestricted guarantee that every environment
class accepts every arbitrary keyword. A projection other than a registered
key raises `ValueError`.

`display=False` selects the Matplotlib `Agg` backend and prevents
`render()` from calling `plt.pause`; it does not mean that the constructor
never creates a Matplotlib figure. `disable_all_plot=True` skips render plot
work and makes `end()` return early, so use it only when that lifecycle caveat
is acceptable.

## Lifecycle and control

| Method | Exact signature | Contract |
|---|---|---|
| `step` | `step(self, action=None, action_id=0, *args, **kwargs)` | Normalized action IDs are aligned to objects. Internal mode steps objects; external mode refreshes supplied states and rejects a non-empty action. Then sensors, world clock, and status are updated. |
| `render` | `render(self, interval: float = 0.01, figure_kwargs: dict[str, Any] \| None = None, mode: str = "dynamic", **kwargs: Any)` | Updates the plot when the world sampling flag is true. `mode` is `dynamic`, `static`, or `all`; extra keywords go to object plotting. |
| `show` | `show(self) -> None` | Delegates to the environment plot's Matplotlib show operation; interactive/desktop use only. |
| `end` | `end(self, ending_time: float = 3.0, **kwargs: Any)` | Optionally writes an animation, optionally waits when displayed, closes all Matplotlib figures, clears environment object bookkeeping, and stops/disconnects keyboard hooks best-effort. |
| `close` | `close(self, ending_time: float = 3.0, **kwargs: Any)` | Alias that calls `end(ending_time, **kwargs)`. |
| `quit` | `quit(self) -> None` | Sets quit status, calls `end(ending_time=1.0)`, and raises `SystemExit(0)`. |
| `done` | `done(self, mode: str = "all") -> bool \| None` | Checks robot completion: `all` or `any`. Returns `False` with no robots and `None` for an unsupported mode. |
| `pause` | `pause(self) -> None` | Sets pause flag and status `Pause`; `step` then returns without a simulation update. |
| `resume` | `resume(self) -> None` | Clears pause and debug flags/counter and sets status `Running`. |
| `reset` | `reset(self, random: bool = False) -> None` | Restores initial state and clock; `random=True` rebuilds from cached parsed YAML and resamples. |
| `refresh` | `refresh(self) -> None` | Synchronizes geometry, collision tree, sensors, and status without advancing world time. |
| `reload` | `reload(self, world_name: str \| None = None) -> None` | Rereads YAML (or a replacement path) and rebuilds in the existing figure. |

The `step` method is decorated by the action normalizer. Use a NumPy vector
for a single robot action and a list of vectors for several actions:

```python
import numpy as np

env.step(np.array([0.8, 0.0]), action_id=0)
env.step([np.array([0.8, 0.0]), np.array([0.4, 0.1])], action_id=[0, 1])
```

For a list action with one integer `action_id`, entries are assigned to
successive aligned slots starting at that ID. With a list of IDs, the list
length must match the ID list. A NumPy action with a list of IDs is assigned
to each listed slot. Do not pass an action at all in external mode.

## Queries and scene-facing helpers

| API | Signature | Use |
|---|---|---|
| `get_robot_state` | `get_robot_state(self) -> np.ndarray` | State of the first robot; differential/omni normally provide `[x, y, theta]`, Ackermann includes steering state. |
| `get_lidar_scan` | `get_lidar_scan(self, id: int = 0) -> dict[str, Any]` | Convenience getter for a robot's LiDAR; payload details route to sensing. |
| `get_lidar_offset` | `get_lidar_offset(self, id: int = 0) -> list[float]` | Sensor offset for a robot. |
| `get_robot_info` | `get_robot_info(self, id: int = 0) -> Any` | One robot's information snapshot. |
| `get_robot_info_list` | `get_robot_info_list(self) -> list[Any]` | All robot information snapshots. |
| `get_obstacle_info_list` | `get_obstacle_info_list(self) -> list[Any]` | All obstacle information snapshots. |
| `get_map` | `get_map(self, resolution: float = 0.1) -> Any` | Builds a planning/collision map; map semantics route to sensing/mapping. |
| `get_group_by_name` | `get_group_by_name(self, group_name: str) -> list[ObjectBase]` | Objects carrying the requested group name. |
| `get_object_by_name` | `get_object_by_name(self, name: str) -> ObjectBase \| None` | Lookup by unique configured name. |
| `get_object_by_id` | `get_object_by_id(self, target_id: int) -> ObjectBase \| None` | Lookup by object ID. |
| `set_title` | `set_title(self, title: str) -> None` | Set a custom plot title. |
| `set_status` | `set_status(self, status: str) -> None` | Set the world status label. |
| `set_random_seed` | `set_random_seed(self, seed: int \| None = None, reload: bool = False) -> None` | Reset the process-level IR-SIM RNG; optionally call `reload()`. |
| `save_figure` | `save_figure(self, save_name: str \| None = None, include_index: bool = False, save_gif: bool = False, **kwargs: Any) -> None` | Save to the active path manager's figure or animation-buffer directory. |

The main properties are `robot`, `robot_list`, `robot_number`,
`obstacle_list`, `obstacle_number`, `objects`, `static_objects`,
`dynamic_objects`, `names`, `step_time`, `step_mode`, `time`, `status`,
`world_param`, `env_param`, `path_param`, `logger`, and `object_factory`.
`env.robot` raises `IndexError("No robots in the environment. Add a robot first.")`
when the scene has no robot. Object creation/addition/deletion is documented
under [scene-configuration](../../scene-configuration/SKILL.md); custom
controller state ownership is documented under
[extension-and-control](../../extension-and-control/SKILL.md).

## Rendering and drawing signatures

The inherited 2D-facing helpers are:

```python
env.draw_trajectory(self, traj: list[Any], traj_type: str = "g-", **kwargs)
env.draw_points(self, points: list[Any], s: int = 30, c: str = "b", refresh: bool = True, **kwargs)
env.draw_box(self, vertex: np.ndarray, refresh: bool = False, color: str = "-b")
env.draw_quiver(self, point: Any, refresh: bool = False, **kwargs)
env.draw_quivers(self, points: Any, refresh: bool = False, **kwargs)
```

`draw_points` accepts point lists or arrays interpreted as 2D coordinates;
`draw_quiver` uses `[x, y, u, v]`; `draw_box` expects a `2 x N` vertex matrix.
`draw_trajectory` accepts a list of state-like points or an array accepted by
the plot utility. `refresh=True` stores transient artists so later plot
clearing can remove them.

The 3D renderer overrides these signatures:

```python
EnvPlot3D.draw_points(points, s=10, c="m", refresh=True, **kwargs)
EnvPlot3D.draw_quiver(point, refresh=False, **kwargs)
EnvPlot3D.draw_quivers(points, refresh=False, **kwargs)
EnvPlot3D.draw_trajectory(traj, traj_type="g-", label="trajectory",
                         show_direction=False, refresh=False, **kwargs)
```

3D points/quivers use `[x, y, z]` and `[x, y, z, u, v, w]` forms. The 3D
trajectory renderer warns that `show_direction` is unsupported. It is a
projection of 2D object simulation; true 3D object models are not supported.
