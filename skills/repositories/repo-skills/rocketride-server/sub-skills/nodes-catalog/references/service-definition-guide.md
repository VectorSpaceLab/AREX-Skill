# Service Definition Guide

## Purpose

Read this when you need to understand, review, or modify RocketRide node catalog entries. RocketRide node providers are described by `service*.json` files that are intentionally comment-bearing JSON. A single node directory may contain one default `services.json` or several named variants such as `services.<variant>.json`.

## JSON format

The service files are not strict JSON:

- `//` comments are common and are used as inline documentation for fields.
- Some files include trailing commas or comment-bearing values.
- Plain `json.loads`, `JSON.parse`, or `python -m json.tool` can fail even when the service is valid for RocketRide tooling.
- A validation helper should strip line comments outside strings, strip block comments if present, and remove trailing commas before parsing.

Treat parse failures as contract issues only after using a comment-aware parser.

## Concrete service versus shared field library

Most `service*.json` files define selectable or executable services and include `title`, `protocol`, `classType`, `capabilities`, `prefix`, `shape`, and usually `fields`, `lanes`, `node`, `path`, and `register`.

Some catalog files are shared field libraries rather than standalone services. Shared libraries mainly define reusable `fields` blocks such as cloud credentials, include/exclude forms, LLM access, vector-store settings, remote-processing settings, anonymization, or combined provider selectors. They may not have a `title` or `protocol` and should not be treated as malformed solely for missing concrete-service fields.

## Core service fields

| Field | Meaning | Maintenance notes |
|---|---|---|
| `title` | Human-facing display name in UI/docs. | Keep concise and stable. If changed, update co-located prose and generated docs. |
| `protocol` | Endpoint/provider scheme such as `llm_openai://`, `filesys://`, or `webhook://`. | Must identify the service. Changing it can break existing pipelines and URL/path conversion. |
| `classType` | Array describing what the node does. | Common values include `source`, `target`, `data`, `text`, `image`, `audio`, `video`, `embedding`, `llm`, `store`, `database`, `tool`, `agent`, `memory`, `infrastructure`, and `preprocessor`. Some services use multiple classes, for example `store` plus `tool`. |
| `capabilities` | Engine/UI flags. | Common flags include `invoke`, `gpu`, `experimental`, `noremote`, `nosaas`, `filesystem`, `security`, `internal`, and `noinclude`. Do not infer installed dependencies from capabilities; they are catalog/engine hints. |
| `register` | Factory registration mode. | Usually `filter`; `endpoint` appears for source/endpoints such as webhook-style services. Missing can mean a shared library or internal service. |
| `node` | Physical implementation type. | Most catalog entries use `python`. If omitted, the engine may infer from protocol or the service may be a shared library/internal definition. |
| `path` | Implementation import or executable path relative to the node package namespace. | For Python services this commonly names the node module. Keep it aligned with the actual implementation and importable package structure. |
| `prefix` | Label/prefix used when converting between paths, URLs, and UI/provider identifiers. | Keep stable; a mismatch can make path/URL conversion confusing even if the protocol parses. |
| `icon`, `documentation`, `tile` | UI presentation metadata. | `tile` strings often interpolate runtime parameters, for example `${parameters.<field>}`. Ensure referenced parameter fields exist after profile/shape merging. |
| `description` | Human-facing provider summary, often an array of string fragments. | Keep it accurate but avoid making it the only documentation; update co-located README prose for public behavior changes. |

## Lanes and control-plane nodes

`lanes` maps an input lane to one or more output lanes:

```json
"lanes": {
  "questions": ["answers"],
  "documents": ["documents"],
  "_source": ["tags"]
}
```

Use lanes for dataflow compatibility, not for every invocation relationship:

- `source` nodes often emit from `_source` into `tags`, `text`, `json`, media, or question lanes.
- Text/image/audio/video/document transforms consume and emit concrete data lanes.
- LLM nodes commonly map `questions` to `answers`.
- Vector stores may accept `documents` for ingest and `questions` for retrieval, sometimes emitting `documents`, `answers`, or enriched `questions`.
- Tool and agent nodes may have empty `lanes` because they participate through the control/invoke plane rather than data lanes.

Valid lane names seen in node contracts include `text`, `documents`, `questions`, `answers`, `table`, `image`, `audio`, `video`, `classifications`, `classificationContext`, `tags`, and special lanes starting with `_`.

## Profiles and `preconfig`

`preconfig` declares presets that are merged into runtime parameters:

- `default` names the default profile.
- `profiles` maps profile ids to concrete values such as model names, provider hosts, API-key slots, dimensions, token limits, or feature flags.
- A field such as `<node>.profile` often has `enum: ["*>preconfig.profiles.*.title"]` and `conditional` entries that reveal parameter groups for the selected profile.
- Profiles can carry internal capability flags, for example reasoning support or deprecated/migration notes for model profiles.

When adding or renaming profiles, update all of these together: `preconfig.profiles`, the profile field's `default`, `enum`, `conditional` references, `tile` interpolations, and README prose.

## Fields, shape, and parameters

`fields` is the local schema dictionary. Common properties include:

- `type`, `title`, `description`, `default`, `enum`, `minimum`, `maximum`, `optional`, `secure`, `readonly`, `hidden`, `const`, and `ui` hints.
- `conditional`, used to reveal additional properties based on the selected value.
- `object`, used to define grouped subforms or profile-specific parameter groups.
- `section`, used to label parameter sections such as `parameters`, `Source`, `Target`, `Pipe`, or custom groups.
- `properties`, used to reference other field ids in a shape or object.

`shape` determines which fields are exposed in each service form. Concrete services normally need at least one shape entry. Source/target-style services may expose separate shapes, while many pipeline nodes expose a `Pipe` shape.

The word `parameters` appears in two related ways:

1. Runtime components and tile strings refer to resolved node parameters, for example `${parameters.llm_openai.profile}`.
2. Some service definitions declare a field object named `parameters` or a `<node>.source.parameters` group whose `section` is `parameters`; `shape` then includes that group.

When a UI field does not appear, check whether its field id is included in the active `shape` path, not merely defined under `fields`.

## Optional descriptive fields

Some service files also use:

- `input`: verbose lane documentation with `lane`, `description`, and output lane descriptions. This is useful for docs and tests but does not replace `lanes`.
- `actions`: supported endpoint operations such as export, delete, or download.
- `required`: dependencies or prerequisites used by particular services.
- `invoke`: metadata for control-plane/tool invocation.
- `test` and `fulltest`: native node test declarations. Treat them as validation evidence and test-selection hints, not as proof that external credentials or large model dependencies are available.

## Category map

Use `classType` for high-level routing:

- Ingestion and egress: `source`, `target`, filesystem/webhook/response-like services.
- Data processing: `data`, `text`, `image`, `audio`, `video`, `preprocessor`, parser/fingerprinter/anonymization/transcription/captioning-style nodes.
- Retrieval and storage: `embedding`, `store`, `database`, `memory`, vector stores, SQL/AQL, retrieval helpers.
- Reasoning and orchestration: `llm`, `agent`, `tool`, `graph`, MCP/tool providers, LLM providers, agent frameworks.
- Operations and internals: `infrastructure`, `internal`, `other`, combined selectors, remote/local processing helpers.

Class type is not enough to wire a pipeline. Always pair it with `lanes` for dataflow and `capabilities`/`invoke` for control-plane behavior.
