---
name: gameplay-tasks
description: "Guides MaaNTE user-facing daily, city-tycoon, fishing, heist,
  coffee, reward, furniture, touch, divination, and character ability task
  workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: AGPL 3.0
---

# Gameplay Tasks

## Use This When

Use this sub-skill when the request is about MaaNTE's ordinary user-facing automation tasks, task presets, task options, or gameplay-specific failure modes.

Covered task families include:

- Fishing (`Fish`, `FishNew`), bait buying, fish selling, and fishing auto-navigation handoff.
- Coffee and coffee lite automation.
- Daily rewards and fountain check-in.
- City-tycoon income withdrawal, restock, product selection, and furniture collection.
- Pink Paw Heist routes, schemes, recovery, resolution, and combat/evacuation control.
- Bid King, Touch, Witch Divination, character ability/city ability sync, and presets.

Route navigation internals belong to [../navigation-realtime/SKILL.md](../navigation-realtime/SKILL.md); Python action mechanics belong to [../custom-actions/SKILL.md](../custom-actions/SKILL.md).

## Read First

1. [references/gameplay-workflows.md](references/gameplay-workflows.md) for task behavior and important options.
2. [references/heist-and-city-tycoon.md](references/heist-and-city-tycoon.md) for PinkPaw, city-tycoon, furniture, rewards, and sync details.
3. [references/troubleshooting.md](references/troubleshooting.md) for workflow-specific symptoms and fixes.
4. [../../references/task-catalog.md](../../references/task-catalog.md) for the repo-wide task table.

## Workflow Editing Strategy

- Start from the task JSON to learn user-visible options and controller restrictions.
- Find the task entry node and follow `next` branches through the relevant Pipeline files.
- If a node calls Python, switch to the custom-actions sub-skill for parameter parsing and runtime behavior.
- Preserve 1280×720 coordinates and task-specific controller restrictions.
- For gameplay task changes, prefer adding robust state recognitions and recovery branches over increasing retries.

## Common Safety/Runtime Warnings

- Many gameplay tasks require a live NTE game window and may carry account-risk implications. Keep the repo disclaimer visible in user-facing explanations.
- Foreground tasks can seize mouse/keyboard; tell users when `Win32-Front` is required.
- PinkPaw Heist is route/timing-sensitive and can hold movement/combat inputs. Stop-key setup and release logic are critical.
- Fishing and navigation features may be interrupted by popups, midnight/month-card prompts, wrong bait state, or route mismatch.
- Do not claim real task success from static checks. Use static checks for code correctness and live MaaFramework tests for gameplay behavior.

## Validation

Safe static checks:

```bash
python ../../scripts/inspect_task_catalog.py --repo-root .
python -m py_compile agent/custom/action/**/*.py
```

Live verification, when available, should be task-specific and bounded: a single reward claim, one fishing loop, one coffee loop, one heist dry-start/recovery check, or one manually controlled SceneManager route. Avoid long farming runs as validation unless the user explicitly asks.
