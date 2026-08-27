# Simulator and Visual Tool Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `metadrive` import fails | optional simulator dependency is not installed | Document the simulator as unavailable or install the optional dependency in a separate environment. |
| PlotJuggler download/launch fails | network issue, stale binary, or unsupported platform | Use help checks, confirm the platform support matrix, or avoid auto-install in offline work. |
| Cabana/PlotJuggler UI crashes | missing GUI/display/Qt/OpenGL prerequisites | Prefer command syntax documentation or layout checks without launching the app. |
| replay cannot load route | route not accessible, auth missing, or local data absent | Use a demo route only when the task explicitly allows it; otherwise verify route access first. |
| `can_replay.py` cannot talk to hardware | no Panda/Panda Jungle or device bridge | Treat it as live-device-only tooling and skip on ordinary CPU hosts. |
| joystick control changes device state | it writes `JoystickDebugMode` and can interact with offroad/device control paths | Require explicit offroad intent and a device-safe environment before use. |
| simulator loops do not terminate | long-running control process or waiting for route/sim inputs | Use help/command-planning checks instead of live launch for routine verification. |
