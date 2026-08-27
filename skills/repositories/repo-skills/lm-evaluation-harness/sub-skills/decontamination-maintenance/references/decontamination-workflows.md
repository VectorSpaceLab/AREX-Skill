# Decontamination Workflows

## Concepts

Decontamination checks whether evaluation examples overlap with model training data. LM Evaluation Harness supports a GPT-3-style ngram workflow: task documents are converted into ngrams, compared against precomputed training-set ngram buckets, and contaminated document IDs can be excluded from clean metrics. The default ngram size used by the documented Pile workflow is 13.

Decontamination is not a normal evaluation default. It requires prepared training-data ngram artifacts and can introduce large I/O costs. For most agent tasks, start with static configuration review and only recommend full scans when the user already has the artifacts and accepts the runtime/disk implications.

## Task YAML fields

Task YAMLs expose two key fields:

- `should_decontaminate`: boolean; defaults to `false` if omitted.
- `doc_to_decontamination_query`: string, Jinja expression, feature name, or function reference used to build the text checked for contamination.

Review rules:

- If `should_decontaminate: true`, require a non-empty `doc_to_decontamination_query` unless the task implementation deliberately falls back to `doc_to_text`.
- If `should_decontaminate: false`, flag a populated query as informational only; it may be staged for later, but it is inactive.
- Prefer stable source fields such as question, passage, story, context, page, sentence, or text over target labels alone.
- For multiple-choice tasks, include enough context and question text to identify the example, but avoid answer-only queries.
- Preserve YAML quoting carefully; double quotes process escapes like `\n`, while single quotes preserve the literal backslash-n pair.

Use `../scripts/check_decontamination_config.py` for static review:

```bash
python ../scripts/check_decontamination_config.py path/to/task.yaml
```

The checker is intentionally conservative: it does not import task code, execute `!function` references, or download datasets.

## Runtime decontamination artifact shape

A prepared ngram directory should contain:

- `info.json` with an `ngram_size` entry, typically `13`.
- Sorted compressed bucket files matching the training-data ngram output pattern, such as `*.sorted.zst`.

Missing `info.json`, missing sorted buckets, or a mismatched ngram size should be treated as a setup issue before any evaluation attempt.

## Clean-training-data pipeline safety

The clean-training-data scripts are reference-only for normal agent work. They are not bundled here and should not be run by default because they depend on large training corpora, huge disk/network consumption, optional compiled helpers, and multi-day generation/sort/package steps.

If a user asks to run the Pile pipeline, classify it as unsafe/heavy unless they explicitly confirm:

- They have legal access to the training corpus and enough local storage.
- They accept multi-day wall-clock time for ngram generation and sorting.
- They set `PYTHONHASHSEED=0` for reproducible bucket hashing.
- They have a separate working directory and final artifact directory.
- They understand the output is an artifact set for later evaluation, not an ordinary task YAML change.

Safer default response: explain the risk, inspect YAML fields statically, and give an artifact checklist rather than launching the pipeline.

## Static review checklist

- Confirm all modified task YAMLs parse as YAML, or explicitly note custom tags such as `!function` that require repository loaders.
- Confirm `should_decontaminate` is a boolean-like value, not a quoted ambiguous string.
- Confirm enabled tasks have a non-empty query.
- Check whether queries reference likely source fields rather than labels or targets.
- Check newline quoting if the query includes prompt framing such as `Question: {{question}}\nAnswer:`.
- Route broader task authoring questions to `../task-authoring/`.
