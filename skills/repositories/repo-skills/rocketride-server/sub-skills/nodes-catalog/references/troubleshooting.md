# Nodes Catalog Troubleshooting

## Purpose

Use this reference when a RocketRide node service definition, generated node documentation, dependency list, or node contract check behaves unexpectedly.

## Fast triage

1. Is the affected file a concrete service definition or a shared field library? Shared libraries can lack concrete-service fields by design.
2. Was the file parsed with a comment-aware JSON parser? Strict JSON tools are often the wrong parser.
3. Does `shape` include every field group you expect the UI/runtime to expose?
4. Do `preconfig`, profile defaults, profile conditionals, and tile interpolation agree?
5. Are lanes dataflow lanes, or is the node actually a control-plane tool/agent node with empty `lanes`?
6. Did the change touch a public contract? If yes, update co-located README prose and regenerate the generated params block.
7. Does verification require optional packages, credentials, services, or GPU/model assets? If yes, do not treat a missing backend as a schema failure; record the requirement and select an appropriate check.

## Service JSON will not parse

Symptoms:

- A generic JSON parser reports an error near `//` comments.
- A generic parser reports trailing comma errors.
- Docs generation or contract tests skip a service after parse failure.

Likely causes:

- The file is JSON-with-comments, not strict JSON.
- A `//` in a URL was stripped by a naive comment remover.
- A trailing comma, unescaped control character, or malformed string remains after comment stripping.

Recovery:

- Re-parse with a JSONC-aware parser or a comment stripper that ignores `//` inside strings and URL schemes.
- Remove true malformed JSON syntax, but do not delete useful field comments just to satisfy strict JSON tooling.
- If a service parses only because a parser is overly permissive, tighten the JSON so the repository's docs generator and contract parser can both handle it.

## Required fields are reported missing

Symptoms:

- Contract validation says a service is missing `title` or `protocol`.
- A service is absent from the catalog/UI.
- A shared common file is incorrectly flagged as a broken service.

Likely causes:

- A concrete provider is missing required service identity fields.
- A shared field library was classified as a concrete provider.
- A multi-service node variant was renamed in a way the discovery glob does not recognize.

Recovery:

- For concrete services, add or restore `title`, `protocol`, `classType`, `capabilities`, `prefix`, and an appropriate `shape`.
- For shared field libraries, ensure the reviewer/test understands that field-only files are libraries, not standalone providers.
- Keep variant filenames in the `services*.json` family so docs and tests discover them.

## A parameter is missing from the UI or generated docs

Symptoms:

- A field exists under `fields` but is not visible in the node form.
- A profile-specific field appears for the wrong profile or not at all.
- A tile interpolation displays blank or unresolved values.
- The generated schema table omits an expected field.

Likely causes:

- The field id is not included in the active `shape` entry.
- The field is nested in an `object` but the object is not referenced by shape or conditionals.
- The profile field's `conditional` values do not match `preconfig.profiles` keys.
- `default` references a profile that does not exist.
- `tile` uses a `parameters.<field>` path that no longer matches the resolved parameter key.

Recovery:

- Trace the visible path from `shape[].properties` to field groups and leaf field ids.
- Check profile `default`, `enum`, and `conditional` entries together.
- Update generated docs after fixing schema wiring.
- Prefer adding a narrow contract/usability check that asserts the field appears in the generated schema or resolved shape.

## A node cannot be wired in a pipeline

Symptoms:

- Pipeline validation says an input lane is unsupported.
- A node appears in the catalog but cannot connect to the expected upstream/downstream node.
- A tool node has no data lanes and appears unusable in a lane-only view.

Likely causes:

- `classType` suggests the right category, but `lanes` do not expose the needed dataflow.
- Output lane names are misspelled or not in the contract's known lane set.
- The node is a control-plane `tool`, `agent`, `llm`, or `memory` participant and should be connected through invoke/control configuration rather than data lanes.
- A source/endpoint uses special `_source` lanes.

Recovery:

- Validate lane names against the known lane set: `text`, `documents`, `questions`, `answers`, `table`, `image`, `audio`, `video`, `classifications`, `classificationContext`, `tags`, plus special `_` lanes.
- For dataflow transforms, update `lanes` and README prose together.
- For control-plane nodes, document the invoke/tool attachment clearly instead of adding fake data lanes.
- Route full `.pipe` composition and lane-repair recipes to the pipeline-authoring guidance; this sub-skill only owns the catalog contract.

## Generated README block was edited or drifted

Symptoms:

