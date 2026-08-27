---
name: benchmark-evaluation
description: "Validate DeepResearch benchmark rollout files and choose official
  evaluation routes before spending judge API credits."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Benchmark Evaluation

Use this sub-skill when a future agent already has DeepResearch prediction rollout
files and needs to decide whether they are ready for official LLM-as-judge
evaluation. It is a guidance and preflight skill: it does not generate
predictions and it does not call external judge APIs.

## Route to this sub-skill when

- The task mentions `evaluate_deepsearch_official.py`,
  `evaluate_hle_official.py`, pass@k, HLE, GAIA, BrowseComp, WebWalker,
  XBench DeepSearch, scored JSONL, or judge-model costs.
- A rollout folder contains `iter1.jsonl`, `iter2.jsonl`, `iter3.jsonl`, or
  split-suffixed files such as `iter2_split3of8.jsonl`.
- The user wants to inspect malformed JSONL, missing predictions/messages,
  invalid `<answer>...</answer>` tags, missing round files, or termination
  frequencies before running official judging.

## Do not use this sub-skill for

- Creating DeepResearch predictions or running the ReAct agent; route to the
  sibling `react-inference` sub-skill.
- Choosing among WebAgent family projects or understanding their project-specific
  evaluators; route to `webagent-family`, then return here for common rollout and
  LLM-judge concepts.
- Replacing the official judge scripts. The bundled validator is a safe schema
  preflight only, not an implementation of official benchmark metrics.

## Fast safe preflight

From this sub-skill directory, validate an unsplit DeepResearch rollout folder:

```bash
python scripts/validate_prediction_rollouts.py <rollout-folder> --dataset gaia
```

Validate distributed rollouts written by `run_multi_react.py --total_splits N`:

```bash
python scripts/validate_prediction_rollouts.py <rollout-folder> --dataset webwalker --allow-splits
```

Validate an HLE single JSONL file before the HLE judge route:

```bash
python scripts/validate_prediction_rollouts.py <hle-predictions.jsonl> --dataset hle
```

A passing validator result means the files satisfy local shape checks. It does
not mean the official LLM judge has run or that pass@k metrics are available.

## Read next

- `references/prediction-format.md` for rollout file names, fields, split
  behavior, and validator interpretation.
- `references/evaluation-workflows.md` for official DeepSearch and HLE evaluator
  routes, judge-model selection, metrics, and output files.
- `references/troubleshooting.md` for missing rounds, malformed JSON, absent
  fields, invalid answer tags, unsupported datasets, missing API variables, and
  tokenizer caveats.
