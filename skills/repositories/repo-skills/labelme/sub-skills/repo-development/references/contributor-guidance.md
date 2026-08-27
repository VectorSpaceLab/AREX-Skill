# Contributor Guidance

## Repository instructions

- User-facing changes belong in `CHANGELOG.md` under `## [Unreleased]`, under
  the correct Added/Changed/Removed/Fixed section, with the PR number linked.
- Prefix a changelog entry with `**Breaking:**` when the change bumps the major
  version.
- Treat `CONTEXT.md` as the domain glossary. Use **Annotation**, **Shape**,
  **Flag**, **Shape Flag**, **Group**, **Config File**, **Settings**, and
  **Setting Control** as defined there.
- Read the relevant ADR in `docs/adr/` before changing behavior that has an
  architectural decision. Surface contradictions rather than silently
  overriding them.

## Issue tracker and triage

Issues are on `wkentaro/labelme` via `gh`. Canonical role labels are:

- `needs-triage`: maintainer evaluation needed.
- `needs-info`: reporter information needed.
- `ready-for-agent`: fully specified for an agent.
- `ready-for-human`: requires human implementation.
- `wontfix`: will not be actioned.

Existing category labels are separate (`issue:bug`, `feature`, `docs`,
`refactor`, `test`, `ui`, `perf`, `i18n`, `dependencies`, `python:uv`,
`others`). Do not conflate category and triage roles.

## AI Assist policy

AI Assist Setting Controls are proactive guidance. Check Prompt Compatibility at
runtime before model download or inference, and reject incompatible prompts
without changing the selected model Setting.

## Architecture reminders

- labelme is an application; the CLI, Annotation File, and Config File are the
  stable public surfaces.
- The Qt-free Annotation codec is deliberately separate from GUI rendering.
- Config is sparse, comment-preserving YAML; Window State is separate Qt
  QSettings state.
- Annotation transitions preserve the last known-good state on load/save failure.
