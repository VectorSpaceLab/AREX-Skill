# Eval Gauntlet aggregation

Eval Gauntlet is an aggregation layer over completed ICL evaluator metrics. It does not run benchmarks by itself; it reads the metric keys produced by `icl_tasks` and computes composite category scores.

## Minimal config shape

`eval_gauntlet` may be inline in the offline eval YAML or a local path to a YAML containing an `eval_gauntlet:` section:

```yaml
eval_gauntlet:
  weighting: EQUAL
  subtract_random_baseline: true
  rescale_accuracy: true
  averages:
    core_average:
    - world_knowledge
    - commonsense_reasoning
    - language_understanding
  categories:
  - name: world_knowledge
    benchmarks:
    - name: mmlu
      num_fewshot: 5
      random_baseline: 0.25
    - name: triviaqa_smoke
      num_fewshot: 3
      random_baseline: 0.0
```

Required fields:

- `categories`: list of category objects.
- Each category needs `name` and `benchmarks`.
- Each benchmark needs `name`, `num_fewshot`, and `random_baseline`.

Optional fields:

- `weighting`: `EQUAL`, `SAMPLE_SZ`, or `LOG_SAMPLE_SZ`. Default-like documented configs use `EQUAL`.
- `subtract_random_baseline`: if true, subtract benchmark chance performance before averaging.
- `rescale_accuracy`: if true, and only when `subtract_random_baseline` is also true, divide by `1 - random_baseline`.
- `benchmark_sizes`: required by non-equal weighting; when using LLM Foundry's builder, sizes are derived from evaluator sample counts.
- `averages`: map from average-name to list of category names. If omitted, a default average over all categories is created.

## Category families used by published configs

The main Eval Gauntlet families in the installed examples/docs are:

- `world_knowledge`: Jeopardy, MMLU, ARC, TriviaQA, wikidata-style factual QA.
- `commonsense_reasoning`: COPA, PIQA, OpenBookQA, SIQA, CommonsenseQA, BIG-bench commonsense tasks.
- `language_understanding`: LAMBADA, HellaSwag, Winograd/Winogrande, language identification/translation/composition tasks.
- `symbolic_problem_solving`: elementary math, Dyck languages, operators, arithmetic, GSM8K/SVAMP, LSAT/SAT math-like tasks.
- `reading_comprehension`: SQuAD, BoolQ, CoQA, LSAT/SAT reading, PubMedQA, fables.
- `programming`: HumanEval-style code tasks appear in some historical configs, but code-evaluation task support is outside this sub-skill's four required ICL families.

Some configs add derived “lite” or “lm_task_subscore” categories. Treat those as normal categories: they must have unique names and benchmark entries that match tasks that actually ran.

Long-context Gauntlet variants add tasks designed for contexts above ordinary 2K-4K lengths, such as document QA, key-value retrieval, and numeric WikiQA. For these, ensure the model, tokenizer, `max_seq_len`, and task-specific `max_seq_len` can actually support the requested lengths before launching.

## Matching rules

For Gauntlet aggregation, every benchmark entry is matched to an ICL evaluator key formed from:

```text
<task label>/<num_fewshot>-shot
```

Therefore:

- `benchmarks[].name` must equal `icl_tasks[].label` exactly.
- `benchmarks[].num_fewshot` must be present in the matching task's `num_fewshot` list.
- If `has_categories: true`, the benchmark can still aggregate; subcategory scores are averaged into the benchmark score before category-level aggregation.
- If any benchmark in a category is missing, that category is removed from the composite result and a warning is logged.

Example mismatch:

```yaml
icl_tasks:
- label: hellaswag
  num_fewshot: [0]
  icl_task_type: multiple_choice

eval_gauntlet:
  categories:
  - name: language_understanding
    benchmarks:
    - name: hellaswag
      num_fewshot: 10   # wrong: task only runs 0-shot
      random_baseline: 0.25
```

Fix by adding `10` to the task's `num_fewshot` list or changing the Gauntlet benchmark to `num_fewshot: 0`.

## Random baselines

`random_baseline` is the expected score from random guessing or near-zero chance performance:

- Four-way multiple choice: commonly `0.25`.
- Two-way multiple choice: commonly `0.5`.
- Free-response exact match and many LM continuation tasks: often `0.0`.
- Dataset-specific MC tasks may differ if choices are not balanced or choice counts vary.

When `subtract_random_baseline: true` and `rescale_accuracy: true`, each benchmark score becomes:

```text
(adjusted score) = (accuracy - random_baseline) / (1 - random_baseline)
```

For example, a four-way MC benchmark with accuracy `0.30` and random baseline `0.25` becomes:

```text
(0.30 - 0.25) / (1 - 0.25) = 0.0667
```

This expresses performance above chance on a scale whose maximum is 1.0. Scores can be below 0 when a model performs below the random baseline.

Invalid combinations:

- `rescale_accuracy: true` with `subtract_random_baseline: false` is rejected.
- `random_baseline >= 1` makes rescaling impossible.

## Weighting rules

Within each category, adjusted benchmark scores are weighted and averaged.

- `EQUAL`: every benchmark has weight 1. This is simplest and does not require sample sizes.
- `SAMPLE_SZ`: each benchmark weight is proportional to sample count. Requires benchmark sizes.
- `LOG_SAMPLE_SZ`: each benchmark weight is proportional to `max(log2(sample_count), 1)`. Requires benchmark sizes.

Offline evaluation built through LLM Foundry constructs benchmark sizes from the ICL evaluator dataloaders. For hand-authored or standalone aggregate reasoning, use `EQUAL` unless you have reliable sample counts for every benchmark.

## Named averages

`averages` maps output average names to category lists:

```yaml
averages:
  core_average:
  - world_knowledge
  - commonsense_reasoning
  - language_understanding
  stem_average:
  - symbolic_problem_solving
```

Rules:

- Average names and category names must not overlap.
- Missing/removed categories are ignored for the average; if no categories remain, the average is reported as 0.
- If `averages` is omitted, LLM Foundry creates a `default_average` over all category names.

## Reading Gauntlet results

When configured, offline eval prints a markdown table containing:

- `model_name` from the model config.
- Columns for each named average.
- Columns for individual categories.

Higher values are better for the supported accuracy metrics. Compare models by category, not only by average, because a single average can hide regressions in a specific capability area.

If expected columns are missing:

1. Check stderr/stdout warnings for missing benchmarks.
2. Ensure every category benchmark has a corresponding completed ICL task label and few-shot count.
3. Ensure full eval actually ran; `icl_subset_num_batches` can be useful for smoke tests, but it changes metric stability.
4. Ensure task metric names contain `Accuracy`; the markdown summary and Gauntlet extraction ignore non-accuracy metrics.

## Building custom Gauntlets

For a custom benchmark suite:

1. Start with task configs and local JSONL rows that pass [task-schemas.md](task-schemas.md).
2. Decide categories that users can act on, not just dataset sources.
3. Assign a random baseline per benchmark.
4. Keep `weighting: EQUAL` unless sample-size weighting is explicitly desired.
5. Add named averages only when they will be interpreted consistently.
6. Run `scripts/llmfoundry_eval_config_lint.py` and fix missing task/Gauntlet matches before launching.

A small custom suite can be as useful as a large one if it has clear categories, stable prompts, and a documented random baseline.
