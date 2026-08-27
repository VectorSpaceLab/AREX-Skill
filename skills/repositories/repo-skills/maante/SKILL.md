---
name: maante
description: "Repo-specific operating guidance for MaaNTE Neverness to Everness
  MaaFramework automation tasks, pipeline JSON, Python custom actions,
  navigation, audio, minigame, and maintainer workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: AGPL 3.0
---

# MaaNTE Repo Skill

## Purpose

Use this repo skill when working on MaaNTE, a MaaFramework-based automation assistant for Neverness to Everness (异环 / NTE). It helps future agents understand the repository's task catalog, Pipeline JSON conventions, Python CustomAction/CustomRecognition code, real-time navigation stack, audio and rhythm automation, packaging expectations, and common troubleshooting paths without reopening the original source documentation.

MaaNTE automates a live Windows game through image/OCR/color recognition and simulated input. Always respect the repository's disclaimer and user intent: keep changes limited to normal gameplay automation, do not help modify game files, bypass protections, or create unfair/unsafe tooling, and call out account-risk implications when relevant.

## First Checks

1. Confirm the working tree is a MaaNTE checkout by checking for `assets/interface.json`, `agent/main.py`, `assets/resource/tasks/`, and `assets/resource/base/pipeline/`.
2. Read [references/repo-provenance.md](references/repo-provenance.md) before relying on version-sensitive details; refresh this skill if the current checkout differs materially from the recorded snapshot.
3. For installation, build, and runtime constraints, read [references/setup-and-runtime.md](references/setup-and-runtime.md).
4. Run the safe environment/catalog helpers when useful:
   - `python scripts/check_maante_environment.py --summary`
   - `python scripts/inspect_task_catalog.py --repo-root <checkout>`
5. Choose the focused sub-skill below; do not keep all detailed context in the root.

## Sub-Skill Routing

| Need | Read |
| --- | --- |
| Add or modify Pipeline JSON nodes, task option JSON, i18n keys, controller restrictions, SceneManager routes, or JSON formatting | [sub-skills/pipeline-development/SKILL.md](sub-skills/pipeline-development/SKILL.md) |
| Add or modify Python CustomAction/CustomRecognition classes, action registration, MaaFramework Python APIs, logging, maafocus messages, controller input, or runtime state | [sub-skills/custom-actions/SKILL.md](sub-skills/custom-actions/SKILL.md) |
| Understand or edit user-facing gameplay tasks such as fishing, coffee, rewards, fountain check-in, city-tycoon income/restock, furniture, bid king, pink paw heist, presets, touch, or character ability sync | [sub-skills/gameplay-tasks/SKILL.md](sub-skills/gameplay-tasks/SKILL.md) |
| Work on local route navigation, map teleport, online map WebSocket broadcasting, coordinate capture, real-time assistance, movement tests, or dataset collection | [sub-skills/navigation-realtime/SKILL.md](sub-skills/navigation-realtime/SKILL.md) |
| Work on sound dodge/counter, rhythm game, auto piano MIDI playback, Tetris AI, BagelSpam posting, or AutoFScroll pickup automation | [sub-skills/media-minigames/SKILL.md](sub-skills/media-minigames/SKILL.md) |

## Repo-Level Rules to Keep in Mind

- Runtime assets assume a 1280×720 game window. Pipeline coordinates, ROI rectangles, click targets, and screenshots are all designed for that baseline.
- MaaNTE uses MaaFramework Pipeline v2 style in newer nodes: nested `recognition: {type, param}` and `action: {type, param}`. Some older nodes still use flat shorthand; preserve local style unless refactoring the whole node family.
- Prefer recognition-driven transitions: identify a screen state, act once, then recognize again. Avoid blind multi-click chains and broad retry loops.
- Explicitly set `rate_limit: 0`, `pre_delay: 0`, and `post_delay: 0` when a node truly needs no default MaaFramework waits.
- Public SceneManager interfaces live under `Interface/Scene/`; task pipelines should not jump directly to private `__ScenePrivate*` nodes.
- Python actions are for logic that Pipeline cannot express. Register actions with `@AgentServer.custom_action("snake_case_name")` or recognitions with `@AgentServer.custom_recognition("snake_case_name")`, then import them in `agent/custom/action/__init__.py`.
- User-facing messages from Python should go through `utils.maafocus.Print()` or `PrintT()`. Use `utils.logger` for developer/debug logging; avoid raw `print()` in user-facing actions.
- Long-running loops must check `context.tasker.stopping` and release held keys/buttons in `finally` blocks.
- New or changed tasks usually require updates in: a task JSON file, one or more Pipeline JSON files, five interface locale files, and `assets/interface.json` imports.

## Installation and Validation Summary

Use Python 3.11+ for development. The runtime package set is requirements-driven and includes MaaFramework (`maafw`), OpenCV/Pillow/NumPy/SciPy/scikit-learn, librosa/soundcard/mido for audio/MIDI workflows, onnxruntime-directml for Windows DirectML navigation inference, networking packages for coordinate capture and WebSocket routes, and build packaging utilities.

Common safe checks:

```bash
python -m py_compile agent/custom/action/**/*.py
python scripts/check_maante_environment.py --summary
python scripts/inspect_task_catalog.py --repo-root .
```

Full UI/node validation still depends on Maa Pipeline Support, a Windows game window, MaaFramework resources, and the chosen Win32 controller mode. Do not claim real gameplay verification from Linux-only import checks.

## References

- [references/repository-map.md](references/repository-map.md) summarizes the repo layout and selected extraction scope.
- [references/setup-and-runtime.md](references/setup-and-runtime.md) covers installation, build modes, controller/runtime assumptions, and backend notes.
- [references/task-catalog.md](references/task-catalog.md) maps MaaNTE task families, entries, options, and controllers.
- [references/maa-framework-patterns.md](references/maa-framework-patterns.md) records verified MaaFramework Python binding facts and Pipeline semantics used across sub-skills.
- [references/troubleshooting.md](references/troubleshooting.md) covers cross-cutting failures: imports, paths, controller modes, resolution, OCR/assets, optional backends, and logs.
- [references/repo-routing-metadata.json](references/repo-routing-metadata.json) is structured metadata for managed repo-skill router import.
