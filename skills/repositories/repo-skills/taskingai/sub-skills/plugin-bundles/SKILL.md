---
name: plugin-bundles
description: "Work with the TaskingAI plugin microservice bundle catalog, plugin
  schemas, execution, credential validation, image storage, and plugin-specific
  troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# TaskingAI Plugin Bundles

Use this sub-skill when the task is about TaskingAI's plugin microservice: built-in bundle/plugin discovery, plugin input/output schema selection, plugin execution payloads, credential validation, generated image storage, or plugin-specific troubleshooting.

## Load this first

1. For catalog selection, schema shape, and no-credential bundle choices, read [references/bundle-catalog.md](references/bundle-catalog.md).
2. For HTTP route contracts, request/response bodies, credential validation, and execution flow, read [references/api-reference.md](references/api-reference.md).
3. For source-backed native-test behavior and safe skip criteria, read [references/native-testing.md](references/native-testing.md).
4. For failure diagnosis, especially local image URL versus S3 storage problems, read [references/troubleshooting.md](references/troubleshooting.md).
5. To inspect a local TaskingAI checkout without network calls or credentials, use [scripts/inspect_plugin_bundles.py](scripts/inspect_plugin_bundles.py).

## Source-backed facts to preserve

- The plugin microservice exposes 47 built-in bundles and 86 plugins in the verified catalog snapshot.
- Static import checks passed in Python 3.10 for `APIRouter`, `Bundle`, `Plugin`, `Arithmetic`, and `ChartMaker`.
- Catalog metadata is defined by bundle schemas and plugin schemas, then loaded into in-memory caches at service startup.
- Plugin execution validates bundle credentials before plugin lookup/input validation, then calls the dynamically loaded bundle/plugin handler class.
- Generated-image plugins use either local storage or S3-compatible storage based on object-storage configuration.

## Quick routing

- Need a safe synthetic no-credential tool? Prefer `arithmetic/add` or `arithmetic/divide` for precise numeric behavior. Use `chart_maker/*` or `qr_code_generator/generate_qr_code` only when image storage and `project_id` are intentionally in scope.
- Need to send a backend-created tool instance/action through TaskingAI's backend object lifecycle? Route that task to `../backend-api/` and return here only for plugin bundle/schema payload details.
- Need inference-provider model invocation or provider credentials unrelated to plugin bundles? Route to `../inference-providers/`.
- Need deployment environment basics, container startup, or cross-service env wiring? Route to `../deployment-configuration/`; return here for plugin-specific storage and credential variables.

## Operating workflow

1. **Identify the bundle and plugin.** Use the no-credential and credentialed catalogs in [references/bundle-catalog.md](references/bundle-catalog.md). Confirm whether provider credentials, network access, `project_id`, or image storage are required.
2. **Validate schema before execution.** Compare the task payload to the plugin input schema types: `string`, `integer`, `number`, `boolean`, `string_array`, `integer_array`, `number_array`, `boolean_array`, `image_url`, or `file_url`. Required inputs must be present; URL types must start with `http`.
3. **Choose the credential path.** For no-credential bundles, pass `{}` as credentials. For credentialed bundles, pass either plaintext `credentials` or encrypted credentials, never both. Use the verification endpoint if credentials must be encrypted for later reuse.
4. **Execute through the plugin service contract.** POST to `/v1/execute` with `bundle_id`, `plugin_id`, `input_params`, `credentials`, and optional `project_id`. Expect `status: success` plus `data.status` and `data.data` on normal execution.
5. **Handle storage outputs.** If the plugin returns `url` or `image_url`, check whether local or S3 storage is configured and diagnose with [references/troubleshooting.md](references/troubleshooting.md) before blaming the provider.

## Hard usability cases covered here

- Select a no-credential built-in bundle for a synthetic tool workflow and explain exact expected input/output schema: use `arithmetic/add` with numeric `number_1`, `number_2` and numeric `result`, or use `arithmetic/divide` and explicitly reject `number_2 = 0`.
- Diagnose a generated chart or QR-code URL that works under local storage but fails under S3, or vice versa, by checking `OBJECT_STORAGE_TYPE`, local `HOST_URL`/`PATH_TO_VOLUME`, S3 endpoint/bucket/public-domain variables, and whether the returned URL path includes the generated image category prefix.
