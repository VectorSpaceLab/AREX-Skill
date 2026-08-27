# Documentation And Generated Files

Use this reference for source-checkout changes under `docs/`, generated documentation outputs, schema snapshots, changelog files, notebook documentation, and maintainer-only scripts.

## Documentation source of truth

- Treat `docs/` MDX files as the source of truth for published product documentation and product-usage agent entry points.
- Before editing a docs page, read the full target page. Preserve its workflow and match the surrounding structure.
- Map behavior changes to existing pages before proposing a new page.
- Update `docs/index.yml` when navigation, slugs, or page placement changes.
- Refer to the package as "the NVIDIA NeMo Guardrails library".
- Use active voice, second person, present tense, and direct language.
- Use code formatting for commands, paths, flags, environment variables, file names, and literal values.
- Avoid hype, rhetorical questions, emoji, em dashes, and unnecessary bold text.
- Do not duplicate the page title as a body H1 because Fern renders the title from frontmatter.
- Use Fern components such as `<Tabs>`, `<Tab>`, `<Cards>`, `<Card>`, `<Badge>`, `<Note>`, `<Tip>`, and `<Warning>` consistently with nearby pages.

## Agentic documentation

- Product-usage agent guidance should route users to canonical docs rather than duplicating full instructions.
- Prefer docs MCP, `llms.txt`, and clean per-page Markdown for agent entry points.
- Keep starter prompts focused on bootstrapping an agent to the docs.
- Do not hardcode staging URLs in user-facing docs unless the page is explicitly about staging.
- Document version-alignment behavior when telling agents how to use docs.

## Docs validation

Documentation tooling requires Node.js 22. The Fern CLI version is pinned and invoked through repository targets; do not run `fern upgrade` as part of normal docs work.

Use checkout-scoped commands:

```bash
make docs-fern
make docs-fern-live
make docs-fern-strict
uv run --locked pre-commit run --files <changed files>
```

- Run `make docs-fern` when rendering, links, examples, navigation, or docs configuration may be affected.
- Run `make docs-fern-live` only when an interactive preview is useful.
- Run `make docs-fern-strict` when link changes are broad or risky.
- For docs-only changes, run file-scoped pre-commit before handoff when practical.
- Report skipped docs validation and residual risk clearly.

## Public behavior documentation

Update docs when changing user-visible behavior, public APIs, configuration syntax, examples, installation requirements, optional dependency requirements, provider integrations, model routing, supported modes, server shapes, evaluation behavior, or observability/telemetry contracts.

For optional integrations, document:

- Whether the integration is optional.
- Which extra or package is required.
- Which API keys or environment variables are expected.
- Whether it uses the default OpenAI-compatible framework path or LangChain.
- Supported modes and known limitations.
- Whether examples require live providers or can run with deterministic fakes.

Use current generally available model IDs in docs/examples and verify them against provider docs before claiming support. Do not change shipped default model parameters as a documentation-only update.

## Generated SDK reference and docs outputs

- Do not hand-edit generated Python SDK reference output.
- Do not edit generated docs artifacts just to make a docs check pass; fix the source or run the documented generation target when explicitly appropriate.
- Fern-related helper scripts may mutate generated docs output or normalize generated SDK pages. Treat them as docs-maintenance tooling, not user runtime helpers.
- If a generated docs target changes files, review the generated diff and report it separately from source edits.

## Changelog and release files

- Never edit `CHANGELOG.md` or `CHANGELOG-Colang.md` manually.
- Put release-note context in issue or PR draft text.
- Do not hand-edit release-generated files unless the task explicitly requires a documented regeneration workflow.

## Notebook documentation

Notebook docs are special. Do not run `build_notebook_docs.py` unless explicitly asked.

If a human explicitly requests notebook-doc generation:

1. Use a clean worktree.
2. Confirm the notebook folder has the expected single-notebook layout.
3. Expect the script to run notebook-doc conversion, rename generated Markdown to `README.md`, run broad `git add .`, and run pre-commit over all files.
4. Review the full resulting diff and report any broad changes.

For ordinary docs work, edit the relevant MDX source instead of invoking notebook generation.

## Maintainer-only and reference-only scripts

Do not copy these maintainer scripts into repo-skill runtime helpers. They are source-checkout maintenance commands and require explicit task intent before use.

| Script or category | Decision | Why |
| --- | --- | --- |
| `scripts/generate_rails_config_schema_snapshot.py` | Exclude unless explicitly maintaining config-schema snapshots | Writes `schemas/rails_config.snapshot.json`; it is a mutation-prone maintainer workflow after schema changes. |
| `scripts/extract_telemetry_snapshot.py` | Exclude unless explicitly syncing telemetry schema snapshots | Consumes an upstream telemetry schema and writes the local anonymous-events snapshot; it is not a product-usage or default validation helper. |
| `scripts/telemetry_smoke.py` | Reference-only unless explicitly running telemetry staging smoke | Requires staging endpoint configuration, network access, isolated audit state, subprocess orchestration, and waits for event delivery. It is not safe as default validation. |
| `scripts/openai_coverage.py` | Reference-only unless explicitly checking API conformance | Requires `oasdiff`, OpenAI spec input or fetch, and API-spec maintenance intent; do not run as routine server validation. |
| `scripts/kibana_verify_export.py` | Exclude unless explicitly authorized for telemetry/Kibana maintenance | It targets credentialed external observability services. |
| `docs/scripts/*` and Fern helper scripts | Reference-only for docs maintainers | They convert or normalize docs/source/generated outputs and can touch broad docs trees. Use documented `make docs-fern*` targets for normal validation. |
| `build_notebook_docs.py` | Explicit request only | Runs notebook conversion, broad staging, and pre-commit over all files; use only with a clean worktree and human intent. |

When in doubt, do not run mutation-prone scripts. Draft the maintainer command, prerequisites, expected diff, and validation plan instead.
