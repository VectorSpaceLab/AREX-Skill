# Node Workflows

## Purpose

Read this when adding, revising, documenting, or validating RocketRide node catalog entries. This reference focuses on node-specific workflows and intentionally leaves generic builder/package-manager troubleshooting to the repo-level development/build/docs guidance.

## Where node artifacts are co-located

In a RocketRide checkout, each node provider is organized as a co-located node directory. The relevant artifacts usually sit together:

- `service*.json` definitions for provider metadata, lanes, UI/config schema, profiles, and tests.
- `README.md` prose for public node behavior, configuration, authentication, examples, and operational notes.
- `requirements.txt` for the node's Python runtime dependencies when it has non-baseline dependencies.
- Python implementation modules for `node: "python"` services.
- Optional assets such as SVG icons.

Do not rely on an external docs page as the source of truth for node contract edits. The maintained contract is the service JSON plus co-located prose and generated parameter block.

## Adding or revising a service definition

Use this checklist before changing code or docs:

1. Decide whether the change is a new concrete provider, a new variant of an existing provider, or only a shared field/profile update.
2. Choose the provider identity:
   - `title`: display label.
   - `protocol`: stable provider scheme ending in `://`.
   - `prefix`: path/UI conversion prefix.
   - `classType`: category array.
   - `capabilities`: engine/UI flags such as `invoke`, `gpu`, `experimental`, `noremote`, or `internal`.
3. Decide registration/runtime:
   - `register: "filter"` for normal pipeline filters/transforms/tools.
   - `register: "endpoint"` for endpoint/source-style services.
   - `node: "python"` and `path` when the implementation is a Python node module.
4. Define lanes and control behavior:
   - Dataflow nodes need explicit `lanes` from input lane to output lane(s).
   - Control-plane tool nodes may intentionally have empty `lanes`; document how they are attached to agents/tools.
   - Never add a lane solely to make wiring look possible if the implementation does not consume or emit that lane.
5. Define parameters through `fields`, `preconfig`, and `shape`:
   - Put reusable or profile-specific parameter groups under `fields` with `object`/`properties` entries.
   - Include the relevant field ids in `shape`; a field omitted from `shape` usually will not appear in the UI.
   - Keep `tile` interpolation paths aligned with resolved `parameters` names.
6. Update tests or test declarations only to match behavior that can be verified safely. Separate mock/safe checks from real provider, GPU, database, or credential-dependent checks.

## Co-located README and generated params rule

For any public node contract change, update the node's co-located README prose in the same change. Public contract changes include new or changed inputs, outputs, lanes, config fields, profiles, authentication behavior, actions, dependencies, or important error behavior.

Generated parameter regions are protected:

```md
<!-- ROCKETRIDE:GENERATED:PARAMS START -->
...
<!-- ROCKETRIDE:GENERATED:PARAMS END -->
```

Never hand-edit content between those markers. The generated block is regenerated from `service*.json` and per-node `requirements.txt`. Hand-authored prose before or after the markers should explain behavior, examples, authentication, caveats, and testing notes that the generated schema table cannot express.

## Node docs generation

The node docs generator:

- Regenerates schema tables from the service definition fields.
- Emits dependency bullets by parsing the node's `requirements.txt`, preserving constraints while dropping comments/blank lines.
- Emits a source breadcrumb in the generated block for docs rendering.
- Preserves prose outside the generated markers.
- The underlying generator can restrict generation to named nodes when invoked with node names; the builder task shown below uses the repository's configured invocation.
- Skips legacy READMEs that do not carry generated markers.

Useful node-specific command, when the checkout has the required Node workspace tooling installed and the user permits command execution:

```bash
builder nodes:docs-generate
```

After a node public contract change, the repository policy also expects the docs site to build successfully. Use the repo-level development/build/docs guidance for the full docs build command, package-manager setup, and generic builder failures.

## Requirements and optional dependencies

RocketRide has a baseline node runtime dependency set plus per-node dependency files. Treat them as follows:

- Baseline dependencies cover common Python node/runtime needs such as HTTP clients, FastAPI/uvicorn, Pydantic, NumPy, and platform-specific support.
- Per-node `requirements.txt` files declare provider-specific packages such as OpenAI/LangChain libraries, Chroma client, segmentation helpers, vector database clients, API SDKs, or tool integrations.
- Comments in requirements files often explain why a package is needed; preserve that reasoning when changing dependencies.
- The docs generator exposes per-node dependency names in the generated README block.
- Do not install every node's optional requirements just to validate a schema edit. Use static parsing and focused contract tests first.
- If a node is marked `gpu`, `experimental`, or talks to an external provider/database, document that runtime verification may require extra packages, models, hardware, credentials, or services.
- If a dependency is optional for one profile but required for another, document the profile boundary in prose and tests; do not present it as universally installed.

## Test selection for node changes

Prefer the narrowest safe validation that matches the change:

| Change type | First check | Broader check when needed |
|---|---|---|
| Comments/prose outside generated block only | Markdown review and docs-generation diff if the generated block is nearby. | Docs site build via development/build/docs guidance. |
| Service JSON schema/profile/lane edit | Comment-aware JSON parse plus node contract tests. | Focused functional node test with mocks. |
| New Python node module or `path` change | Import/module existence contract check. | Focused functional test after dependencies are available. |
| Lane/output behavior change | Contract lane validation plus a fixture or mock functional test. | Full node functional test only if behavior spans engine/server execution. |
| Provider credential behavior | Static schema/prose review plus mock tests. | Real-provider test only with explicit credentials and user approval. |
| GPU/model/database/runtime dependency | Static schema/prose review and optional dependency import check. | Hardware/service-backed test only when that backend is required and available. |

Known node test surfaces:

- Contract tests parse all service definitions with a comment/trailing-comma tolerant parser, check required fields for Python services, check module existence, and validate lane names/output lanes. They do not test runtime node behavior.
- Functional node tests require a test server and mocks. They are broader and more expensive than contract tests.
- Full tests may include slow, GPU, model, real-provider, or credential/service-bound cases. Do not use them as the default check for catalog-only edits.

Builder task names that appear in node maintenance evidence:

```text
nodes:docs-generate   regenerate generated README parameter/dependency/source blocks
nodes:test-contracts  run service contract validation
nodes:test            run node functional tests with the test server/mocks
nodes:test-full       include full node tests
nodes:build           sync nodes and regenerate docs as part of a build
nodes:clean           remove node build artifacts
```

Some builder tasks may build server artifacts or require workspace dependencies. If the current task only needs schema confidence, a lightweight comment-aware parse plus focused contract check is usually preferable before any broad build.

## Safe review recipe for a node catalog change

1. Identify the affected provider(s) and whether the change is schema, lane, dependency, docs, or implementation behavior.
2. Review the service definition for JSON-with-comments validity, stable `protocol`/`prefix`, correct `classType`/`capabilities`, accurate `register`/`node`/`path`, and coherent `lanes`.
3. Review `preconfig`, profile field defaults, conditional properties, and `tile` interpolation together.
4. Ensure all new visible fields are included in `shape` and all referenced field ids exist.
5. Update co-located README prose outside generated markers.
6. Regenerate the generated block instead of editing it manually.
7. Choose the narrowest safe validation from the table above.
8. If validation requires credentials, network, GPU, a database, a long-running server, or all workspace dependencies, stop and make that requirement explicit before running it.
