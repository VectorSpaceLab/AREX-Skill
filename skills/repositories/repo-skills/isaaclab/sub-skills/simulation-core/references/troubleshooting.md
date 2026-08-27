# Simulation Core Troubleshooting

## `KeyError: 'EXP_PATH'`

- **Likely cause:** a Kit-based script ran without the Isaac Sim environment being active.
- **Recovery:** launch through `./isaaclab.sh` or source the Isaac Sim environment before running the script.

## Invalid launcher values

- **Likely cause:** a malformed `--visualizer`, `--device`, or `--experience` value.
- **Recovery:** use comma-separated visualizer names, choose `cpu` or `cuda[:N]` for the device, and let the launcher resolve the default experience file when possible.

## Visualizer/backend conflicts

- **Likely cause:** `kit` visualizer was combined with `ovrtx` or `ovphysx`.
- **Recovery:** switch to a kitless visualizer such as `newton`, `rerun`, or `viser`, or choose a Kit-compatible backend.

## Headless confusion

- **Likely cause:** `--headless` and `--viz` were mixed in a way that hides the intended visualizer.
- **Recovery:** prefer omitting `--viz` for the normal headless path, or pass `--viz none` to disable visualizers explicitly.

## Camera renderers do not appear

- **Likely cause:** the script did not request camera rendering in a headless workflow.
- **Recovery:** enable camera rendering and re-check the selected visualizer/backend combination.

## Distributed device mismatch

- **Likely cause:** the requested CUDA device is incompatible with the visible device count.
- **Recovery:** use the bundled helper to inspect the resolved launcher settings and pick a valid CUDA device for the current process.
