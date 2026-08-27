---
name: mobile-agent
description: "Operate the MobileAgent repository family: GUI-Owl/Mobile-Agent
  v3.5, Mobile-Agent-E, PC-Agent, legacy mobile agents, GUI benchmarks,
  GUI-Critic, and UI-S1 post-training workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# MobileAgent Repo Skill

Use this repo skill when a task involves the MobileAgent / GUI-Owl family of GUI agents, benchmarks, desktop/mobile/browser automation, GUI-Critic-R1, or UI-S1 GUI trajectory training. This skill is a router plus safety gate: choose the nearest sub-skill, then use that sub-skill's references and bundled scripts.

The generated skill is self-contained for operating guidance. It can build commands for a user-provided MobileAgent deployment checkout, validate configs/data, and explain backend requirements; it does not require the original construction checkout to be present.

## First decision: which family?

| User task | Read this |
|---|---|
| Run or debug current GUI-Owl / Mobile-Agent-v3.5 on Android, desktop, or browser | [`sub-skills/current-gui-owl/SKILL.md`](sub-skills/current-gui-owl/SKILL.md) |
| Build AndroidWorld, OSWorld, WebArena/WebVoyager/VisualWebArena, grounding, knowledge, or GUI-Critic evaluation commands | [`sub-skills/benchmarks-and-evaluation/SKILL.md`](sub-skills/benchmarks-and-evaluation/SKILL.md) |
| Use Mobile-Agent-E for individual tasks, task lists, self-evolution, persistent tips, shortcuts, or Mobile-Eval-E-style JSON | [`sub-skills/mobile-agent-e/SKILL.md`](sub-skills/mobile-agent-e/SKILL.md) |
| Use PC-Agent for desktop automation with SoM/OCR/accessibility on Mac or Windows | [`sub-skills/pc-agent/SKILL.md`](sub-skills/pc-agent/SKILL.md) |
| Preserve, run, or migrate Mobile-Agent v1/v2/v3 legacy mobile workflows | [`sub-skills/legacy-agents/SKILL.md`](sub-skills/legacy-agents/SKILL.md) |
| Prepare UI-S1 / verl post-training, SOP evaluation, GUI trajectory JSONL, checkpoint merge, or vLLM/Ray/GRPO commands | [`sub-skills/ui-s1-training/SKILL.md`](sub-skills/ui-s1-training/SKILL.md) |

If a prompt names only "MobileAgent" and a platform, prefer the current v3.5 GUI-Owl route unless the prompt explicitly says Mobile-Agent-E, PC-Agent, UI-S1, GUI-Critic-R1, AndroidWorld/OSWorld/WebArena, or v1/v2/v3.

## Safety and verification rules

- Do not silently run live Android, desktop, browser, API, benchmark, training, checkpoint, or upload workflows. These routes can control external devices, call paid APIs, mutate screens, require login cookies, or use multi-GPU resources.
- Use bundled command builders first. They print commands and warnings; they do not connect to ADB/HDC, launch browsers/desktops, call model APIs, train, evaluate, or upload checkpoints.
- Keep credentials in environment variables or private config files. Never paste raw API keys into generated commands or review artifacts.
- Do not install all requirement files into one global environment. MobileAgent is a monorepo with conflicting/large stacks. Read [`references/environment-matrix.md`](references/environment-matrix.md) before installing.
- For cross-cutting failures, read [`references/troubleshooting.md`](references/troubleshooting.md). Each sub-skill also has route-specific troubleshooting.

## Common entry scripts

Run these from the generated skill directory or pass an explicit path:

```bash
python scripts/check_prerequisites.py --route current-gui-owl --route benchmarks
python scripts/check_mobile_agent_artifacts.py --skill-dir .
```

`check_prerequisites.py` reports host-level prerequisites for selected routes without running the routes. `check_mobile_agent_artifacts.py` performs static self-containment/frontmatter/link/privacy checks for this generated skill tree.

## Version and environment references

- Read [`references/version-and-family-map.md`](references/version-and-family-map.md) when choosing between v3.5, v3, v2, v1, Mobile-Agent-E, PC-Agent, GUI-Critic-R1, and UI-S1.
- Read [`references/environment-matrix.md`](references/environment-matrix.md) before preparing a runtime checkout or deciding whether CPU-only validation is enough.
- Read [`references/repo-provenance.md`](references/repo-provenance.md) to compare this skill against the source commit and evidence paths used at construction time.

## Handoff boundary

This skill is intended for Researcher-mode operating use. Creator-mode construction artifacts, usability cases, and verification reports live outside the runtime tree. The user requested no import during creation, so a later user must explicitly import or load this repo-local skill before expecting automatic router selection in a new session.
