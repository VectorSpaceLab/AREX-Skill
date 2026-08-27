# Cross-cutting troubleshooting

Read the focused route first; this file covers failures that cross routes.

## Import and version failures

- **`ModuleNotFoundError` for NumPy, SciPy, OpenCV, Matplotlib, Torch, or
  TorchVision:** use a fresh isolated environment and install only the
  documented runtime stack. This checkout has no package metadata, so an
  editable install is not a supported proof of correctness.
- **`torchvision` operator/ABI errors or snapshot `state_dict` mismatches:**
  align Torch and TorchVision versions, then distinguish a bounded current
  numerical-stack check from loading a historical PyTorch 0.3 snapshot. Do not
  download or overwrite weights as a first repair. Let `<skill-root>` mean the
  directory containing the root `SKILL.md`, then run
  `python <skill-root>/scripts/check_environment.py --help` (and, when
  appropriate, without `--help`) before any external service. Historical
  source imports and source `main.py -h` were construction evidence only, not
  runtime instructions.
- **NumPy deprecation or Python-2 syntax errors:** this is a 2020-era research
  checkout. Keep the generated offline helpers on a current Python, but use a
  separately pinned historical runtime only when the full loop is explicitly
  required. Do not silently claim current end-to-end compatibility.
- **Historical `evaluate.py` or `plot.py` behavior is needed:** those source
  artifacts parse command-line arguments at import. Do not import or execute
  them from a checkout. Use the bundled standalone helpers in the evaluation
  route, whose commands are rooted at `<skill-root>/sub-skills/evaluation/`,
  and do not treat a source check as a runtime dependency.

## Path, data, and snapshot failures

- **Missing mesh, preset, snapshot, calibration, or session path:** validate
  the path before opening a service. Preset files must be checked with the
  bundled simulation validator; sessions must have the transition files
  documented by the evaluation route; real operation needs both calibration
  text files. Never substitute a random snapshot or pad a truncated log with
  zeros.
- **Unexpected coordinates or empty heightmaps:** check metre units, camera
  pose direction, depth scale application order, workspace limits, and NaN
  empty-cell semantics in `perception-geometry`. Validate a tiny fixture before
  moving a robot.
- **No completed evaluation trials:** confirm the selected method and
  `--num_obj_complete`. Reactive uses exact reward `0`; reinforcement uses
  reward `>= 0.5` only for grasp rows. A push reward is not a grasp success.
  `undefined` completion-conditioned metrics can be a genuine policy result.

## External simulator/service failures

- **Remote API connection refused or `sim_client == -1`:** start a compatible
  V-REP/CoppeliaSim scene with its remote API child script, confirm the
  implemented client endpoint `19997`, then preflight meshes and preset count.
  Do not change ports blindly or start a long-running loop while the scene is
  unstable.
- **Native remote API cannot load:** the historical platform-specific library
  must match the simulator/client ABI. Obtain it from the simulator setup; the
  generated skill intentionally does not ship the opaque binary.
- **RealSense TCP timeout/truncated frame:** start the streamer only after
  validating the SDK/device/USB 3 path; confirm port `50000`, `1280x720` shape,
  the 4,608,040-byte frame contract, and fragmented-read handling with the
  bundled capture validator. Do not treat a partial frame as valid depth.
- **UR5 timeout, force stop, or unsafe motion:** stop and place the controller
  in a safe state. Verify ports `30002`/`30003`, network reachability, home pose,
  workspace limits, tool orientation, and the real-time force threshold. Never
  bypass the guard or retry motion automatically.

## Verification boundary

Safe checks include module imports, CLI help, utility fixtures, preset schema
validation, offline session metrics, headless plot output, and a tiny CUDA
allocation. Simulator, camera-server, calibration, robot, GUI, weight download,
and long training checks require their external prerequisites and explicit human
approval; a skipped hardware check is a recorded limitation, not a pass.
