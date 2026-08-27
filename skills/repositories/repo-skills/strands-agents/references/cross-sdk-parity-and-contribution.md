# Cross-SDK parity and contribution guidance

Read this reference before changing APIs, docs, package exports, tests, or behavior that exists in both SDKs.

## Shared tenets

- Build small, focused changes that the contributor can explain.
- Prefer simple, maintainable code over clever abstractions.
- Verify behavior with the smallest meaningful check before broad CI-style runs.
- Use team design docs, decisions, tenets, API bar, feature lifecycle, and PR guidance for significant API or subsystem work.
- Avoid drive-by reformatting and unrelated refactors.

## Cross-SDK naming and literal parity

| Surface | Rule |
| --- | --- |
| Construct names | Name constructs for what they do, not for the interface they implement. Avoid `Plugin` suffixes in product names unless the public concept is actually a plugin. |
| Identifiers | Match concept names across SDKs and recase idiomatically: Python `snake_case`, TypeScript `camelCase` or `PascalCase`. |
| Single-word string literals | Keep values byte-identical across SDKs, such as `user` or `success`. |
| Multi-word string literals | Python uses `snake_case`; TypeScript uses `camelCase`. Convert through explicit maps rather than ad hoc casing. |
| Wire field names | Preserve provider/API wire field names even when they violate the language style. |
| Hook event names | Keep event concepts paired and shared. Python names usually use `AgentInitializedEvent`; TypeScript may use the documented counterpart such as `InitializedEvent`. |
| Directories | Python subsystem paths use snake_case; TypeScript subsystem paths use kebab-case with matching stems when possible. |

## Public vs internal API

Python:

- Public package surfaces are declared with `__all__`.
- Internal modules should be prefixed with `_` and kept out of public exports.
- Heavy or optional providers should remain lazy-loaded so base imports do not require every optional dependency.

TypeScript:

- Use named exports only; never add default exports.
- Keep exported-but-internal symbols out of the root `index.ts` barrel and tag them `@internal` when appropriate.
- Update `package.json` exports when a new public entry point should be importable by consumers.

Both SDKs:

- API changes should satisfy the API bar and feature lifecycle expectations.
- Deprecations, experimental status, and compatibility constraints must be reflected in docs and tests.
- A public change in one SDK may require a sibling SDK issue, implementation, or explicit non-parity note.

## Logging and comments

Python structured logging uses `%s` interpolation:

```python
logger.debug("field=<%s> | lowercase message", value)
```

TypeScript structured logging uses template literals:

```typescript
logger.debug(`field=<${value}> | lowercase message`)
```

For both SDKs:

- Format context fields as `field=<value>, field=<value> | lowercase human-readable message`.
- Avoid punctuation at the end of the human message.
- Keep comments evergreen and only explain non-obvious constraints or invariants.
- Do not narrate how code changed or what it used to do.

## Testing and verification selection

Choose checks by changed surface:

| Change | First checks | Escalate when |
| --- | --- | --- |
| Python SDK source | focused pytest file or package smoke | public API, provider, session/memory, or integration behavior changes |
| TypeScript SDK source | focused Vitest file or `type-check` | browser safety, package exports, or example behavior changes |
| Docs page/snippet | snippet typecheck or site tests | generated API, navigation, sourceLinks, or build output changes |
| MCP server | offline unit tests and smoke helper | live docs fetch behavior is intentionally selected |
| Cross-SDK API | both affected SDK test slices and docs/sourceLinks review | public naming, hook events, message shapes, or wire fields change |

Treat credentials, network, browser, Docker, and AWS infrastructure as explicit optional backends. A skipped optional backend is not a pass; record it.

## Documentation and source links

- Documentation terminology is locked: use `agent loop`, `tool calling`, `model provider`, `session management`, `memory`, `hooks`, `multi-agent`, `structured output`, `observability`, and `deployment` consistently.
- Do not call SDK tools "skills" in user-facing SDK docs. Use "skills" only for agent skill files.
- Docs `sourceLinks` track backing implementation files. When a source file is moved or renamed, update affected docs page frontmatter in the same change.
- Generated API docs are regenerated, not hand-edited.
- Code examples must be verified against source or installed package facts before handoff.

## PR and community workflow

- One logical change per PR.
- Open an issue first for significant API or feature work.
- Run relevant package checks and manually exercise behavior when automated checks do not prove the user-facing claim.
- Self-review the diff end to end before PR handoff.
- For community support, point design questions to Discord or GitHub Discussions and keep guidance warm, concise, and educational.
