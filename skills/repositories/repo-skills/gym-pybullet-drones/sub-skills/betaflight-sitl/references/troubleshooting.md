# Betaflight SITL Troubleshooting

Use this page when the checker or wrapper says the external Betaflight layout is incomplete, when SITL launch fails, or when the UDP communication does not start.

## Missing `betaflight_sitl/bfN` directories

Typical symptoms:

```text
.../betaflight_sitl/bf0 not found
FileNotFoundError for betaflight_SITL.elf
The checker reports missing bfN directories
```

Recovery:

1. Run the bundled checker first:

   ```bash
   python scripts/check_betaflight_layout.py --num-drones 2
   ```

2. Verify that the expected external SITL tree exists at the location the installed package resolves for `BetaAviary`.
3. Confirm each requested drone has its own `bfN/obj/main/betaflight_SITL.elf` executable.
4. If the tree is missing, stop. This skill does not bundle the cloning/building step.

## Missing `gnome-terminal` or alternative terminal spawning differences

The source `BetaAviary` logic attempts to launch SITL instances in `gnome-terminal` when available and falls back to direct subprocess execution otherwise.

Recovery:

- Do not assume `gnome-terminal` is required on every host.
- If the checker says the terminal launcher is unavailable, note that the fallback path should still work on some hosts, but execution can be less visible.
- If execution fails immediately after launch, inspect the Betaflight executable itself and the `bfN` directory layout first rather than the launcher choice.

## UDP port mismatch

Typical symptoms:

- No PWM packets arrive.
- The example appears to launch but the drone never responds.
- A port is already in use.

Recovery:

- Compare the port map against the checker output.
- Drone `0` uses `9002/9003/9004`; each additional drone adds `10`.
- Make sure the number of requested drones matches the number of staged `bfN` directories.
- If ports are stale from a previous run, stop the old SITL processes before retrying.

## Trajectory or asset confusion

`beta.py` reads the package assets `beta-traj.csv` and `eeprom.bin`. If those files are missing in the installed package, the package install itself is incomplete.

Recovery:

- Reinstall the package in the active environment.
- Confirm the assets are part of the installed distribution, not only the source checkout.
- Do not edit the CSV in place unless you are intentionally changing the demonstration trajectory.

## GUI and plotting issues

The wrapper is safe by default with `--no-gui` and `--plot` off. If you enable GUI or plotting and the run fails:

- Re-run check-only mode to isolate the external layout.
- Only enable GUI on a host with a display/OpenGL stack.
- Keep plotting off until the external SITL path is confirmed to be stable.

## `BetaAviary` or wrapper exits before launch

Possible causes:

- The external layout is incomplete.
- The number of drones exceeds the number of staged SITL instances.
- The wrapper was asked to `--execute` before the check-only command passed.
- The package installation is incomplete and cannot locate the bundled assets.

Recovery:

1. Re-run `python scripts/check_betaflight_layout.py --num-drones N`.
2. Fix the missing paths or rebuild the external SITL tree.
3. Retry the execute path only after the checker reports a complete layout.

## When to stop

If the issue is the missing external Betaflight checkout/build, the correct next step is to stage that external tree outside this skill. Do not try to repair it by editing the generated skill files.
