# HITL API Reference

This reference summarizes the practical Habitat-HITL concepts future agents need for diagnosis and small app changes. It intentionally avoids full viewer/VR launch code because those paths can open graphics windows, construct simulator environments, start network servers, or write session files.

## Package and Entry Points

- Package: `habitat_hitl` from the `habitat-hitl` distribution.
- Verified dependency names: `websockets`, `aiohttp`, and `hydra-core` are direct package requirements.
- Core entrypoint: `habitat_hitl.core.hitl_main.hitl_main(app_config, create_app_state_lambda=None)`.
- Hydra helper: `habitat_hitl.core.hydra_utils.register_hydra_plugins()` should be called before Hydra app entrypoints.
- App base class: `habitat_hitl.app_states.app_state_abc.AppState`.
- Service object passed to app states: `habitat_hitl.app_states.app_service.AppService`.

## `hitl_main`

`hitl_main` is the top-level runtime dispatcher. It:

1. Requires a `data/` directory in the current working directory.
2. Converts `app_config.habitat_hitl` into an object-style config.
3. Dispatches to headed mode unless `habitat_hitl.experimental.headless.do_headless` is true.
4. In headed mode, creates a GLFW/Magnum GUI application and replay renderer.
5. In headless mode, creates mock input/drawing objects and loops at `target_sps`.
6. Chooses `LabDriver` or `SimDriver` from `habitat_hitl.driver`.
7. Passes `create_app_state_lambda(app_service)` into the selected driver.

Important constraints:

- Calling `hitl_main` is not a harmless import check; it can open a window, initialize Habitat-Sim, construct datasets, start networking, or run an infinite-ish frame loop.
- Headless mode requires `habitat_hitl.window` to be `None`.
- LabDriver paths require Habitat-Sim with Bullet for rearrangement/physics workflows.
- Missing `data/` causes an early `FileNotFoundError` before runtime setup continues.

## Drivers

### `LabDriver`

Use for full Habitat-Lab environments. It:

- Patches Habitat config and enables gfx replay saving.
- Builds a dataset through Habitat dataset factories.
- Creates a gym-wrapped Habitat environment.
- Initializes `ControllerHelper` unless `disable_policies_and_stepping=True`.
- Exposes `env`, `sim`, metrics, episode helper, data recorders, GUI helpers, controllers, and client messaging through `AppService`.
- Applies `episodes_filter` by filtering and ordering dataset episodes.
- Saves episode records and gfx-replay keyframes when data collection is enabled.

### `SimDriver`

Use for simulator-only HITL apps. It:

- Creates a Habitat-Sim `Simulator` without a Habitat-Lab environment.
- Requires `disable_policies_and_stepping=True`.
- Does not support episode records or gfx-replay file collection in the same way as LabDriver.
- Provides `AppService.reconfigure_sim(dataset, scene)` for scene changes.
- Exposes `env=None`, no policy controllers, and no episode helper.

### `AppDriver`

The shared driver base owns:

- `Users` slot tracking.
- `ClientMessageManager` when networking is enabled.
- `GuiDrawer` wired to local debug-line rendering and/or remote-client messages.
- Networking subprocess launch/termination.
- `RemoteClientState` and `UIManager` for networked input/UI.
- Keyframe/message packaging for remote clients.

## `AppState`

Subclass `AppState` for app-specific logic.

Practical hooks:

- `sim_update(dt, post_sim_update_dict)`: called every frame before render/send. Update app state, optionally step the env, draw UI/debug elements, and set render outputs.
- `on_environment_reset(episode_recorder_dict)`: reset per-episode state and optionally add app-specific fields to the episode record.
- `record_state()`: called during recorded environment steps; use it to add per-step custom records when data collection is enabled.

Common `post_sim_update_dict` keys:

- `cam_transform`: required for main 3D viewport camera in headed/server-camera flows.
- `application_exit`: request exit from headed/headless loops.
- `application_cursor`: set pending cursor style.
- `keyframes`: emitted by drivers for renderer/networking internals.
- `debug_images`: emitted/consumed in headless debug-video paths.

## `AppService`

`AppService` is the app-facing object passed to `AppState` constructors.

Key properties:

- `config`: full Hydra/OmegaConf app config.
- `hitl_config`: object-style `habitat_hitl` config.
- `users`: active local or remote user slots.
- `gui_input`: keyboard/mouse input state.
- `remote_client_state`: remote client inputs, UI events, XR poses, connection events, and history.
- `gui_drawer`: line, circle, box, and highlight drawing helper.
- `text_drawer`: headed/headless text helper for local on-screen text.
- `ui_manager`: networked UI canvas helper.
- `env`: Habitat `Env` for LabDriver; `None` for SimDriver.
- `sim`: underlying Habitat-Sim simulator object.
- `compute_action_and_step_env`: call to compute controller actions and step LabDriver env.
- `step_recorder`: recorder used by data collection.
- `get_metrics`: returns recent Habitat metrics in LabDriver.
- `end_episode`: end or reset current episode in LabDriver.
- `set_cursor_style`: request cursor style change.
- `episode_helper`: current/next episode helper in LabDriver.
- `client_message_manager`: server-to-client messages when networking is enabled.
- `gui_agent_controllers`: GUI-controlled controllers indexed by user order.
- `all_agent_controllers`: controllers indexed by Habitat agent index.
- `reconfigure_sim`: simulator-only scene reconfigure function in SimDriver.

