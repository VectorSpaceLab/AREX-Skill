# Changelog

## 0.2.0 - 2026-08-31

- Replace the legacy scenario-oriented repository router with a taxonomy-driven
  `area -> family -> repository skill -> relevant sub-skill` router. The
  generated router now uses the fixed 20-area, 178-family taxonomy and supports
  evidence-backed multi-assignment when one repository provides several
  distinct capabilities.
- Add deterministic machine-readable router indexes for the taxonomy,
  repositories, and assignments, together with generated area and family pages
  that support progressive disclosure. Agents can narrow a request to the
  relevant area and family before opening only the smallest useful repository
  skill set.
- Standardize repository routing identity around canonical `owner/repository`
  IDs, while keeping runtime skill IDs separate for collision-free skill
  directories and frontmatter names.
- Add strict taxonomy and metadata validation. Repository routing metadata now
  uses the compact v2 area/family projection with a taxonomy hash; full
  assignment rationale and repository evidence remain in external routing
  decision artifacts rather than being duplicated in the runtime skill graph.
- Add evidence-first routing constraints to the repository-skill meta
  workflows. Assignments must match exact taxonomy paths and repository-local
  evidence; keyword-only matches, dependency-only references, optional
  integrations, example-only signals, and context collisions are rejected.
  Repositories with no justified exact family remain explicitly
  `unclassified` instead of receiving a forced route.
- Add transactional repository-skill collection build and import behavior.
  Router indexes, per-skill routing metadata, provenance, and generated views
  are validated and updated together under a shared lock, with staging,
  rollback, stale-file removal, and preservation of unrelated local skills.
- Preserve router visibility control through
  `disco repo-skills router enable|disable`. Disabling adds
  `disable-model-invocation: true` to the live `repo-skills-router` so it is no
  longer selected automatically; explicit
  `/skill:repo-skills-router` invocation remains available. The setting is
  reported by `status` and preserved across repository-skill updates.
- Remove internal taxonomy design notes from the published taxonomy snapshot
  so the released router contains only runtime routing data.
- Add `--creator` and `--researcher` as concise CLI mode selectors for new
  sessions while retaining `--agent-mode creator|researcher` as a compatibility
  form. Conflicting selectors, selector values, and incompatible resume/fork
  combinations now fail with explicit diagnostics, and the CLI help, prompts,
  and bundled documentation use the shorter forms.
- Harden the inline dynamic workflow runtime around timeout and failure
  boundaries. Timed-out attempts are aborted and drained before the default one
  retry starts, non-recoverable run failures cancel and drain sibling lanes, and
  persisted runs retain stable agent IDs, per-attempt errors and usage, execution
  limits, and recovery lineage across resume.
- Treat explicit `{ complete, rows, missing, errors }` workflow results as a
  coverage contract. Incomplete background runs now return actionable missing
  IDs to the main agent, remain visibly recoverable in `/workflows`, and support
  missing-only recovery with a 50-round default cap, a 1,000-round hard cap, and
  early no-progress termination.
- Add a shared `workflow-authoring` contract and structured prepared-environment
  assertions so Creator can use the verified executable, package, and version on
  its first workflow call without reading runtime source. Known legacy report
  fields are normalized with visible deprecation warnings, parser diagnostics
  point to fragile Markdown-rich script payloads, and finalized usage now
  distinguishes terminal totals, live observations, estimated fallback, cache
  reads, and cache writes. The implementation remains an inline DisCo adaptation
  and adds no workflow npm runtime dependency.
- Rework `import-repo-skills-to-agent` around a bundled transactional export
  helper for Codex, Claude Code, and agent-neutral skill roots. Full and
  selected exports now regenerate the target `repository-index.jsonl` and
  scoped router deterministically, preserve unrelated target skills, require
  per-skill overwrite approval, reject source/target overlap and symlinks, and
  persist enough transaction state for automatic rollback and `--resume`
  recovery after interruption.
- Keep repository skills portable across agents by applying
  `agents/openai.yaml` only to Codex target copies and excluding that target-only
  policy from repository content digests. Align router refresh defaults with
  the managed `skills/repositories/` collection layout.
- Stop persisting per-repository `content_sha256` values in long-lived
  repository indexes. Whole-index integrity digests and transaction-only
  source snapshots remain available for safe export recovery, while the
  one-time `skill_content_sha256` handoff check remains in verified imports.
- Include DisCo's built-in extension packages in startup update discovery and
  `disco update --extensions` / `disco update --extension` processing without
  persisting them into user settings or installing missing defaults as an
  update side effect. Legacy global npm installs are migrated into DisCo's
  managed npm root when updated.
