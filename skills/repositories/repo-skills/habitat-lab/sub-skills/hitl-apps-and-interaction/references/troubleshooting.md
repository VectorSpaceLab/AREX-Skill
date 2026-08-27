# HITL Troubleshooting

Use this reference before launching or debugging full Habitat-HITL apps. Many failures are environment, graphics, data, or networking issues rather than bugs in app state code.

## Triage Order

1. Run the safe import/config probe first.
2. Confirm the intended mode: import-only, headed desktop, headless local loop, headless server, web/VR server, or simulator-only viewer.
3. Confirm launch working directory has `data/` or a suitable symlink.
4. Confirm Habitat-Sim supports the required graphics/physics path, especially Bullet for LabDriver rearrangement.
5. Confirm the selected config composes `hitl_defaults` and contains `habitat_hitl`.
6. Confirm datasets/assets match the example or app config.
7. Confirm network ports and client reachability only after local app initialization works.

## Import Failures

Symptoms:

- `ModuleNotFoundError: habitat_hitl`.
- `ModuleNotFoundError: websockets`, `aiohttp`, or `hydra`.
- Importing HITL modules fails before any app starts.

Likely causes:

- `habitat-hitl` is not installed in the active Python environment.
- Direct requirements are missing.
- The shell is using a different Python than the prepared Habitat environment.
- Core Habitat-Lab, Habitat-Baselines, or Habitat-Sim packages are missing for modules that import deeper runtime dependencies.

Actions:

- Use `scripts/hitl_config_probe.py --modules habitat_hitl habitat_hitl.core.hitl_main` from this sub-skill.
- Verify `websockets`, `aiohttp`, and `hydra-core` in the active environment.
- If only source checkout is present, install or expose `habitat-hitl` consistently with the rest of Habitat-Lab.
- Do not patch imports inside app scripts until the environment mismatch is ruled out.

## `data/` Directory Errors

Symptom:

- `FileNotFoundError` saying HITL apps expect a `data/` directory.

Cause:

- `hitl_main` checks for `data/` in the current working directory before choosing headed/headless mode.

Actions:

- Run the app from a directory that contains the Habitat `data/` tree.
- Or create a symlink named `data` in the app working directory.
- Confirm the required subdirectories are present, not just an empty `data/` directory.

## Habitat-Sim Bullet and Physics Errors

Symptoms:

- Assertion that Habitat-Sim is built without Bullet.
- Rearrangement app fails during LabDriver or simulator/task initialization.
- Articulated-object, humanoid, robot, or physics behavior is missing.

Cause:

- LabDriver is decorated to require Habitat-Sim with Bullet for HITL physics workflows.

Actions:

- Use a Habitat-Sim build/package with Bullet enabled.
- Route installation/build remediation to setup guidance rather than changing HITL app logic.
- For scene-only inspection that does not require Habitat-Lab tasks or physics, consider a SimDriver-style workflow.

## Headed Window and Display Failures

Symptoms:

- GLFW/Magnum platform errors.
- Cannot open display.
- OpenGL context creation fails.
- Remote desktop or container sessions fail before the app window appears.

Likely causes:

- No attached monitor or accessible display server.
- Missing GPU/driver/OpenGL support.
- Running over unsupported remote desktop/headless environment.
- `habitat_hitl.window` dimensions invalid or absent in headed mode.

Actions:

- Prefer `scripts/hitl_config_probe.py` for diagnostics that do not open windows.
- If a full app must run without a display, use an explicit headless config and set `habitat_hitl.window=null`.
- If headed rendering is required, use a machine/session with a real display or validated virtual display/GPU setup.
- Reduce extra viewports/debug images if context creation succeeds but performance is poor.

## EGL, Headless, and Container Issues

Symptoms:

- Headless mode still fails with graphics or simulator errors.
- EGL/OpenGL libraries are missing.
- Headless server starts but cannot render keyframes or debug images.

Important distinction:

- `experimental.headless.do_headless=True` avoids the desktop GLFW app, but it does not avoid Habitat-Sim, data, renderer, physics, or policy initialization requirements.

Actions:

- Confirm the config sets `habitat_hitl.window=null` in headless mode.
- Use `experimental.headless.exit_after` for bounded headless smoke runs.
- Disable optional debug-video output unless intentionally testing it.
- For networked headless servers, still verify Habitat-Sim can initialize the target scene in the selected backend.
- Avoid assuming headless mode is safe in CI unless the native test or config is known to skip unavailable data/backends.

## Pygame, GLFW, Magnum, and Input Confusion

Symptoms:

- User expects app code to poll OS input directly.
- Key presses are ignored or only remote input works.
- Mouse/camera controls feel stale or continuous input is choppy.

Model:

- App code reads `GuiInput`; it does not call Pygame/GLFW directly.
- Headed `GuiApplication` and remote `RemoteClientState` populate `GuiInput`.
- Remote clients send input at a different frequency than server frames; continuous input reset behavior matters.

Actions:

- Check whether the app reads `get_key`, `get_key_down`, mouse button methods, scroll offset, and `mouse_ray` appropriately.
- Check `networking.client_sync.server_input` when remote client input should control server `GuiInput`.
- Avoid adding direct OS event calls inside `AppState`.

