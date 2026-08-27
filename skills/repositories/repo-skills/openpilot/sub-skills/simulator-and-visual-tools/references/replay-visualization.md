# Replay and Visualization Reference

## Replay

Replay simulates driving sessions by publishing logged messages from a route. Use it when you need to inspect message timing or watch openpilot run on route data.

Typical inputs:

- route name or segment range
- `--demo` for a built-in demo route when the workflow allows it
- `--data_dir` for local route files
- `--cabin`, `--wide-road`, `--qcam`, `--no-vipc`, and `--all` flags depending on the analysis target

`can_replay.py` streams CAN messages to connected Panda/Panda Jungle hardware. Treat it as live-device tooling, not a generic CPU test.

## Cabana

Cabana is the CAN/DBC viewer. It can load routes, Panda devices, SocketCAN, or ZMQ sources. Use it when the task needs raw CAN inspection or DBC cross-checking.

## PlotJuggler / JotPluggler

`juggle.py` installs or launches PlotJuggler, can infer DBC names from logs, supports `--demo`, `--stream`, `--layout`, `--dbc`, and `--install`, and may download binaries. Prefer help/layout checks when a GUI or network is unavailable.

## Camera/watch workflows

The replay README documents watch3 and multi-camera replay using cabin and wide-road streams. These workflows are useful for manual inspection, but they require real route data and often a UI.

## CTF/tool exploration

The tools README includes a CTF route for exploring the toolchain. Treat it as a special guided exercise, not a general verification target.
