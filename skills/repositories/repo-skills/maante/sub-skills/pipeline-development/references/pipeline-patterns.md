# Pipeline Patterns

## Purpose

This reference distills MaaNTE's Pipeline JSON conventions for future edits. It does not require reading the original developer docs.

## Node Naming and Layout

- Use PascalCase node names with a task/module prefix, such as `FishNewCast`, `FurnitureGoHome`, or `RhythmPlaying`.
- Private SceneManager internals use `__ScenePrivate*`; task pipelines should call public interfaces instead.
- Complex workflows usually live in a folder under `assets/resource/base/pipeline/<Family>/` plus a task JSON in `assets/resource/tasks/`.
- Top-level single-file workflows exist for simple tasks such as `AutoFScroll.json` or `auto_piano.json`.

## Recognition Examples

### TemplateMatch

Use for fixed icons and buttons. Paths are relative to the resource image root.

```json
"recognition": {
  "type": "TemplateMatch",
  "param": {
    "template": "Fish/FishGeneralBait.png",
    "roi": [389, 293, 494, 135],
    "threshold": 0.8,
    "green_mask": true
  }
}
```

### OCR

Use full visible text where possible. MaaNTE often includes multiple languages and English regex entries.

```json
"recognition": {
  "type": "OCR",
  "param": {
    "roi": [663, 449, 237, 44],
    "expected": ["购买", "購買", "(?i)Purchase", "購入", "구매"],
    "threshold": 0.8
  }
}
```

### ColorMatch

Use for bars, cursor pixels, monsters, and minigame state when text/template recognition is poor.

```json
"recognition": {
  "type": "ColorMatch",
  "param": {
    "roi": [399, 43, 486, 14],
    "method": 40,
    "lower": [24, 64, 253],
    "upper": [30, 154, 255],
    "connected": true,
    "count": 20
  }
}
```

### Composite Checks

Use `And` to ensure both a scene and a task-specific UI are visible before acting.

```json
"recognition": {"type": "And", "param": {"all_of": ["InWorld", "FishSceneHookButton"]}}
```

## Action Examples

- `Click`: click the recognition result or explicit target.
- `ClickKey`: use virtual key codes such as 70 for F or 27 for Esc.
- `Swipe`: drag or scroll UI; movement tests also use it for camera/mouse behavior.
- `Custom`: call Python action by registered name.
- `DoNothing`: route or recognize without acting.
- `StopTask`: end a long-running task.

Custom action v2 form:

```json
"action": {
  "type": "Custom",
  "param": {
    "custom_action": "local_route_navigation",
    "custom_action_param": {"json_path": "penquan", "route_name": "penquan"}
  }
}
```

Older MaaNTE shorthand exists:

```json
"action": "Custom",
"custom_action": "auto_fish_without_cv"
```

Do not convert a whole file just for style unless that is the requested task.

## Flow Control

- `next`: ordered candidate list after the current node's action. First hit wins.
- `[JumpBack]SomeNode`: temporarily execute a helper/fallback branch, then return to the parent candidate list.
- `[Anchor]Name`: dynamic restart/callback target. Fishing and character sync use anchors.
- `on_error`: route when recognition/action fails or times out.
- `max_hit`: bounded loop counter; use sparingly and document the intent.

Good entry nodes include the main business branch plus scene recovery:

```json
"MyTaskEntry": {
  "next": [
    "MyTaskMainStep",
    "[JumpBack]SceneAnyEnterWorld",
    "[JumpBack]SceneClickBlankToExit",
    "[JumpBack]SceneLoading"
  ]
}
```

## SceneManager Rule

Use public interface nodes such as:

- `SceneAnyEnterWorld`
- `SceneAnyEnterEscMenu`
- `SceneAnyEnterCityTycoonsMenu`
- `SceneAnyEnterHethereauHobbiesMenu`
- `SceneAnyEnterBattlePassMenu`
- `SceneClickBlankToExit`
- `SceneLoading`
- status checks such as `InWorld`, `InCityTycoonMenu`, `InCharactersMenu`

If adding a new scene, create private implementation nodes under SceneManager and a public interface node under Interface/Scene. Then use only the public node in task flows.

## Delay Guidance

MaaFramework defaults can add waits when fields are omitted. For tight loops or pure checks:

```json
"rate_limit": 0,
"pre_delay": 0,
"post_delay": 0
```

For visual stability, prefer `pre_wait_freezes` or `post_wait_freezes` with a target ROI over arbitrary sleep. Some workflows still require short explicit delays for animation or key input; keep them local and documented.

## Common Pitfalls

- Option override targets a node that has been renamed.
- New OCR text is added in one language only.
- A task that needs foreground input is left visible for background controllers.
- An old shorthand node receives a nested override that does not match its actual structure.
- A fallback SceneManager branch is placed before the main business branch and steals control.
- A new template uses a screenshot at a non-720p scale.