## Browser/Websocket/VR Connection Failures

Symptoms:

- Unity/VR/web client cannot connect.
- Server starts, but client sees no scene.
- Client connects then disconnects or receives no keyframes.
- HTTP availability check reports unavailable.

Likely causes:

- `networking.enable` is false or wrong config is loaded.
- Firewall/router blocks the websocket port, default `18000`.
- Another server process already owns the port.
- Client points to the wrong server IP/address.
- Client and server are on different networks or corporate network isolation blocks traffic.
- `max_client_count` is reached.
- `wait_for_app_ready_signal=True` but app never calls `signal_app_ready()`.
- Client has incompatible or missing scene data for VR workflows.

Actions:

- Confirm the server config has `habitat_hitl.networking.enable=True` and expected `port`.
- Check that only one server is running on the host/port.
- Test local port reachability before involving a headset or remote browser.
- Verify client config uses the server address reachable from the client device.
- If HTTP availability is enabled, remember it can return unavailable when a single-client server already has a connected user.
- For VR, validate local Unity Editor connection before deploying to a headset.
- For Quest/headset usage, verify USB-deployed client config and same-network reachability.

## Port and Process Cleanup

Symptoms:

- Re-running an app reports port already in use.
- Client connects to an old app instance.
- Server appears unavailable after a crash.

Actions:

- Stop old HITL server processes before relaunch.
- If using multiprocessing/spawned networking, make sure the parent process exits cleanly or the child is terminated.
- Change `habitat_hitl.networking.port` temporarily only after confirming clients use the same port.

## Policy and Baselines Integration Failures

Symptoms:

- App initializes but fails when stepping the environment.
- Checkpoint load errors.
- Observation/action space mismatch.
- Multi-agent controller errors.
- GPU memory or CUDA device mismatch.

Likely causes:

- Baselines config does not match the selected task/agents.
- `eval.should_load_ckpt` and checkpoint path do not match available files.
- `gui_controlled_agents` leaves policy-controlled agents requiring a baseline policy.
- More than two agents are configured; `ControllerHelper` supports only one or two.
- Unsupported articulated agent type is configured for GUI control.

Actions:

- For viewer-only diagnosis, set `disable_policies_and_stepping=True` when appropriate.
- For basic viewer-style inspection, ensure `gui_controlled_agents` is empty if the app rejects GUI control.
- For rearrangement, confirm GUI-controlled agent index maps to `KinematicHumanoid` or `SpotRobot`.
- Route training/checkpoint creation and evaluation campaign fixes to the baselines skill.

## Dataset and Asset Errors

Symptoms:

- Missing HSSD scene dataset.
- Missing humanoid walk pose file.
- Missing Spot arm, YCB objects, humanoid assets, or scene instance JSON.
- Sim viewer cannot reconfigure scene.
- VR client renders missing or mismatched assets.

Likely causes:

- Required data bundles were not downloaded into `data/`.
- Running from the wrong working directory.
- Config points to dataset paths for a different data layout.
- Unity/VR workflows require a processed copy of assets separate from Habitat-Sim data.

Actions:

- Confirm config paths under `habitat_hitl`, `habitat.dataset`, and app-specific sections.
- Verify scene dataset config and scene instance file exist before launching full apps.
- For VR, ensure Unity client asset processing/import was completed with the same scenes intended for the server.
- Do not fix missing data by editing app logic unless the requested task is to change dataset selection.

## Session/Data Collection Failures

Symptoms:

- Runtime error when data collection is enabled.
- Expected JSON/pickle/gfx-replay files are missing.
- Files are written to an unexpected location.

Likely causes:

- `save_episode_record` or `save_gfx_replay_keyframes` is enabled without `save_filepath_base`.
- The working directory is not where the user expected.
- The session did not end cleanly or no steps were recorded.
- SimDriver does not support the same data collection path as LabDriver.

Actions:

- Set `habitat_hitl.data_collection.save_filepath_base` intentionally before running.
- Use relative paths only when the launch working directory is clear.
- End sessions cleanly so the driver saves buffered data.
- Avoid enabling data collection during simple import/config probes.

## Performance and Low SPS

Symptoms:

- App prints low SPS.
- Controls lag.
- VR/client motion jitters.
- Remote client receives delayed updates.

Likely causes:

- Hardware below target for scene complexity.
- Extra debug viewports/images or high window resolution.
- Retina/high-DPI display overhead.
- Network congestion or low client send/receive rate.
- Heavy policy inference on CPU or busy GPU.

Actions:

- Reduce window size, debug images, or debug third-person viewport.
- Use smaller scenes for VR/headset workflows.
- Disable Retina/high-DPI modes where practical.
- Keep laptop power connected.
- Avoid busy/corporate networks for VR; use a local router/hotspot when needed.
- Disable checkpoint/policy stepping only for diagnosis, not when policy behavior is required.

## When Not to Launch Full HITL

Choose probes or static review instead when:

- The user only asks whether imports/config modules are available.
- There is no display and no validated headless backend.
- Required datasets/assets are absent.
- The task is about config inspection rather than app behavior.
- Starting a websocket server could conflict with another service.
- The environment may write session outputs in an uncontrolled directory.
