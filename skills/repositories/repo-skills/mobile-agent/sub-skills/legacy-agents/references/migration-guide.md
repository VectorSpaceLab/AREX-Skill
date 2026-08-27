# Legacy Migration Guide

## v1/v2 to current v3.5

Use current GUI-Owl v3.5 for new Android tasks when the user does not need exact legacy reproduction.

Migration steps:

1. Preserve the natural-language `instruction`.
2. Move useful `add_info` or operational hints into v3.5 `--add_info`.
3. Replace raw API/token fields with env vars used by current command builders.
4. Re-check ADB path/device and ADB Keyboard.
5. Validate the current route before live execution with `current-gui-owl/scripts/validate_gui_owl_config.py`.

## v2 reflection/memory to Mobile-Agent-E

Do not automatically route v2 memory/reflection to Mobile-Agent-E. Use Mobile-Agent-E only when the user wants persistent cross-task evolution or shared tips/shortcuts across a task sequence. For one-off hints, keep current GUI-Owl `--add_info`.

## v3 to v3.5

- Android v3 maps cleanly to v3.5 mobile for most new tasks.
- HarmonyOS/HDC remains a legacy v3 route unless the user changes platform.
- `coor_type qwen-vl` indicates 0-1000 relative coordinates. Current GUI-Owl v3.5 also expects normalized coordinates internally, but do not assume every legacy output grammar is identical.
- `notetaker` should become explicit task instructions/additional hints unless the new route has a memory mechanism.

## When not to migrate

- The user must reproduce an old published result/log exactly.
- The user depends on v1 hosted session semantics.
- The user uses HarmonyOS/HDC and v3.5 route lacks equivalent support.
- The old workflow's local perception stack is the object of investigation.