- Add source-commit-bound GitHub license resolution to repository-skill creation,
  refresh, extension, verification, collection build, and cross-agent export.
  Every root and sub-skill now receives one shared top-level `license` value;
  GitHub `NOASSERTION` is preserved, while unavailable queries use `NO_LICENSE`
  and report the required manual follow-up.
- Align the paper-oriented Creator meta-skill contracts around
  `scope -> ground -> construct -> verify`, including task-agnostic and
  task-oriented anchors, construction adequacy guidance, and the renamed
  `construction-strategy-and-adequacy.md` reference.
- Update the published collection contract to the current 1,000 repository
  roots and 2,209 area-family memberships, and add the corresponding default
  collection-build guard and regression coverage.
- Require `@juicesharp/rpiv-todo@^2.7.1` so main, child, and detached sessions
  use isolated Todo state and status changes preserve task creation order. Add
  an isolated published-package contract verifier for session separation,
  child cleanup, foreground ownership, task IDs, and stable ordering.
- Upgrade `undici` to `8.10.0` and override `nanoid` to `3.3.18`, removing the
  high-severity advisories previously reported by a source installation audit.

## 0.1.1 - 2026-08-03

- Fork Pi coding-agent v0.83.0 into the DisCo package.
- Supersede the legacy DisCo `0.0.x` release line and the internal
  `@auto-ml-skills/disco-agent-core`, `@auto-ml-skills/disco-ai`, and
  `@auto-ml-skills/disco-tui` packages. Users should upgrade to
  `@auto-ml-skills/disco@latest`.
- Isolate DisCo configuration and resources under `.disco` and `DISCO_*`.
- Preserve Creator/Researcher modes, dynamic workflows, bundled skills, SDK
  exports, and the interactive splash experience.
- Add `disco repo-skills install|update|status` for commit-tracked installation
  and safe updates of the published repository collection while preserving
  Creator/user repo skills and backing up forced conflict resolution; offline
  status checks include managed drift and live router coverage.
- Add `disco repo-skills router enable|disable`; disabled routers leave automatic
  model selection but remain explicitly invocable, and the setting persists
  across individual imports and full collection updates.

## 0.0.4

- Hardened `repo-skills-router` generation against routing metadata residue by
  stripping rendered field labels, rejecting numeric role artifacts, and
  failing on generated `N more sub-skills` entry-point placeholders.
- Documented routing metadata hygiene in the bundled create/verify repo-skill
  workflows so imported skills provide data-shaped fields instead of rendered
  router Markdown.
- Added genomics HTS file and speech/audio modeling scenarios to the bundled
  router registry template for future repo-skill imports.
- Synchronized package versions for the `0.0.4` release.

## 0.0.3

- Added Codex-target export handling for imported repo skills by writing
  target-side `agents/openai.yaml` policies that keep non-router repo skill
  descriptions out of Codex implicit invocation while preserving
  `repo-skills-router` as the routing entry point.
- Clarified repo-skill creation, extension, verification, and architecture docs
  so source repo skills stay agent-neutral; Codex-specific policy files are
  added only during `import-repo-skills-to-agent`.
- Synchronized package versions for the `0.0.3` release.

## 0.0.2

- Initial DisCo release under the `@auto-ml-skills` npm scope.
- Derived from PI `0.79.1`; DisCo uses its own package version series
  starting at `0.0.2`.
- Rebranded the adapted coding-agent runtime as DisCo.
- Bundled DisCo meta-skills for repo skill creation, environment
  preparation, repo-drift refresh, existing skill extension, imported
  repo-skill routing, and explicit export into other agent tools.
- Generated and refreshed repo skills now include `references/repo-provenance.md`
  so future agents can compare source commit, dirty state, package version, and
  evidence paths before deciding whether a skill is stale.
- Repo skill creation now requires complete per-sub-skill briefs for workflow
  subagents, canonical sub-skill id/name consistency, and main-agent review
  against explicit depth, evidence, routing, self-containment, and artifact
  boundary rubrics before integration.
- Added structured import confirmation and DisCo-first
  `repo-skills-router` updates after a user approves importing a verified
  repo-specific skill. Exporting DisCo's managed skill library into other
  agent tools is handled by the explicit `import-repo-skills-to-agent` meta skill.
- Removed default calls to upstream update and install telemetry endpoints.
- Fixed source builds when the optional interactive assets directory is absent
  in a fresh checkout.
