# Contributor Guidance

## Branch and PR discipline

- Platform development normally targets `dev`; `master` is the production
  branch. A catalog-only incident hotfix may use the repository's documented
  hotfix route, then must be merged back to `dev`.
- Keep a change focused. Split unrelated backend, frontend, infrastructure,
  documentation, or migration work rather than combining it opportunistically.
- Use conventional commit titles with a scope such as `feat(backend): ...`,
  `fix(frontend): ...`, or `docs(platform): ...`.
- PR descriptions should clearly state why the change is needed, what changed,
  and how it works. Follow the repository PR template.

## Cross-cutting safety

- Never commit `.env` files, API keys, client secrets, cloud credentials, or
  production data exports.
- Do not run destructive reset, migration, data-seeding, benchmark, or release
  commands without checking the selected environment and side effects.
- Prefer focused tests for the changed surface before expensive full-stack
  suites. Review snapshot changes intentionally.
- Preserve generated-code boundaries. Regenerate the frontend API client after
  intentional backend OpenAPI changes rather than hand-editing generated hooks.

## Test-first convention

For a bug or feature, establish a focused failing test before implementation
when the affected package's testing conventions support it. Remove any
temporary expected-failure marker only after the new behavior passes.

## Documentation work

- Platform block documentation has manually maintained sections; do not
  overwrite designated manual content when regenerating block docs.
- Keep user-facing language concise, practical, and consistent with the
  Platform-versus-Classic distinction.
- For changes that affect a documented configuration, API, block, or workflow,
  identify the closest docs surface and update it with the code.
