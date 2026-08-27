# Agent Data-Harness Workflows

DataChain turns agent work over buckets and files into named, versioned datasets.
The knowledge base then makes those datasets discoverable across agent sessions.
Use this page for workflow shape; route detailed SDK code patterns to
`sdk-pipelines` and query-function details to `query-engine`.

## 1. Check Existing Knowledge First

Before proposing a rebuild:

1. Look for `dc-knowledge/index.md`.
2. If present, read the index and the relevant dataset or bucket pages.
3. Prefer a saved dataset over raw storage when it covers the task, even
   partially.
4. Use a Task query or a small derived dataset on top of existing C/A/S layers
   when that is cheaper than rebuilding from raw files.

A useful quick check:

```bash
python skills/disco/datachain/sub-skills/agent-harness/scripts/knowledge_base_smoke.py dc-knowledge
```

Adjust the script path to wherever this generated skill is installed.

## 2. Build or Update the Knowledge Base

Use this when the user says "build knowledge base", "update DataChain knowledge",
"refresh dataset docs", or when a data-related script just created or changed a
saved dataset.

High-level flow:

1. For referenced storage URIs, check or enlist the bucket root.
2. Plan new/stale dataset and bucket pages.
3. Snapshot datasets and bucket listings into bounded JSON intermediates.
4. Enrich snapshots into markdown pages under `dc-knowledge/`.
5. Rebuild `dc-knowledge/index.md`.
6. Clean temporary JSON unless debugging was requested.
7. Report what changed and any stale/expired bucket listings.

Do not manually edit generated pages to fake a refresh. Regeneration should be
based on the Dataset DB and storage-listing metadata.

## 3. Build C/A/S/Task Datasets

When a task needs new data work, plan with CAST:

- **Container (`l1_`)**: file listings, headers, bounded metadata, sidecars.
- **Asset (`l2_`)**: decoded units or joined/mixed raw data.
- **Sense (`l3_`)**: embeddings, classifications, transcriptions, detections,
  LLM outputs, or other model-derived signals.
- **Task (no prefix)**: task-specific filters, rankings, aggregations, eval sets,
  or curated subsets on top of C/A/S layers.

Rules of thumb:

- Read existing `dc-knowledge/` first and reuse C/A/S layers when they give a
  meaningful speed or cost win.
- If a new UDF-bearing task is not an explicit quick one-off, leave behind at
  least one reusable C/A/S layer.
- Save full reusable outputs before applying task-specific filters; filter or
  aggregate downstream.
- Use `attrs` and `description` on saved datasets so the knowledge base can
  resolve layer, scope, source, model, preset, and human intent.
- Multi-stage pipelines should be one script per stage and one `.save()` per
  script so checkpoints and lineage stay clear.

## 4. Dataset and Bucket Agent Workflows

### Existing dataset question

1. Read `dc-knowledge/index.md` and the named dataset page.
2. Confirm schema, latest version, dependencies, and preview.
3. Query the saved dataset by name; do not re-read source storage unless the
   dataset is stale or insufficient.
4. If the answer becomes reusable, save it as a Task dataset and update the
   knowledge base.

### New bucket analysis

1. Derive the bucket root from any storage URI.
2. Check access and listing status; stop on missing credentials or denied access.
3. Build the cheapest sufficient reusable layer, usually starting with a
   Container or directly with Sense when the task is semantic.
4. Rebuild `dc-knowledge/` so the bucket page and new datasets become readable
   by future sessions.

### Cross-agent handoff

1. Install the same DataChain skills into each target agent, or install them
   project-locally when the project should carry its own agent instructions.
2. Keep the Dataset DB and `dc-knowledge/` available to the agents that need to
   query prior work.
3. Treat dataset names and versions as the contract: one agent can save
   `curated_images`, another can read it by name and extend it.
4. Refresh the knowledge base after each material dataset change so the next
   agent finds the new contract before writing code.

### Jobs analytics

For Studio job questions, use the jobs workflow. It maintains
`dc-knowledge/jobs/index.md`, optionally enriches duration/cluster details with
extra API calls, and answers from the markdown table once fresh.

## 5. Memory Across Sessions

The durable memory layers are:

- saved datasets in the Dataset DB;
- markdown summaries in `dc-knowledge/`;
- target-agent skills or command/rule files that teach agents to read both.

A good final response after data work names the saved dataset(s), versions or
row counts when known, which C/A/S layer was reused or built, and whether the
knowledge base was updated. This teaches the next agent and the human what can
be reused without recomputation.
