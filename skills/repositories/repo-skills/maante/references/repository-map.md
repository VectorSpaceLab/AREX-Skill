# Repository Map and Extraction Scope

## When To Read

Read this when orienting in a MaaNTE checkout or deciding which sub-skill should own a change. It records the agent-confirmed extraction scope used to build this skill.

## Included Evidence Sources

| Source | Why it matters | Planned use in this skill |
| --- | --- | --- |
| `README.md` | Public project purpose, platform, feature list, disclaimer, resolution note. | Root purpose, runtime warnings, task-family inventory. |
| `AGENTS.md` | Repository coding rules, build/check commands, JSON/Python conventions, i18n and PR policies. | Maintainer guardrails in root and sub-skills. |
| `assets/interface.json` | Controller definitions, resource paths, agent child process, task import registry. | Runtime setup, controller notes, task catalog, registry checks. |
| `assets/resource/tasks/*.json` | User-facing tasks, option definitions, controller restrictions, pipeline overrides. | Task catalog, gameplay routes, pipeline-development reference. |
| `assets/resource/base/pipeline/**/*.json` | MaaFramework task graphs, recognition/action patterns, SceneManager, route/navigation entries. | Pipeline-development guidance and workflow-specific references. |
| `assets/resource/base/routes/*.json` | Local route examples for navigation. | Navi route schema and route validator helper. |
| `assets/resource/locales/interface/*.json` | Five-language UI labels/descriptions used by tasks. | i18n rules and troubleshooting. |
| `agent/main.py` | Runtime bootstrap, venv relaunch, AgentServer startup, logging, PI env behavior. | Setup/runtime and custom-action references. |
| `agent/custom/action/**/*.py` | CustomAction/CustomRecognition implementations, registries, route/nav/audio/minigame logic. | All sub-skill API and troubleshooting details. |
| `agent/utils/**/*.py` | Logger, maafocus, i18n, screen/window utilities. | Cross-cutting Python guidance. |
| `docs/zh_cn/develop/*.md` | Maintainer docs for pipeline, custom actions, SceneManager, route navigation, map teleport, node testing. | Distilled references; not linked as runtime dependencies. |
| `docs/zh_cn/introduction/*.md` | User-facing task behavior and option descriptions. | Gameplay/media task guidance. |
| `.claude/skills/*.md` | Existing repo-local guidance for logging, Pipeline, Python actions, task config, issue log analysis. | Reused as evidence and distilled into self-contained references. |
| `build.py`, `scripts/update_navi_coordinate_transform.py`, `tools/demo_coordinate_capture.py`, `tools/i18n/sync_ocr_expected.py` | Maintainer scripts and tool workflows. | Script import map and reference-only/adapted helper decisions. |

## Excluded or De-Prioritized Sources

| Source | Decision | Reason |
| --- | --- | --- |
| `.git/`, caches, `__pycache__/`, local virtual environments, build outputs | Exclude | Generated or machine-local; not useful runtime skill evidence. |
| `assets/resource/base/image/**` binary templates | Reference as assets, not deeply extracted | Large binary image corpus; paths matter but images are not copied into the skill. |
| `deps/`, `install/`, `install-mxu/`, vendored release/runtime outputs when present | Exclude | Build/runtime artifacts rather than reusable guidance. |
| Network downloads in `build.py` | Reference-only | Useful release workflow, but running it can download large binaries. |
| `tools/i18n/sync_ocr_expected.py` full JSONC implementation | Reference-only | Large specialized tool with external localization-data expectations; summarized instead of copied. |
| `tools/demo_coordinate_capture.py` live capture | Reference-only | Requires Windows coordinate `.pyd`, game/runtime, and capture backend. A safe route validator is bundled instead. |
| Manual Maa Pipeline Support node tests | Reference-only | Require a developer IDE/plugin and live game state. |

## Source Script Inventory Decisions

| Source artifact | Workflow/capability | Decision | Bundled replacement | Rationale |
| --- | --- | --- | --- | --- |
| `build.py` | Release packaging | Reference-only | `references/setup-and-runtime.md` | It performs downloads and release assembly; not safe as a bundled helper. |
| `scripts/update_navi_coordinate_transform.py` | Navi calibration fitting | Reference-only | `sub-skills/navigation-realtime/references/navi-workflows.md` | It mutates source constants and depends on calibration files; future agents need the procedure more than a second copy. |
| `tools/demo_coordinate_capture.py` | Coordinate capture smoke/demo | Reference-only | `sub-skills/navigation-realtime/references/navi-workflows.md` | Requires Windows `.pyd` ABI and game capture; not safe for generic execution. |
| `tools/i18n/sync_ocr_expected.py` | OCR expected text localization sync | Reference-only | `sub-skills/pipeline-development/references/task-config-and-i18n.md` | Large parser tied to external localization exports; keep workflow guidance. |
| Task catalog inspection from repo JSON | Safe metadata check | Adapt | `scripts/inspect_task_catalog.py` | Small deterministic checker; helps future agents inspect task/import consistency. |
| Dependency/backend inspection | Safe environment check | Adapt | `scripts/check_maante_environment.py` | Small deterministic import/provider checker with graceful optional-backend warnings. |
| Custom action registry matching | Safe source scan | Adapt | `sub-skills/custom-actions/scripts/check_custom_action_registry.py` | Detects missing action imports or Pipeline references without running Maa. |
| Route JSON parsing | Safe data-format check | Adapt | `sub-skills/navigation-realtime/scripts/validate_route_json.py` | Validates route schemas and point conversion shapes without live navigation. |
| MIDI metadata inspection | Safe tiny fixture/helper | Adapt | `sub-skills/media-minigames/scripts/check_midi_file.py` | Lets future agents check AutoPiano input files without running game input. |

## Sub-Skill Ownership

- `pipeline-development`: Pipeline JSON, task config JSON, SceneManager interfaces, i18n, formatting, and registry updates.
- `custom-actions`: Python action architecture, MaaFramework bindings, logging/maafocus, controller calls, action/recognition registration, and source scanning.
- `gameplay-tasks`: ordinary gameplay and daily/city-tycoon/heist task behavior and option semantics.
- `navigation-realtime`: real-time assistance, map teleport, local route navigation, OnlineMapNavigation WebSocket service, coordinate capture, movement tests, and dataset collection.
- `media-minigames`: audio and media-style automation: SoundDodge, Rhythm, AutoPiano, Tetris, BagelSpam, AutoFScroll.
