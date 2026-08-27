# LLM Judge and Subjective Evaluation

## When to Use LLM-as-Judge

Use an LLM judge when exact-string or rule-based evaluators are too brittle: free-form QA, factual responses with varied wording, open-ended answer quality, or tasks where model output lacks clean option identifiers. Keep rule-based metrics when the answer format is stable, cheaper, and auditable.

OpenCompass provides two relevant paths:

- `GenericLLMEvaluator`: asks a judge model to score each prediction and then postprocesses judge output into metrics.
- Subjective evaluation configs and summarizers: compare or score model responses using judge models for preference-oriented benchmarks.

## `GenericLLMEvaluator` Data Flow

A single-model LLM-judge evaluation usually has:

1. A dataset reader with question/input columns and a reference output column.
2. A normal model inference config that produces `prediction` values.
3. An evaluation config whose evaluator is `GenericLLMEvaluator`.
4. A judge prompt template that includes original input, reference answer, and model prediction.
5. A judge model config supplied in `judge_cfg`, or environment variables used by the evaluator fallback.
6. A `dict_postprocessor`, commonly `generic_llmjudge_postprocess`, to convert judge text into a numeric metric.

A compact evaluator shape is:

```python
eval_cfg = dict(
    evaluator=dict(
        type=GenericLLMEvaluator,
        prompt_template=dict(type=PromptTemplate, template=dict(round=[dict(role='HUMAN', prompt=JUDGE_TEMPLATE)])),
        dataset_cfg=dict(type=CustomDataset, path='data/my_eval', file_name='qa.jsonl', reader_cfg=reader_cfg),
        judge_cfg=judge_model[0],
        dict_postprocessor=dict(type=generic_llmjudge_postprocess),
    ),
    pred_role='BOT',
)
```

If `judge_cfg` is an empty dict or otherwise not provided, `GenericLLMEvaluator` reads judge settings from:

- `OC_JUDGE_MODEL`
- `OC_JUDGE_API_KEY`
- `OC_JUDGE_API_BASE` optional, defaulting to an OpenAI-compatible base URL when omitted

For public reusable configs, prefer a placeholder or empty `judge_cfg` plus documented environment variables. Never commit API keys in dataset configs, skill content, examples, or summary artifacts.

## Judge Output Contract

The generic judge postprocessor documented for OpenCompass expects the judge to answer with `A` for correct or `B` for incorrect. Prompts that ask for words such as “CORRECT” and “INCORRECT” can fail postprocessing unless a different dict postprocessor is configured.

Checklist for reliable generic judge scoring:

- The judge template explicitly says which label means correct and which label means incorrect.
- The model response is inserted as `{prediction}` and the reference answer is inserted from the dataset output/reference column.
- `dict_postprocessor` matches the expected judge output format.
- `pred_postprocessor`, if used, is deterministic and appropriate for the model's output format.
- `--dump-eval-details` is enabled when diagnosing individual judge prompts or decisions.

## Credential-Safe JSONL QA Judge Case

For a user request like “Add LLM judge eval for JSONL QA while keeping credentials out of config,” use this pattern:

```python
reader_cfg = dict(input_columns=['problem'], output_column='answer')

judge_cfg = dict()  # resolved from OC_JUDGE_MODEL, OC_JUDGE_API_KEY, OC_JUDGE_API_BASE

JUDGE_TEMPLATE = """
Question: {problem}
Reference Answer: {answer}
Model Response: {prediction}
If the model response correctly answers the question, answer A. Otherwise answer B.
Answer with only A or B.
""".strip()
```

Then wire `CustomDataset` with the JSONL location, normal `GenInferencer` for the model being evaluated, and `GenericLLMEvaluator` for scoring. Document the required environment variables in private run instructions, not in committed config values.

## CascadeEvaluator

`CascadeEvaluator` combines a rule evaluator and an LLM judge:

- Cascade mode (`parallel=False`) runs the rule evaluator first, then sends only rule-failed samples to the LLM judge. This reduces cost and keeps rule-based correctness as the first pass.
- Parallel mode (`parallel=True`) runs both and accepts a sample if either evaluator marks it correct. This is more lenient and more expensive.

Use cascade mode when a rule evaluator is mostly reliable but misses semantically correct variants. Use parallel mode only when the evaluation policy intentionally allows either judgment source.

## Subjective Evaluation Concepts

Subjective evaluation targets human-preference-like quality rather than exact correctness. OpenCompass supports two broad modes:

- Compare mode: pairwise comparison of model responses, reporting win rates or preference-oriented summaries.
- Score mode: single-response scoring, often with a judge model and benchmark-specific rubric.

Typical subjective benchmarks include AlignBench, MT-Bench, MT-Bench101, AlpacaEval, ArenaHard, FoFo, WildBench, and related dataset-specific summarizers.

## Subjective Config Anatomy

Subjective configs often differ from objective configs in three places:

- Models under evaluation may use sampling (`generation_kwargs=dict(do_sample=True)`) instead of greedy decoding.
- Judge models may be separate from the evaluated models and may use API-backed or locally served chat models.
- Evaluation partitioners can be configured separately for inference/evaluation work splitting.

For custom subjective datasets:

1. Prepare records with fields such as `question`, `capability`, and `others`, or follow the selected benchmark's dataset class requirements.
2. Implement or select a subjective dataset reader that returns a list of dictionaries.
3. Configure inference prompts for response generation.
4. Configure evaluation prompts and judge models for compare or score mode.
5. Use the benchmark-specific subjective summarizer when available.

Multi-turn subjective datasets store dialogue turns as alternating user/assistant messages. Some MT-Bench-style configs split subsets by temperature because different question categories require different sampling settings.

## Subjective Output Layout

Subjective evaluation commonly writes judge responses under result paths that include the evaluated model, dataset, and judge model. The default subjective summarizer reads judge-specific result folders, including names with `judged-by--<judge_abbr>`, and can average across base models when a dataset config defines `base_models`.

When a subjective score is missing:

- Check whether judge inference completed and produced judge response files.
- Check the judge abbreviation embedded in result directory names.
- Check whether `base_models`, `compare_models`, and `judge_models` abbreviations match the summarizer's expected naming.
- Check whether the dataset-specific subjective summarizer is required rather than the default objective summarizer.

## Interpreting LLM-Judge Metrics

LLM-judge `accuracy` means “percentage judged correct by the configured judge policy,” not necessarily objective truth. Always report:

- The judge model or judge service family if available.
- The prompt/rubric shape, especially A/B labels or score scale.
- Whether the run used rule-only, LLM-only, cascade, or parallel judging.
- Whether details were dumped and sampled for sanity.
- Any known judge bias controls, such as pair order checks for compare mode.