## GUI Input

`GuiInput` holds frame input state; it does not query OS APIs itself. The GUI application or remote-client state populates it.

Use:

- `get_key(KeyCode.X)` for held keys.
- `get_key_down(KeyCode.X)` and `get_key_up(KeyCode.X)` for frame transitions.
- `get_mouse_button(MouseButton.X)` and transition variants for mouse buttons.
- `mouse_position`, `relative_mouse_position`, `mouse_scroll_offset`, and `mouse_ray` for pointer/camera interactions.
- `get_any_input()` for idle detection.
- `reset()` only when implementing input plumbing, not inside ordinary app logic.

Common keys used by examples:

- `ESC`: exit.
- `P`: pause/unpause.
- `SPACE`: single-step, pick, or place depending on app.
- `M`: next episode.
- `W/A/S/D/Q/E/I/K/J/L`: camera or avatar movement controls.

## Drawing and Text Helpers

`GuiDrawer` draws debug geometry locally and/or sends equivalent remote-client messages.

Useful methods:

- `set_line_width(width)`.
- `draw_box(min_extent, max_extent, color, destination_mask=Mask.ALL)`.
- `draw_circle(translation, radius, color, ...)`.
- `draw_transformed_line(from_pos, to_pos, from_color, ...)`.
- `push_transform(transform)` and `pop_transform()` for local transform stacks.

`TextDrawer` is used for local on-screen text in desktop/headless paths. Example apps add control help and status text each frame.

## Client Messages and Remote State

Use `ClientMessageManager` to send server-to-client messages embedded in keyframes:

- Highlights, lines, and text.
- Modal dialog boxes and legacy UI buttons/textboxes.
- XR origin/headset rebasing messages.
- Scene-change and app-ready signals.
- Object outline and visibility-layer instructions.
- Viewport properties and UI canvas updates.

Use `RemoteClientState` to consume client-to-server state:

- `get_gui_input(user_index)` for remote keyboard/mouse state.
- `get_xr_input(user_index)` for XR controller/button state.
- `get_head_pose(user_index)` and `get_hand_pose(user_index, hand_idx)` for VR/avatar pose.
- `ui_button_pressed(user_index, button_id)` and `get_textbox_content(user_index, textbox_id)` for networked UI.
- `on_client_connected` and `on_client_disconnected` events for app/session state.
- Client history utilities for latency/keyframe synchronization.

Networking is only initialized when `habitat_hitl.networking.enable=True` and `max_client_count > 0`.

## `UIManager`

`UIManager` provides a structured, canvas-based network UI API.

Pattern:

```text
with app_service.ui_manager.update_canvas("center", Mask.ALL) as ctx:
    ctx.label(text="Ready")
    ctx.button(uid="start", text="Start", enabled=True)
```

Canvas names include `top_left`, `top`, `top_right`, `left`, `center`, `right`, `bottom_left`, `bottom`, `bottom_right`, and `tooltip`.

Use `is_button_pressed(uid, user_index)` to read button/toggle interactions reported by clients.

## Controller Helpers

`ControllerHelper` chooses per-agent controllers for LabDriver.

Core rules:

- Supports one or two agents; more than two raises an error.
- `gui_controlled_agents` must not exceed the number of Habitat agents.
- GUI-controlled humanoids use `GuiHumanoidController`.
- GUI-controlled Spot robots use `GuiRobotController`.
- Unspecified agents use Habitat-Baselines controllers.
- All-policy one-agent tasks use `SingleAgentBaselinesController`.
- All-policy two-agent tasks use `MultiAgentBaselinesController`.
- Mixed GUI/policy tasks create GUI controllers for configured agents and single-agent policy controllers for the rest.

Policy controllers own inference-time setup:

- Device selection uses CUDA when available, otherwise CPU.
- Observation transforms come from Habitat-Baselines config.
- Agent access managers create actor-critic inference wrappers.
- Checkpoints load only when both the agent should load state and eval config enables checkpoint loading.
- Recurrent hidden state, previous actions, and masks reset on environment reset.

## App/Session Structure Patterns

Simple apps keep all interaction in one `AppState`. Richer apps, such as multi-user rearrangement, split the workflow into state classes for loading, lobby, start session, in-session feedback, reset, and end session.

When debugging stateful apps:

- Identify which state owns client connect/disconnect behavior.
- Check whether UI canvases and modal dialogs are updated only for intended users.
- Check whether episode reset calls also reset controllers and app-local fields.
- Check whether data/session recorders write only when the config enables them.
- Check whether remote-client loading/app-ready signals gate scene changes correctly.

## Safe Introspection

Safe operations:

- Import `habitat_hitl` and selected modules.
- Inspect module presence and function/class names.
- Load YAML with a generic parser or OmegaConf without calling `hitl_main`.
- Check whether a config contains `habitat_hitl`, `driver`, `networking`, `window`, and headless fields.

Unsafe or side-effectful operations:

- Calling `hitl_main`.
- Instantiating `LabDriver` or `SimDriver`.
- Running example viewer scripts.
- Enabling networking.
- Running dataset download or Unity dataset processing.
- Saving data collection outputs.
