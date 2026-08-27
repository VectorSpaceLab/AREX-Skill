---
name: legacy-agents
description: "Preserve, run, and migrate legacy Mobile-Agent v1, v2, and v3
  mobile workflows with hosted/local route selection, ADB/HDC handling,
  coordinate-mode notes, and safe command builders."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Legacy Mobile-Agent v1/v2/v3

Use this sub-skill when a task names Mobile-Agent v1, v2, or v3; asks to preserve or migrate an old mobile workflow; mentions hosted v1 API, local v1 perception stack, edited v2 settings, HarmonyOS/HDC, `coor_type`, or `notetaker`.

## Route map

| Prompt signal | Workflow | Read / run |
|---|---|---|
| v1 hosted service, `run_api.py`, URL/token | v1 API route | [`references/legacy-mobile-workflows.md`](references/legacy-mobile-workflows.md), `scripts/build_legacy_mobile_command.py --version v1-api` |
| v1 local GroundingDINO/OCR/CLIP stack | v1 local route | same reference, command builder `--version v1-local` |
| v2 `run.py` edited settings, reflection/memory, caption model/API | v2 preservation/migration | [`references/version-map.md`](references/version-map.md), validator script |
| v3 Android/HarmonyOS, ADB/HDC, `coor_type qwen-vl`, `notetaker` | v3 route | command builder `--version v3-android` or `v3-harmony` |
| Move old tasks to v3.5 or Mobile-Agent-E | Migration | [`references/migration-guide.md`](references/migration-guide.md) |
| Device/API/typing/coordinate pitfalls | Troubleshooting | [`references/troubleshooting.md`](references/troubleshooting.md) |

## Safe workflow

1. Validate any structured notes for the old workflow:

```bash
python sub-skills/legacy-agents/scripts/validate_legacy_mobile_config.py --config legacy_config.json
```

2. Build a safe command. Hosted v1 example:

```bash
python sub-skills/legacy-agents/scripts/build_legacy_mobile_command.py \
  --version v1-api \
  --instruction "Open Notes and write a reminder" \
  --adb-path-env ADB_PATH \
  --url-env MOBILE_AGENT_V1_URL \
  --token-env MOBILE_AGENT_V1_TOKEN
```

3. For v2, the builder prints `python run.py` plus a warning because v2 stores runtime settings in top-of-file variables rather than CLI flags.

4. For v3 HarmonyOS, use HDC and do not include ADB:

```bash
python sub-skills/legacy-agents/scripts/build_legacy_mobile_command.py \
  --version v3-harmony \
  --instruction "Remember this address" \
  --hdc-path-env HDC_PATH \
  --api-key-env GUI_API_KEY \
  --base-url-env GUI_BASE_URL \
  --model-env GUI_MODEL \
  --coor-type qwen-vl \
  --notetaker
```

## Boundaries

- New GUI-Owl v3.5 phone/desktop/browser work belongs to [`../current-gui-owl/SKILL.md`](../current-gui-owl/SKILL.md) after migration.
- Persistent cross-task evolution belongs to [`../mobile-agent-e/SKILL.md`](../mobile-agent-e/SKILL.md).
- AndroidWorld/OSWorld benchmark evaluation belongs to [`../benchmarks-and-evaluation/SKILL.md`](../benchmarks-and-evaluation/SKILL.md).

Do not install legacy local model stacks unless exact reproduction requires them. Prefer hosted v1 or current v3.5 for new work.