- Generated schema/dependency rows differ from `service*.json` or `requirements.txt`.
- Manual prose was added between the generated markers and later disappeared.
- Review comments ask why dependencies are missing from a node page.

Likely causes:

- Someone hand-edited the protected generated region.
- Docs generation was not run after a service or requirements change.
- The node README lacks generated markers, so the generator skipped it.

Recovery:

- Move hand-authored explanation outside the generated markers.
- Regenerate node docs from the service definition and requirements file.
- If a README intentionally has no generated markers, document that migration separately rather than assuming generation failed.
- When a public node contract changed, also run the repo's docs-build workflow if allowed by the current task and environment.

## Optional dependency import fails

Symptoms:

- A node import fails with `ModuleNotFoundError` or `ImportError` for a provider SDK.
- A catalog/static check passes but functional node execution fails.
- Generated docs list a dependency that is not installed in the current environment.

Likely causes:

- Only the baseline node dependencies are installed.
- The affected node's per-node `requirements.txt` was not installed.
- The dependency is profile-specific, GPU/model-specific, or external-service-specific.
- The node intentionally avoids an external SDK, but stale requirements/prose still mention it.

Recovery:

- Identify whether the missing package is baseline, per-node, or profile/backend-specific.
- Do not install all node requirements as a default repair. Install only the dependency set required for the selected node/profile/test.
- If the task is only catalog/schema validation, record optional dependency status and use static parsing/contract tests.
- If the task is runtime behavior, obtain approval for provider credentials, external services, GPU/model packages, or database setup as needed.
- Update the generated dependency block after changing requirements.

## Python node module cannot be imported

Symptoms:

- Contract tests report a missing module or missing `__init__.py` for a Python node.
- The service uses `node: "python"` but the implementation path no longer matches the package.
- Functional tests fail before node logic runs.

Likely causes:

- `path` does not match the implementation module.
- Package init files or exports are missing.
- Optional dependencies are imported at module import time instead of inside the profile/function that needs them.
- The test environment lacks the package path or baseline dependencies.

Recovery:

- Keep `path`, service directory name, and Python package/module structure aligned.
- Prefer lazy imports for optional provider SDKs so schema and docs checks do not require every provider package.
- Add focused import or contract coverage for a new Python node before broader functional tests.

## Node test command is too broad or unsafe

Symptoms:

- A simple service JSON edit triggers server builds, long-running functional tests, or real provider calls.
- Tests fail because credentials, external services, model caches, Docker, pnpm workspace dependencies, or GPU packages are unavailable.
- Full tests fail while contract tests pass.

Likely causes:

- The broad node test suite was selected before narrowing to the changed contract.
- `test`/`fulltest` declarations include real-provider or expensive cases.
- The environment is missing optional packages that are not required for the catalog change.

Recovery:

- Start with comment-aware parse and node contract validation for schema/lane/doc-generation changes.
- Use mock/focused functional tests only when implementation behavior changed.
- Reserve full tests for explicitly authorized backend/service coverage.
- If a required backend is unavailable, state the block; do not silently reinterpret a failed full test as a catalog failure.

## Docs generator or builder task fails before node logic

Symptoms:

- A command fails because package-manager tooling is absent.
- A builder task wants to build server artifacts before the intended node check.
- Docs generation is skipped on a branch where the generator intentionally avoids source-link churn.

Likely causes:

- Workspace tooling is not installed in the current environment.
- The selected builder task bundles broader build steps.
- The docs generator has branch restrictions for generated source links.

Recovery:

- For node-schema review, use a lightweight parser or focused contract check when possible.
- Escalate package-manager setup, generic builder usage, and full docs-build remediation to the repo-level development/build/docs guidance.
- When the task requires generated docs, make the skipped-generation reason explicit and ask whether to switch branches, run a narrower generator invocation, or defer full docs generation.

## Provider credentials or live validation fail

Symptoms:

- A node validates schema but warns on live provider checks.
- Authentication errors mention invalid API keys, missing tokens, unauthorized project/location, or unreachable service host.
- Rate limits or transient connection errors appear during provider tests.

Likely causes:

- The service definition is valid but runtime credentials/services are missing.
- A provider profile changed model names, endpoint fields, token limits, or credential keys.
- A live provider test is being run in an environment without authorized network/credentials.

Recovery:

- Separate catalog correctness from live-provider readiness.
- Verify that credential fields are marked secure/optional as appropriate and documented in prose.
- Use mock tests for schema/contract changes.
- Run live-provider checks only with explicit credentials, network permission, and an accepted cost/rate-limit risk.
