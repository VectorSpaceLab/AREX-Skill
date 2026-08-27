# Cross-cutting Newton troubleshooting

## Start here

1. Run `python scripts/check_newton_env.py --show-optional` from this generated skill directory.
2. Run `python scripts/newton_smoke.py --device cpu --steps 2` to prove base modeling/solver viability.
3. Route the failure to the nearest sub-skill:
   - Model/state/contact loop: `sub-skills/modeling-simulation/SKILL.md`.
   - Solver/contact tuning: `sub-skills/solvers-contacts/SKILL.md`.
   - URDF/MJCF/USD/mesh import: `sub-skills/asset-import-export/SKILL.md`.
   - Actuators/controllers/IK/policies: `sub-skills/robotics-control/SKILL.md`.
   - Sensors/viewers/examples: `sub-skills/sensors-visualization/SKILL.md`.

## Newton or Warp is not importable

- Install the base package first: `pip install newton`.
- If `warp-lang` cannot be resolved, use the package's documented NVIDIA index path for Warp wheels.
- Avoid mixing global Python, conda base, and project virtual environments.
- Re-run `check_newton_env.py` with the same Python that will execute the user's code.

## Optional workflow fails after base import succeeds

A successful base import does not imply every extra is installed. Match the missing module to the smallest extra:

- `mujoco`, `mujoco_warp`: `newton[sim]`.
- `pxr`, `newton_usd_schemas`, mesh-processing modules: `newton[importers]`.
- `open3d`, `pyfqmr`: `newton[remesh]` or an importer extra where supported.
- `warp_nn`, `onnx`: `newton[onnx]`.
- `torch`: `newton[torch-cu12]` or `newton[torch-cu13]` chosen for the user's CUDA/Python stack.
- `pyglet`, `imgui_bundle`: `newton[examples]`.
- `ovrtx`: `newton[rtx]`.
- `viser`, notebook/Rerun support: `newton[notebook]` or explicit visualization packages.

## CPU works but CUDA does not

- Confirm the task actually requires CUDA. Many public API checks and small simulations can run on CPU.
- Run `check_newton_env.py --require-cuda`.
- Check that the NVIDIA driver is visible inside the current environment/container.
- Do not install Torch CUDA wheels just to fix Warp CUDA unless the task requires Torch.
- Treat RTX and Torch policy workflows as separate optional backends.

## Example CLI fails

Use the package CLI shape:

```bash
python -m newton.examples --list
python -m newton.examples basic_pendulum --viewer null --device cpu --test
```

If an example is unknown, list examples first. If an example imports optional dependencies, install the matching extra or choose a simpler CPU/base example for smoke testing.

## Runtime instructions must stay public

When using this skill, do not ask future agents to import `newton._src` or to open original repository docs/examples/tests. The generated references and scripts contain distilled public guidance; if they are stale, refresh the repo skill from the current checkout.

## When to stop and ask

Stop instead of guessing when the user task requires:

- Network downloads, private assets, credentials, or external services.
- Installing broad extras or mutating a user-owned environment.
- GPU/RTX/Torch behavior on hardware that is unavailable or incompatible.
- Changing public Newton API behavior without following repository maintenance conventions.
