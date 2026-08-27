---
name: simulation-environments
description: "The simulation-environments skill guides users through creating,
  stepping, inspecting, rendering, resetting, and closing isolated IR-SIM
  environments in 2D, 3D, headless, and externally controlled workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Simulation environments

Use this sub-skill when the task is to run IR-SIM, choose a YAML world, control
its lifecycle, use internal or external state advancement, render safely, or
run more than one environment. Keep scene YAML/object schemas in
[scene-configuration](../scene-configuration/SKILL.md), sensor and map payloads
in [sensing-and-mapping](../sensing-and-mapping/SKILL.md), planners and
behaviors in [navigation-and-planning](../navigation-and-planning/SKILL.md),
and custom controllers/registries or live GUI input in
[extension-and-control](../extension-and-control/SKILL.md).

## Fast route

1. Install the base package and verify `import irsim`; add `pynput` only for
   live keyboard input and `imageio[ffmpeg]` only for video output. No GPU is
   required for the covered workflows.
2. Start from a self-contained YAML path: `env = irsim.make("world.yaml",
   display=False, seed=7)` for batch/headless work, or omit `display=False`
   only when a supported desktop backend is intended.
3. Run `env.step()` then `env.render()` in internal mode, check `env.done()`,
   and always call `env.close(ending_time=0)` in a `finally` block. Use
   `scripts/render_smoke.py --help` for a safe, tiny, arbitrary-cwd check.
4. Select `step_mode="external"` when another system owns state. Mutate every
   relevant object's state and velocity, call `env.step()` **without** an
   action, and use `env.refresh()` when a direct mutation needs derived data
   immediately.
5. Read the linked references for exact signatures, reset/reload semantics,
   action alignment, multi-environment/RNG caveats, and optional rendering.

## Scope boundary

This skill covers `irsim.make`, `EnvBase`/`EnvBase3D`, clocks and statuses,
headless rendering and figure output, lifecycle cleanup, query/draw helpers,
seed handling, and isolated environment instances. It does not define the
full YAML object schema, sensor array formats, planner contracts, or extension
registration APIs; follow the cross-links above instead.

## Evidence and limits

The operating guidance is based on the IR-SIM 2.10.2 public entry point and
environment/plot implementations, the English quick-start, environment,
multiple-environment, and animation documentation, and focused lifecycle and
plot test evidence. Interactive keyboard events, desktop windows, MP4/ffmpeg,
and long visual demos are intentionally not bundled or claimed as verified.
The helper adapts only a tiny headless render and does not depend on an
original checkout file.
