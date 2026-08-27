# Betaflight SITL Workflows

This reference explains the package's Betaflight integration without requiring the original repository checkout. Use the bundled [`../scripts/check_betaflight_layout.py`](../scripts/check_betaflight_layout.py) checker before any execution attempt, and use [`../scripts/run_beta_sitl.py`](../scripts/run_beta_sitl.py) only when the external SITL layout already exists.

## What the package expects

`BetaAviary` is an environment wrapper that launches one Betaflight SITL instance per drone and connects to it over UDP. The external binaries are expected under a `betaflight_sitl/bfN/` layout, where `N` is the zero-based drone index.

Observed package behavior:

- `BetaAviary.__init__(...)` checks for each `bfN` directory and raises if it does not exist.
- The environment launches each SITL executable from `bfN/obj/main/betaflight_SITL.elf`.
- The example example workflow uses `CTBRControl` together with the BetaFlight state/RC packet mapping in `beta.py`.
- The package assets include `beta-traj.csv` and `eeprom.bin`; the example reads the trajectory CSV twice, once forward and once reversed.

## Port map

`BetaAviary` uses fixed base ports with a `+10 * drone_index` offset:

| Drone | PWM in | State out | RC out |
| --- | --- | --- | --- |
| 0 | 9002 | 9003 | 9004 |
| 1 | 9012 | 9013 | 9014 |
| 2 | 9022 | 9023 | 9024 |
| ... | ... | ... | ... |

The bundled layout checker reports these ports so a future agent can compare the expected map with the staged external build.

## Safe workflow order

1. Run the layout checker.
2. Confirm the external `betaflight_sitl/bfN` tree exists and contains `obj/main/betaflight_SITL.elf` for every requested drone.
3. Confirm the package assets `beta-traj.csv` and `eeprom.bin` are present in the installed package.
4. If the checker passes and the user explicitly wants execution, run the wrapper with `--execute`.
5. Keep `--gui` off for automation unless a display is available.

### Check-only example

```bash
python scripts/check_betaflight_layout.py --num-drones 2
```

Expected output: a JSON summary of the expected layout, present/missing files, the port map, and whether `gnome-terminal` is available.

### Execution example

```bash
python scripts/run_beta_sitl.py --execute --num-drones 2 --duration-sec 5 --output-folder /tmp/gpd-beta --no-gui
```

The execute path should still fail fast if the layout is missing, rather than trying to clone or build Betaflight inside the generated skill.

## How the source `clone_bfs.sh` script works

The source helper evidence shows a fixed external setup flow:

- clone Betaflight into a temporary directory,
- checkout a fixed commit used by the repo authors,
- patch a few SITL source lines,
- build the SITL target,
- copy the package's `eeprom.bin` into each `bfN` folder.

That workflow is useful as evidence, but it is intentionally not bundled here because it mutates an external repository and depends on host-specific build tools, a terminal launcher, and network access.

## Common use cases

- **Preflight for a local checkout**: run the checker, inspect the missing layout paths, then stage the external SITL tree in the location `BetaAviary` expects.
- **End-to-end execution**: only after the layout checker passes, run the wrapper in execute mode with the desired drone count.
- **Troubleshooting after a failed run**: compare the expected ports and `bfN` folders with the checker output, then fix the external build before retrying.
