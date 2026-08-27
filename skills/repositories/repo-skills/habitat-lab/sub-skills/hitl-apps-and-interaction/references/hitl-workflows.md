# HITL Workflows

## Choose the Right HITL Mode

| User goal | Best path | Why |
|---|---|---|
| Check whether `habitat-hitl` is importable | Run `scripts/hitl_config_probe.py` | It imports selected modules without opening a window, constructing `Env`, or starting sockets. |
| Inspect a Habitat environment and episodes interactively | Use a basic viewer-style `LabDriver` app | It steps a `habitat.Env`, runs policy controllers if enabled, and provides free-camera controls. |
| Inspect a single Habitat-Sim scene without a Lab task | Use a sim viewer-style `SimDriver` app | It avoids Habitat-Lab env/task construction and reconfigures the simulator scene directly. |
| Build a minimal desktop app | Implement a small `AppState` and pass it to `hitl_main` | `AppState.sim_update()` owns per-frame app logic and supplies `cam_transform`. |
| Run rearrangement with a human-controlled agent | Use a rearrange-style `LabDriver` app with `gui_controlled_agents` | Human input maps to `GuiHumanoidController` or `GuiRobotController`; remaining agents can be policy-controlled. |
| Serve a remote web/VR client | Enable `habitat_hitl.networking.enable=True` only when ports, clients, and data are ready | Networking starts a subprocess, websocket server, optional HTTP availability server, and client-state/message synchronization. |
| CI or machine without a display | Prefer import/config probes or explicit headless configs | Headless HITL still constructs simulator/env objects and can require Bullet, data, and graphics backend support. |

## Minimal and Basic Viewer Flow

A minimal HITL app follows this pattern:

1. Register Habitat/Hydra plugins before invoking the Hydra entrypoint.
2. Load a config that includes `hitl_defaults` and the selected Habitat task or simulator settings.
3. Implement an `AppState` with `sim_update(dt, post_sim_update_dict)`.
4. In each frame, optionally call `app_service.compute_action_and_step_env()` while the episode is active.
5. Set `post_sim_update_dict["cam_transform"]` for the renderer.
6. Set `post_sim_update_dict["application_exit"] = True` to exit cleanly, commonly on `KeyCode.ESC`.
7. Call `hitl_main(config, lambda app_service: YourAppState(app_service))`.

A basic viewer expands the minimal pattern with:

- `CameraHelper` for free-camera orbit/look controls.
- `EpisodeHelper` for next-episode navigation.
- `TextDrawer` for on-screen status and control help.
- Optional debug third-person viewport and `debug_images` configured under `habitat_hitl`.
- Policy/controller stepping through `compute_action_and_step_env()` unless paused.

## Config Launch Decisions

HITL config is normally composed from a Habitat task/baseline config plus `hitl_defaults`.

Key `habitat_hitl` decisions:

- `driver`: use `LabDriver` for a full Habitat-Lab environment; use `SimDriver` for simulator-only scene viewing.
- `window`: required for headed desktop mode; must be `None` when `experimental.headless.do_headless=True`.
- `experimental.headless.do_headless`: skips the GLFW window path but still constructs drivers and may need Habitat-Sim/data support.
- `target_sps`: desired steps per second; low actual SPS indicates hardware, scene complexity, rendering, or network pressure.
- `disable_policies_and_stepping`: useful for low-power diagnostics or simulator-only viewing; full policy behavior is skipped.
- `debug_third_person_viewport` and `debug_images`: add extra render outputs, which can increase graphics cost.
- `gui_controlled_agents`: declares which Habitat agents are controlled by GUI/remote input; unspecified agents are policy-controlled.
- `networking.enable`: starts the websocket networking subprocess and remote-client message flow.
- `networking.max_client_count`: limits concurrent clients and drives the user-slot container.
- `networking.client_sync.server_camera`: send server camera transforms to clients when the server controls the viewpoint.
- `networking.client_sync.server_input`: bind the first remote client's input into the server `GuiInput`.
- `networking.client_sync.skinning`: disable for first-person remote clients when skinned humanoid poses are not needed or are costly.
- `data_collection`: records per-episode JSON/pickle data or gfx-replay keyframes; requires a save filepath base when enabled.

## App Selection Patterns

### Minimal App

Use when the user needs the smallest custom app skeleton. It assumes a full Habitat-Lab task config, steps until episode end, sets a fixed camera, and exits on `ESC`.

