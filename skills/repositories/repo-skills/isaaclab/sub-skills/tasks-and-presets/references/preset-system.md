# Preset System

## Core idea

Isaac Lab uses a Hydra-driven preset system so task authors can swap physics backends, renderers, and domain variants from the command line without editing Python code. Presets are declared as `PresetCfg` objects and resolved before the final environment config is used.

## Selector grammar

Accepted typed tokens have no leading dashes:

- `physics=NAME` selects a `PhysicsCfg` variant.
- `renderer=NAME` selects a `RendererCfg` variant.
- `presets=NAME[,NAME,...]` broadcasts one or more domain presets to every matching `PresetCfg` field.

Hydra path overrides still work, for example `env.sim.dt=0.001` or a path-targeted preset such as `env.sim.physics=NAME`.

## Public objects

- `PresetCfg` — base class for declarative preset definitions. The `default` field is the fallback; other fields are named alternatives.
- `preset(**options)` — convenience factory for scalar preset groups; `default` is required.
- `PresetTarget` — enum that owns the typed selector categories and legacy aliases.
- `setup_preset_cli(parser, argv=None)` — attaches help text and returns `(args, remaining)` without mutating `sys.argv`.
- `enumerate_task_presets(task_name)` — returns preset groups keyed by `PresetTarget`, or `None` when a config cannot be loaded.
- `collect_presets(cfg)` and `resolve_presets(cfg, ...)` — resolver helpers used by task registration and config loading.

## Important behavior

- `setup_preset_cli` does not register `physics`, `renderer`, or `presets` as argparse options. The parsed namespace intentionally has no preset attributes, so preset names cannot leak into `AppLauncher`'s SimulationApp config forwarding.
- The returned `remaining` tokens must be assigned to `sys.argv` by the caller when Hydra should parse them.
- Typed selector values are passed through verbatim until Isaac Lab's resolver checks whether the names are valid.
- Deprecated physics aliases exist: `newton` maps to `newton_mjwarp`, and `kamino` maps to `newton_kamino` when the canonical replacements are available.
- The resolver uses replacement semantics for preset sections rather than Hydra's default merge semantics.

## Typical parser wiring

1. Create the script parser and add script-specific args.
2. Add launcher args through the task utility or AppLauncher helper.
3. Call `setup_preset_cli(parser)`.
4. Optionally intersect or filter the returned `remaining` list for an external callback.
5. Set `sys.argv = [sys.argv[0]] + remaining` before Hydra registration.

## Example selector combinations

```bash
./isaaclab.sh train --rl_library rsl_rl --task Isaac-Ant-v0 physics=newton_mjwarp
./isaaclab.sh train --rl_library rl_games --task Isaac-Cartpole-Camera-Presets-Direct-v0 --enable_cameras renderer=newton_renderer
./isaaclab.sh train --rl_library rl_games --task Isaac-Cartpole-Camera-Presets-Direct-v0 --enable_cameras physics=newton_mjwarp renderer=newton_renderer presets=rgb
```

For observation-mode presets, train and play must use the same preset when the preset changes the observation tensor structure; otherwise checkpoint loading can fail with a model-architecture mismatch.
