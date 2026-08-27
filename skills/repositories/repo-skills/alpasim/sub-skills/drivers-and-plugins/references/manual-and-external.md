# Manual and external drivers

## Manual driver

The manual policy is a CPU-only, human-in-the-loop adapter. It displays one
camera in a pygame window, consumes keyboard events, and generates a
constant-curvature arc that the controller tracks. It ignores route commands,
speed, acceleration, and pose history for decision making.

Controls:

| Input | Effect |
|---|---|
| `W` / Up | Increase target speed |
| `S` / Down | Decrease target speed |
| `A` / Left | Steer left |
| `D` / Right | Steer right |
| Space | Set target speed to zero |
| Escape / `Q` | Request quit and return a zero trajectory |

The control state clamps forward speed at 15 m/s, reverse speed at 7.5 m/s,
and steering at approximately 0.4 rad. The generated horizon is four seconds
at the configured output frequency. It paces responses against simulation
timestamps so the window does not run ahead of simulation time.

A display is required (X11 or Wayland). In a headless environment, use a
non-GUI policy or a virtual display only if that is an intentional operator
choice. Do not treat the manual model as a batch benchmark policy.

## External-static workflow

The driver process is not launched by the wizard in this mode. Start the manual
service using the installed driver package and the standalone `manual` config,
then run the wizard with a fixed external address:

```bash
# In the driver environment; use the package's standalone manual config.
uv run alpasim_driver_main --config-path=configs --config-name=manual

# In the simulation environment.
uv run alpasim_wizard \
  deploy=local topology=1gpu driver=manual \
  driver_source=external_static wizard.log_dir=./manual-run \
  scenes.scene_ids='["<scene-id>"]'
```

The standard manual preset advertises `localhost:6789`. If the driver runs on
another host, provide its reachable address explicitly:

```bash
uv run alpasim_wizard deploy=local topology=1gpu driver=manual \
  driver_source=external_static wizard.log_dir=./manual-run \
  'wizard.external_services.driver=["<driver-host>:6789"]'
```

Confirm the driver log's bind address and network reachability from the
runtime container. Binding to `0.0.0.0` listens on all interfaces; it is not an
access-control policy. Restrict exposure with the host/container network when
running outside a trusted machine.

The manual preset uses a 5 Hz control loop and 10 Hz camera updates in its
interactive configuration. It uses one front-wide camera at a reduced display
resolution. If you override these values, keep the camera logical ID and
interval compatible with the driver cache and the runtime cadence.

## External-dynamic workflow

`driver_source=external_dynamic` means the driver process is still external,
but the driver address is supplied per simulation request rather than fixed in
the wizard startup config. The wizard continues to own the renderer, physics,
traffic, controller, and runtime services; the driver is not silently started.
Use this mode only when the caller can provide a valid driver endpoint through
the request/API contract. Route request construction and protobuf details to
grpc-and-developer-tools.

## Shutdown and common workflow errors

- Close the GUI with Escape/Q or the window close action before stopping the
  external process. A stopped driver makes subsequent drive requests
  unavailable; it does not produce a valid zero-cost fallback.
- If the simulator connects but no frames appear, verify the external address,
  port exposure, and the selected front-wide camera. A GUI can be alive while
  the runtime cannot reach its bind address.
- If the driver responds too slowly, check timestamp pacing and camera/control
  cadence before increasing model batch size. Human control is intentionally
  real-time paced.
- A non-GUI environment, missing pygame, or display initialization failure is a
  manual-driver prerequisite error. It is not fixed by changing `device: cuda`.