Check before running:

- `data/` is visible from the launch working directory.
- The selected config includes `hitl_defaults`.
- Habitat-Sim was built with Bullet for LabDriver/rearrange workflows.
- A display or deliberate headless mode is available.

### Basic Viewer

Use when the user needs to inspect episodes and policy behavior with a free camera. It normally loads a social rearrangement baseline config, disables checkpoint loading in example config, and offers pause/single-step/next-episode controls.

Good signs:

- The user asks to inspect episodes, camera sensors, task success/failure, or policy stepping in real time.
- No GUI-controlled agents are required; the example rejects non-empty `gui_controlled_agents`.

### Sim Viewer

Use when the user wants scene visualization without a Habitat task. It uses `SimDriver`, `disable_policies_and_stepping=True`, and `reconfigure_sim(dataset, scene)`.

Good signs:

- The user has a scene dataset config and scene instance.
- The question is about viewing a Habitat-Sim scene rather than task metrics or policy behavior.

### Rearrange App

Use for a collaborative rearrangement session with a user-controlled humanoid and a policy-controlled robot. The app uses helpers for camera, navigation hints, pick/place affordances, controller action hints, and optional data collection.

Check before running:

- HSSD/Habitat humanoid/Spot/YCB-style assets required by the config are present.
- `gui_controlled_agents` maps to a supported articulated agent type: `KinematicHumanoid` or `SpotRobot`.
- Policy-controlled agents can initialize from Habitat-Baselines without missing checkpoints or unsupported observation/action spaces.
- Data collection paths are intentional, because records and gfx-replay files are written during sessions.

### Rearrange V2

Use as an experimental app/session structure reference for single-user, multi-user, and user-agent rearrangement flows. It has a richer state-machine/session organization than the simple rearrange app and may depend on additional planner/application modules.

Good signs:

- The user asks about session/lobby/start/end/feedback app states.
- The task involves multi-user or user-agent settings rather than a single local desktop controller.

### Pick/Throw VR

Use for a proof-of-concept remote VR interaction app. It can run mouse/keyboard locally or enable networking for a Unity-based VR client. The server remains a Habitat-HITL app; the client receives gfx-replay keyframes/messages and returns input/avatar state.

Check before networking mode:

- The server has a display or explicit headless server config.
- Firewall allows the websocket port, default `18000`.
- The client is on a reachable network and points to the server address.
- `networking.client_sync.server_camera=False` is appropriate for VR/client-controlled camera.
- `networking.client_sync.skinning=False` may reduce first-person overhead and avoid humanoid-occlusion issues.

## Multiplayer and Network Notes

HITL networking is a server subprocess around websockets plus optional HTTP availability checks. It is not a generic REST service.

Operational notes:

- Extra clients beyond `max_client_count` are rejected.
- Client slots are indexed by user id; messages can target all users or masks.
- The network manager sends consolidated keyframes to late-joining clients.
- `wait_for_app_ready_signal=True` delays keyframe sending until the app calls `ClientMessageManager.signal_app_ready()`.
- `client_max_idle_duration` can kick idle users through `ClientHelper`.
- Remote UI and input state are separate: use `RemoteClientState` for client input/UI events and `ClientMessageManager`/`UIManager` for server-to-client messages.

Common checks:

- Is another HITL server already using the selected port?
- Is the client sending its initial ready/connection parameters?
- Does the firewall/router allow traffic between devices?
- Are server and client using compatible scene data and coordinate expectations?

## Policy Integration Boundaries

HITL apps integrate policies through controller helpers rather than training loops.

- `LabDriver` constructs a Habitat-Lab gym environment and, unless disabled, a `ControllerHelper`.
- `ControllerHelper` supports one or two agents.
- If every agent is policy-controlled, it creates single-agent or multi-agent Habitat-Baselines controllers.
- If some agents are GUI-controlled, it creates GUI controllers for configured agents and policy controllers for the rest.
- `BaselinesController` initializes policy access managers, observation transforms, recurrent hidden state, and checkpoint loading only when the config asks for it.
- `AppState` should call `app_service.compute_action_and_step_env()` to let controllers produce actions and step the environment.

Do not use HITL as the primary answer for training or batch evaluation. Route checkpoint creation, PPO/DDPPO settings, metric aggregation, and evaluation campaigns to the baselines skill; use this sub-skill only for how those policies are embedded in realtime human interaction.
