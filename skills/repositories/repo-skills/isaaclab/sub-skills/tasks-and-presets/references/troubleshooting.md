# Tasks and Presets Troubleshooting

## `Key 'physics' is not in struct`

- **Likely cause:** the script forwarded `physics=...` to Hydra as a raw struct override instead of letting Isaac Lab's preset resolver consume it.
- **Recovery:** call `setup_preset_cli` after registering launcher and script args, then assign the returned `remaining` list to `sys.argv` before Hydra registration.

## `Unknown preset(s): NAME`

- **Likely cause:** the selector reached the Isaac Lab resolver, but the requested name is not available for that task or selector type.
- **Recovery:** list valid preset names for the task, then switch to a canonical selector such as `physics=newton_mjwarp` instead of a deprecated alias.

## Missing task ID

- **Likely cause:** the task package was not imported, an experimental task package is missing, or the task name was mistyped.
- **Recovery:** import `isaaclab_tasks`, optionally import `isaaclab_tasks_experimental`, then list registry entries filtered by keyword.

## Config loading imports `pxr`, `omni`, `carb`, `isaacsim`, or `scipy`

- **Likely cause:** a config module imports simulator/runtime code at module import time.
- **Recovery:** move the import under a local function, guard annotation-only imports with `TYPE_CHECKING`, use lazy package exports, or store the callable as a string reference that is resolved after launch.

## Observation preset checkpoint mismatch

- **Likely cause:** training used one observation preset and play used another, changing the policy input shape.
- **Recovery:** replay with the same observation preset token that was used during training, for example `presets=rgb` on both train and play.

## `enumerate_task_presets` returns unavailable

- **Likely cause:** the task config could not be loaded in the current environment, commonly because optional task dependencies are missing.
- **Recovery:** verify package installation with the root install helper, install the required optional package or extra, and retry with a narrower `--keyword` to isolate the failing task.
