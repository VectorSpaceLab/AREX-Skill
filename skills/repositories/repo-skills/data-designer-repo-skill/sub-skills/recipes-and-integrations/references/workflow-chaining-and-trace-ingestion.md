# Workflow Chaining, Human Review, and Trace Ingestion

## Purpose

Read this when adapting a recipe that runs multiple DataDesigner stages, pauses for external review, resumes from a reviewed artifact, or turns assistant traces into supervised fine-tuning rows. Use [`../../generation-runtime/SKILL.md`](../../generation-runtime/SKILL.md) for exact runtime method signatures and execution steps.

## Composite workflow pattern

DataDesigner exposes workflow chaining at the interface layer through `DataDesigner.compose_workflow(name=...)`. The workflow API is experimental, so adapted plans should keep stage names, artifact paths, and resume decisions explicit.

Typical shape:

```python
data_designer = DataDesigner(artifact_path=artifact_root)
workflow = data_designer.compose_workflow(name="review_flow")
workflow.add_stage("stage_one", builder_one, num_records=small_n)
workflow.add_stage("stage_two", builder_two, num_records=small_n)
results = workflow.run(resume=dd.ResumeMode.NEVER)
```

Important concepts:

- Stages run linearly; each downstream stage is seeded from the selected output of the previous stage.
- `add_stage(...)` can choose stage output through final output, named processor output, or an `on_success` callback that returns a parquet file/directory.
- `run(...)` supports resume, selected targets, rerun-from, and `stage_output_overrides` so an external artifact can replace a completed stage output.
- `CompositeWorkflowResults` can load the final selected output, load a named stage output, count stage output records, export the final selected output, or export a named stage.
- `CompositeWorkflowResults.push_to_hub(...)` only delegates to the final stage result when the final selected output is the final stage's actual dataset path. If a stage output override or selected processor output is used, export the selected output or push the stage result directly.

## Human review gate pattern

The review-gate recipe demonstrates a local, test-backed pattern without needing remote models:

1. Generate or load local source artifacts and metadata.
2. Validate the metadata before building a workflow.
3. Run the workflow only to the review-candidate stage.
4. Export `review_candidates` to a parquet artifact for external review.
5. Create or ingest a `reviewed_candidates` parquet with human annotations.
6. Resume the workflow with `stage_output_overrides={"review_candidates": reviewed_path}`.
7. Export the final selected output.

A good adapted review gate keeps these columns or equivalents visible:

| Concept | Example column | Why it matters |
| --- | --- | --- |
| Stable row key | `page_id` | Joins machine output, review candidates, and reviewed rows |
| Source media/artifact | `image_path` or seed file reference | Lets reviewers inspect the same item that generation saw |
| Machine prediction | candidate boxes, labels, confidences | Reviewable output before human override |
| Review selection flag | `selected_for_review` | Makes reviewed vs skipped rows auditable |
| Human annotation | `human_boxes` or reviewed fields | The external override artifact |
| Provenance/source | `source` such as `human_review` vs machine | Distinguishes which value won in final data |

Local dry-run checks should validate:

- artifact directory does not already contain data unless overwrite is intentional;
- sample image files or local seed artifacts exist;
- review candidate parquet has the expected row count and key columns;
- reviewed parquet covers the selected rows and leaves skipped rows explicit;
- bounding boxes or structured annotations fit within media dimensions when applicable;
- final exported parquet has one row per source item and marks rows that used human review.

Do not simulate real human approval if the user needs actual compliance, safety, or labeling sign-off. Produce the artifact contract and ask how reviewed data will be provided.

## Trace ingestion pattern

DataDesigner has an `AgentRolloutSeedSource` for assistant trace formats. The trace-distillation recipe uses it to convert traces into compact training examples.

Supported built-in formats include:

| Format value | Default path behavior | File pattern behavior |
| --- | --- | --- |
| `atif` | Requires an explicit trace directory | Defaults to `*.json` |
| `claude_code` | Can use the default Claude Code projects location | Defaults to `*.jsonl` |
| `codex` | Can use the default Codex sessions location | Defaults to `*.jsonl` |
| `hermes_agent` | Can use the default Hermes sessions location | Defaults to `*.json*` |
| `pi_coding_agent` | Can use the default Pi coding-agent sessions location | Defaults to `*.jsonl` |

A distilled trace recipe usually follows this column graph:

1. Seed from normalized trace rows.
2. Generate a structured `trace_digest` summarizing task, context, actions, useful outcome, training value, and quality notes.
3. Generate a structured `sft_record` with standalone instruction, response, tags, and difficulty.
4. Judge the candidate record with multiple rubric scores for groundedness, standalone task, response quality, faithfulness, and training utility.
5. Flatten fields with expression columns such as instruction, response, tags, numeric scores, trace training value, and a boolean `recommended_for_sft`.

Execution is usually credentialed because the digest, SFT record, and judge columns call a model provider. It may also read private local traces. Treat trace ingestion as sensitive by default.

## Safe trace-ingestion preflight

Before running any trace distillation:

- Confirm the user authorizes reading the trace directory. Default trace locations can contain private repository paths, chat contents, tool logs, credentials, or incident data.
- For `atif`, require an explicit `--trace-dir`; do not invent one.
- For default-path formats, report that the format has a default path but ask before scanning it.
- Count matching files and sample only metadata/shape until the user approves content processing.
- Use partitioning (`PartitionBlock`) or small `num_records` for large trace corpora.
- Decide whether to preserve, redact, or drop fields like project path, working directory, branch, source metadata, and final messages.
- If model/API keys are absent, produce a config plan and local trace manifest only.

## Workflow chaining with trace ingestion

A trace-ingestion workflow can chain stages safely when each stage writes a parquet artifact:

1. Stage 1: normalize trace rows or build a filtered seed table.
2. Stage 2: digest and generate candidate SFT rows.
3. Stage 3: judge/score candidates.
4. Stage 4: optionally export only high-confidence rows for human review.

When adding human review, use a reviewed artifact override rather than mutating the prior stage output in place. Keep original trace identifiers and review decisions separate so downstream filtering remains auditable.

## When to stop at a plan

Stop before execution and return a reference-only plan when any of these are true:

- The workflow needs remote model aliases and `data-designer agent context` shows no usable aliases.
- The trace source may include private data and the user has not authorized reads.
- The workflow requires a human review artifact that does not exist yet.
- The stage output override points to a non-existent, empty, or schema-incompatible parquet file.
- The requested target is to publish trace-derived data without a privacy review.
- Running the recipe would mutate or delete an existing artifact directory without explicit overwrite approval.

## Minimal dry-run report shape

For a safe local artifact-only plan, return:

- workflow name and stage names;
- expected input seed columns;
- expected intermediate artifact files;
- reviewed artifact schema;
- final output schema/row-count expectations;
- model/API aliases that would be needed for actual generation;
- which checks were local and which remain unverified.
