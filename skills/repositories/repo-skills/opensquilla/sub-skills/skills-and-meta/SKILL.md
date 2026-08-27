---
name: skills-and-meta
description: "Use this OpenSquilla sub-skill for skill catalog management,
  Community skill installs and updates, taps, meta-skill inspection,
  run/proposal review, and the built-in meta-skill creator workflow."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Skills and Meta-Skills

Use this sub-skill when the task is about OpenSquilla's bundled or managed
Skill system and MetaSkill runtime: discovery, eligibility, routing, provenance,
install/update/uninstall, taps, publication, compiled meta-skill inspection,
meta-run history, proposals, and creator/authoring workflows.

## Route Here For

- Listing, searching, viewing, diagnosing, installing, updating, reloading,
  uninstalling, publishing, inspecting, or tapping Skill sources.
- Understanding why a Skill was or was not selected: eligibility, disabled
  config, shadowing, optional dependency readiness, runtime visibility, and
  provenance.
- Inspecting or running MetaSkill workflows through the supported `/meta`
  surfaces, or inspecting their compiled composition from the CLI.
- Reviewing MetaSkill run history, replay shape, validation metadata, costs,
  failures, proposals, gates, and proposal acceptance.
- Creating a new MetaSkill proposal with the bundled `meta-skill-creator`,
  including trigger boundaries, composition, validation gates, and proposal
  review.

## Use These References

- [Command catalog](references/command-catalog.md) for `opensquilla skills ...`,
  `opensquilla skills meta ...`, taps, publish, inspect, and automation notes.
- [Routing and eligibility](references/routing-and-eligibility.md) for catalog
  layers, shadowing, identity, instruction-only Community projection, disabled
  Skills, and selection diagnostics.
- [MetaSkill workflows](references/meta-skill-workflows.md) for `/meta`, built-in
  workflows, creator proposal flow, authoring frontmatter, composition, template
  safety, and meta-skill config switches.
- [Troubleshooting](references/troubleshooting.md) for install conflicts, scanner
  confirmation, reload/catalog differences, compile failures, trigger
  collisions, recursion guards, proposal mistakes, and tap/source issues.

A bundled read-only helper is available at
[scripts/skills_meta_health.py](scripts/skills_meta_health.py) for quick local
Skill/MetaSkill health snapshots.

## Operating Rules

1. Start with read-only observations unless the user explicitly asks to mutate
   the catalog: `skills list`, `skills view`, `skills doctor`, `skills inspect`,
   `skills meta runs ...`, and `skills meta proposals list/show`.
2. Treat `install`, `update`, `uninstall`, `reload`, `publish`, and proposal
   `accept` as state-changing. Confirm the source, install identity, target,
   and risk trade-off before taking those actions.
3. Use exact managed identity (`--install-id`) when a runtime name is ambiguous,
   shadowed, or shared by more than one installed package.
4. Do not claim that Community Skill installation installs runtime dependencies;
   installation commits instruction content and provenance. Use Doctor/readiness
   output to decide whether setup is still required.
5. For MetaSkills, remember the default launch model: users deliberately launch
   with `/meta` and `/meta <name>` on supported surfaces. Natural-language
   auto-triggering is compatibility mode only when enabled in config.
6. Use `meta-skill-creator` only when the user explicitly wants a new
   multi-step MetaSkill composition. Do not use it for normal standalone Skill
   creation, pasted catalog analysis, or questions about how MetaSkills work.
7. Keep MetaSkill proposals review-first: inspect gates and `SKILL.md`, check
   trigger collisions and risk metadata, and accept only after the requested
   review level is satisfied.

## Route Elsewhere

- General chat automation, sessions, history export, diagnostics toggles,
  replay outside the MetaSkill run-history surface, migration, cron, memory, and
  uninstall safety: [cli-and-automation](../cli-and-automation/SKILL.md).
- Provider selection, model catalog, router modes, search-provider setup, API
  keys, and model/base-url precedence: [configuration-and-routing](../configuration-and-routing/SKILL.md).
- Web/TUI/desktop launch context, including where `/meta` is surfaced in the UI:
  [tui-and-desktop](../tui-and-desktop/SKILL.md).
- Messaging channels and MCP bridge behavior: [channels-and-integrations](../channels-and-integrations/SKILL.md).
- First-run install, gateway lifecycle, Web UI basics, and generic gateway
  readiness: [setup-and-gateway](../setup-and-gateway/SKILL.md).
