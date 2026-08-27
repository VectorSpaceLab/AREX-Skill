---
name: betaflight-sitl
description: "Operate gym-pybullet-drones Betaflight SITL workflows, including
  BetaAviary layout checks, UDP port mapping, and external prerequisite
  troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Betaflight SITL

Use this sub-skill when a task mentions Betaflight SITL, `BetaAviary`, `beta.py`, the `betaflight_sitl/bfN` directory layout, UDP ports, or the external build/check steps implied by the package's Betaflight example.

## Route here for

- Checking whether a local checkout or installed package has the external Betaflight SITL binaries staged in the layout that `BetaAviary` expects.
- Understanding the port mapping used by `BetaAviary` and the BetaFlight example.
- Running the bundled helper in check-only mode or, when explicitly requested, executing the wrapped BetaFlight workflow after prerequisites are present.
- Troubleshooting missing `betaflight_sitl/bfN` directories, missing executables, terminal-launch differences, or port mismatches.

## Do not handle here

- PID, velocity, downwash, or MRAC control simulations; route those to `control-simulation`.
- PPO hover training or playback; route those to `rl-workflows`.
- External Betaflight repository cloning/building itself. This sub-skill only describes and checks the prerequisites that must already exist.

## Start here

1. Read [workflows](references/workflows.md) to understand the layout check, port map, and optional execution flow.
2. Read [troubleshooting](references/troubleshooting.md) before attempting to run anything, especially on machines without a display or without the external SITL tree.
3. Prefer the bundled checker first:

   ```bash
   python scripts/check_betaflight_layout.py --num-drones 2
   ```

4. If and only if the checker reports a complete layout and the user explicitly wants execution, run the wrapper in execute mode:

   ```bash
   python scripts/run_beta_sitl.py --execute --num-drones 2 --duration-sec 5 --output-folder /tmp/gpd-beta --no-gui
   ```

## Runtime guardrails

- `clone_bfs.sh` is reference evidence, not a bundled runtime helper. It clones and patches an external Betaflight repository and should not be auto-run by future agents from this skill.
- `BetaAviary` expects the external SITL binaries to exist in a `betaflight_sitl/bfN` layout relative to the package checkout or installed-package path that the workflow is using.
- The package's BetaFlight example maps drones to ports in steps of 10: drone 0 uses 9002/9003/9004, drone 1 uses 9012/9013/9014, and so on.
- Keep the bundled runner check-only unless `--execute` is passed. This sub-skill is intentionally safe by default.
- When the external layout is missing, stop and report exactly what is absent rather than trying to clone or build Betaflight inside the generated skill.
