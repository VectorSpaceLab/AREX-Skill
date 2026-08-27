# DataChain Agent Skills and Knowledge Base

DataChain ships three bundled agent skills and a markdown knowledge base that
lets coding agents reason over stored datasets before they write new pipeline
code.

## Bundled Skills

| Skill | Use it when | Main persistent output |
| --- | --- | --- |
| `core` | The request is about abstract DataChain SDK mechanics with no concrete dataset or bucket: API usage, UDF shape, settings, saving, exports, file types, and common SDK gotchas. | None by itself. It guides code generation. |
| `knowledge` | The request mentions datasets, buckets, cloud/local storage, data pipelines, creating/saving/listing/exploring data, or any script that may create datasets as a side effect. | `dc-knowledge/` markdown plus temporary JSON during rebuild. |
| `jobs` | The request asks about Studio job analytics: job history, compute hours, user spend, failures, cluster usage, or cost estimation. | `dc-knowledge/jobs/index.md`. |

Operational rule: for any concrete data task, the knowledge skill is the
orchestrator. It reads existing knowledge first, applies CAST layer planning,
uses core-style SDK rules for code, then rebuilds the knowledge base after new
or changed datasets appear.

## Skill CLI Surface

- `datachain skill list` lists bundled skills and supported targets. The
  installed package reports `core`, `knowledge`, and `jobs` for targets
  `claude`, `cursor`, `codex`, `pi`, and `copilot`.
- `datachain skill install [SKILLS] --target <target> [--local]` installs one
  comma-separated skill list, or all three when `SKILLS` is omitted.
- `datachain skill uninstall [SKILLS] --target <target> [--local]` removes the
  corresponding installed skill directories and command/rule files for the same
  target and scope.

Use [target-layouts](target-layouts.md) before installing or removing files.

## `dc-knowledge/` Structure

Expected durable layout:

```text
dc-knowledge/
├── index.md
├── datasets/
│   ├── <local_dataset>.md
│   └── <namespace>/<project>/<studio_dataset>.md
├── buckets/
│   └── <scheme>/<bucket_or_bucket_prefix>.md
└── jobs/
    └── index.md        # only when Studio job analytics were fetched
```

Temporary rebuild files may also appear:

- `dc-knowledge/.plan.json` — update plan kept for reporting/debugging.
- `dc-knowledge/datasets/**/*.json` and `dc-knowledge/buckets/**/*.json` —
  intermediate snapshots created before enrichment and normally removed after
  `index.md` is rebuilt.

Do not parse JSON intermediates as the durable source of truth. Use
`index.md` and the linked markdown pages.

## Dataset Markdown Content

A dataset page summarizes one saved dataset and its versions. Its frontmatter is
built from the latest version and may include:

- `name`, `last_version`, `last_version_uuid`, `updated`, `records`,
  `is_local`, and `known_versions`;
- `cast_layer`, `cast_scope`, and `cast_source` when layer metadata is available.

The body is optimized for agents and humans:

- a short description of what the dataset contains and how it was produced;
- optional session context explaining why it was created;
- dependency links to upstream datasets or bucket listings;
- latest-version preview rows, schema, and optional statistics;
- newest-first version notes and scripts when available;
- plain caveats for partial history, missing versions, or deleted dependencies.

Snapshot collection behavior to remember:

- dataset snapshots are built from metastore reads with incomplete versions
  excluded and preview included;
- Studio dataset names are qualified as `namespace.project.name`;
- direct dependencies are recorded; storage listing dependencies are rendered as
  storage URIs and linked to bucket pages;
- version history is sorted semantically and capped to the most recent 20
  entries to stay within prompt budget;
- the latest version carries schema and preview, while older versions mainly
  carry change history;
- system columns are filtered out, nested `__` columns are displayed with dots,
  and very long preview cells are truncated.

## Bucket Markdown Content

A bucket page summarizes a storage listing or prefix. Its frontmatter may include
`uri`, `bucket`, `prefix`, `anon`, listing `uuid`, `scanned`, `files`, `size`,
and `sampled`. The body normally contains quick stats, directory structure,
file-type breakdown, representative samples, access notes, listing freshness,
and data-quality caveats.

If a listing is stale or expired, update the storage listing first when the user
asks to refresh the source, then rebuild `dc-knowledge/`.

## Regeneration Flow

The knowledge skill performs a seven-step rebuild:

1. enlist new bucket roots and run a fast access check;
2. plan stale/new datasets and bucket docs into `.plan.json`;
3. snapshot stale/new datasets and buckets to JSON;
4. enrich JSON snapshots into markdown pages;
5. render `dc-knowledge/index.md`;
6. remove JSON intermediates unless debugging was requested;
7. report updated, unchanged, scanned, and stale entries.

After any script creates or changes a dataset, rebuild the knowledge base before
answering as if the new result is persistent context.

## CAST Summary

CAST is the layer vocabulary the knowledge workflow uses:

| Layer | Prefix | Meaning | Persistence default |
| --- | --- | --- | --- |
| Container | `l1_` | Typed listing, headers, sidecar metadata, and other bounded-read file facts. | Save and refresh by delta. |
| Asset | `l2_` | Decoded or mixed raw data in a workable row grain. | Save and refresh by delta. |
| Sense | `l3_` | Model-derived signals: embeddings, classifications, transcriptions, detections, LLM outputs. | Save full outputs and filter downstream. |
| Task | none | Task-specific ranking, filter, aggregation, eval set, or curated subset over C/A/S layers. | Persist by exception, except reusable aggregations should be saved. |

Every new C/A/S dataset should have a descriptive name, `attrs` such as
`cast:<layer>`, `scope:<scope>`, and `source:<slug>`, plus a one-line
`description`. UDF-bearing data work should leave at least one reusable C/A/S
layer unless the user explicitly asks for a quick one-off. Multi-stage pipelines
should use one script per stage and one `.save()` per script.

For detailed SDK code patterns, route to `sdk-pipelines`; for query expression
mechanics, route to `query-engine`.
