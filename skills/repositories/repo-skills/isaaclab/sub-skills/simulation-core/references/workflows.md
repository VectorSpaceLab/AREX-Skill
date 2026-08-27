# Simulation Core Workflows

## Launching a simulation app

1. Build an argument parser for the script.
2. Add launcher arguments through `AppLauncher.add_app_launcher_args(parser)` or the bundled `add_launcher_args` helper.
3. Parse the arguments and construct `AppLauncher(args)`.
4. Read `app_launcher.app` for the launched simulation app.
5. Create a `SimulationCfg` and `SimulationContext` before stepping the scene.

## Choosing a backend

- Use `PhysxCfg` when you want the Isaac Sim PhysX stack.
- Use `NewtonCfg` when you want kitless GPU-parallel simulation.
- Use `OvPhysxCfg` when you want standalone PhysX without launching Isaac Sim.
- Keep the renderer and visualizer choices consistent with the selected backend.

## Visualizer and camera rules

- Omit `--viz` when you want a default headless run.
- Use `--viz kit` only with Kit-compatible backends.
- Use `--viz newton`, `--viz rerun`, or `--viz viser` when you want a kitless visualizer.
- Pass `--enable_cameras` when the scene includes camera sensors or the run needs offscreen images.
- For livestreaming, set the relevant environment variables before launching the script.

## Headless and streamed runs

- `HEADLESS=1` and `--headless` force headless execution.
- `LIVESTREAM=1` or `LIVESTREAM=2` also forces headless mode while enabling streaming.
- The app launcher resolves the final state from both CLI and environment variables, so check both when debugging.

## Minimal smoke pattern

- Import the launcher and the relevant config classes.
- Construct a tiny `SimulationCfg`.
- Confirm that the chosen backend and visualizer combination is valid before building the full scene.
- Use the bundled inspection helper when you only need the public API shape and signatures.
