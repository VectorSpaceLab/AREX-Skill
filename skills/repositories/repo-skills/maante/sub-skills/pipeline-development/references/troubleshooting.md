# Pipeline Troubleshooting

## Missing or Misrouted Node

Symptoms:

- MaaFramework reports a node is missing.
- The task immediately exits or falls through to an unexpected branch.
- A task option appears to have no effect.

Likely causes:

- `entry` or `next` names do not match the actual node keys.
- `assets/interface.json` does not import the task file.
- An option's `pipeline_override` targets the old node name after a rename.

Actions:

- Run the bundled task catalog inspector.
- Search the matching Pipeline file for the target node key before editing the task JSON.
- Check for stale anchor names and private SceneManager references.

## OCR or Template Mismatch

Symptoms:

- Recognition loops until timeout.
- Button/text is visible but the node never hits.
- A task breaks after a UI refresh or language change.

Likely causes:

- ROI is too small or wrong for the visible state.
- OCR `expected` is partial, untranslated, or mismatched with the current locale.
- Template image was cropped at the wrong scale or the game is not 1280×720.

Actions:

- Verify the live screenshot and adjust ROI before changing thresholds.
- Update all five locale files for user-visible text changes.
- Only use regex/partial OCR when the repo already expects that style.

## Controller Mode Problems

Symptoms:

- A task only works in the foreground but is still marked for background use.
- Mouse or keyboard actions fail on a specific controller.

Likely causes:

- The task JSON's `controller` restriction no longer matches runtime behavior.
- The action assumes seize/foreground behavior and cannot run in the requested mode.

Actions:

- Keep the task restricted to the modes that are actually supported.
- Update user-facing docs when a task requires `Win32-Front`.

## Delay and Loop Problems

Symptoms:

- A loop feels sluggish.
- A task hangs between states.
- A node seems to re-run too quickly or too slowly.

Likely causes:

- Implicit MaaFramework waits because `rate_limit`, `pre_delay`, or `post_delay` were omitted.
- `next` order hides the intended fast path.
- `max_hit` was used to mask a missing state transition.

Actions:

- Make explicit zero-delay intent visible.
- Replace hidden retry loops with dedicated status nodes.
- Use `pre_wait_freezes`/`post_wait_freezes` only where animation stabilization is needed.

## SceneManager Problems

Symptoms:

- A task cannot return to the correct parent scene.
- The public scene interface works in one place but not another.
- A pipeline references `__ScenePrivate*` directly and later breaks after an update.

Actions:

- Use public `Interface/Scene/` nodes only.
- Add or fix the underlying scene status node if a jump-back branch cannot resolve.
- Re-check the route order so that generic scene exits do not steal control from business nodes.
