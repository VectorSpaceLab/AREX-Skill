# Default Workflows

Default workflows are bundled workflow JSON files synced into the workflow library at app startup. They are library examples and templates, not executable queue sessions by themselves.

## Default Workflow Rules

A valid default workflow must:

- Use an `id` starting with `default_`.
- Keep that ID stable across edits so startup sync updates the existing library record instead of creating a new one.
- Set `meta.category` to `default`.
- Carry a semver-like `meta.version`.
- Avoid references to user-created or locally installed resources such as specific model UUIDs, images, or boards.
- Load in the workflow editor without warnings and run after users choose compatible local resources.

Default workflows appear in the Workflow Library’s default-workflows category and cannot be updated or deleted through normal user workflow mutation methods. If a user loads and saves one, it becomes a user workflow copy.

## Startup Sync Semantics

The default workflow sync scans bundled `*.json` workflow files and validates them as full `Workflow` DTOs. It then:

1. Asserts each ID starts with `default_`.
2. Asserts `meta.category == default`.
3. Adds missing default workflows directly to `workflow_library`.
4. Updates changed default workflows directly.
5. Deletes obsolete default library records whose IDs are no longer present in bundled files.

The sync bypasses public create/update/delete service guards because those guards intentionally reject default workflow mutation. As a result, default workflow `updated_at` and `opened_at` can be noisy around startup sync and should not be interpreted as user activity.

## JSON Shape

Default workflow JSON uses the same frontend-oriented workflow shape as user workflows:

- Top-level metadata: `id`, `name`, `author`, `description`, `version`, `contact`, `tags`, `notes`, `exposedFields`, `meta`, `nodes`, `edges`, and sometimes `form`.
- `nodes`: array of editor nodes. Invocation nodes normally use `type: invocation` and a `data` object with `id`, `version`, `nodePack`, `label`, `notes`, invocation `type`, `inputs`, `isOpen`, `isIntermediate`, and `useCache`.
- `edges`: array with `source`, `target`, `sourceHandle`, and `targetHandle`; IDs are ReactFlow-style and may be long/generated.
- `exposedFields`: references node IDs and input field names that the UI exposes as user-editable form controls.
- `tags`: comma-separated string such as `SD1.5, text to image`.

The server-side workflow DTO does not deeply validate frontend node/edge internals. Structural reference checks still catch many broken default workflow edits: duplicate node IDs, edges pointing to unknown nodes, exposed fields pointing to unknown nodes, and exposed fields not present in a node’s `data.inputs`.

## Safe Inspection Workflow

Use bundled helper `scripts/inspect_default_workflow.py` for a quick no-import check:

```bash
python ../scripts/inspect_default_workflow.py workflow.json
```

Useful options:

- `--json` prints machine-readable summary and issues.
- `--allow-user-category` permits user workflows during inspection when you intentionally reuse the helper outside default assets.
- `--strict` treats warnings as failures.

The helper checks:

- valid JSON object and required top-level keys;
- default ID prefix and `meta.category`;
- semver-like `meta.version`;
- node ID uniqueness;
- edge source/target references;
- exposed field node references and, when possible, `data.inputs` membership;
- suspicious local-resource references in model/image/board-like fields.

## Default Workflow Families

Bundled examples cover common text-to-image, image-to-image, control, upscaling, LoRA, prompt-from-file, SDXL, SD3.5, Flux, CogView, and MultiDiffusion scenarios. Treat them as representative workflow editor JSON when designing UI/library code, but route node-specific compatibility or invocation-schema questions to sibling skills:

- `workflow-nodes`: node type names, input/output schemas, graph construction, edge semantics.
- `model-management`: model node fields, missing model warnings, model identifier compatibility.
- `operations-config`: startup sync timing, deployment config, multiuser auth.

## Source Script Inventory

The repository includes a profiling helper named `generate_profile_graphs.sh`. It is reference-only for this sub-skill because it consumes `.prof` files and requires external Graphviz and `gprof2dot`; it does not validate workflow JSON, queue payloads, or library records. This sub-skill instead bundles safe JSON-only helpers under `scripts/`.

## Common Review Checks

Before accepting a new or edited default workflow:

1. Run `inspect_default_workflow.py` and fix structural issues.
2. Check that `id` remains the existing `default_...` ID for edits.
3. Confirm `meta.category` is `default`; user workflows should not be placed in the default asset set.
4. Check `tags` is a string, not an array.
5. Inspect model/image/board fields for local resource IDs that will not exist for other users.
6. Load the workflow in the UI and run it after selecting compatible resources when native runtime verification is safe.