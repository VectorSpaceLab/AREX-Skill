---
name: results-and-analysis
description: "Interpret OpenCompass summaries, result tables, summary_groups,
  subjective/LLM-judge outputs, result-station reuse, repeat analysis, and
  post-run diagnostics."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# OpenCompass Results and Analysis

Use this sub-skill when an OpenCompass task is about reading, explaining, or post-processing outputs after inference/evaluation has produced `predictions/`, `results/`, or `summary/` files.

## Route Here For

- Explaining summary table columns: `dataset`, `version`, `metric`, `mode`, model score columns, and `-` placeholders.
- Debugging missing aggregate rows from `summarizer.dataset_abbrs` or `summarizer.summary_groups`.
- Choosing or interpreting objective metrics such as accuracy, exact match, BLEU, ROUGE, toxicity, pass rates, F1, AUC, and dataset-specific metrics.
- Configuring or diagnosing `GenericLLMEvaluator`, `CascadeEvaluator`, judge environment variables, and subjective evaluation summaries.
- Reading `--mode viz`, `--reuse`, result-station read/write behavior, case analysis outputs, and repeat-analysis reports.

## Route Elsewhere

- Dataset creation, custom dataset readers, `abbr`, `reader_cfg`, and config import structure belong in `../configuration-and-datasets/SKILL.md`.
- Launch commands, runner setup, `--mode all/infer/eval/viz`, `--debug`, and `--dry-run` belong in `../evaluation-workflows/SKILL.md`.
- Prompt templates, retrievers, `GenInferencer`/`PPLInferencer`, and answer masking belong in `../prompt-and-inference/SKILL.md`.
- Model backend installation, acceleration, HuggingFace/API adapters, and real inference environment issues belong in `../model-backends/SKILL.md`.

## Start Here

1. Locate the active run directory, then inspect `summary/summary_*.txt`, `summary/summary_*.csv`, `results/<model>/<dataset>.json`, and `predictions/<model>/<dataset>*.json`.
2. If a summary cell is `-`, first check whether the dataset or metric exists in `results/`; then check `dataset_abbrs`, `summary_groups`, metric names, and model abbreviations.
3. If a group row is absent or has `-`, verify that every listed subset has a parsed numeric metric for every model; one missing subset prevents that model's group aggregate.
4. For LLM-judge or subjective runs, inspect the judge-specific result directories and keep API keys in environment variables or a private runtime secret source, not in reusable public configs.
5. For repeated or suspicious generations, use `scripts/analyze_repeat_results.py` on exported prediction JSON/JSONL/CSV fixtures before escalating to full native repeat analysis.

## References

- `references/summarizers-and-results.md`: result table semantics, metric selection, `summary_groups`, result files, reuse/viz interpretation, case and multi-model analysis.
- `references/llm-judge-and-subjective.md`: `GenericLLMEvaluator`, cascade judging, subjective compare/score modes, judge credentials, and output locations.
- `references/troubleshooting.md`: missing cells, incompatible versions, mixed modes, judge env vars, postprocessor failures, and result-station overwrite/read flags.
- `scripts/analyze_repeat_results.py`: self-contained repeat-pattern analyzer for tiny JSON, JSONL, or CSV prediction fixtures.

## Safety Notes

- Do not claim real HuggingFace model execution was verified merely because result files or CLI help are inspectable.
- Treat `version` hashes as comparability guards: mixed prompt/eval settings can make two numeric scores non-comparable even when dataset names match.
- Keep judge credentials out of runtime skill content, committed configs, logs, summary artifacts, and copied examples.
