---
name: evaluation-and-optimization
description: "Guide AdalFlow evaluation metrics, datasets, parameters,
  gradients, prompt/few-shot/text-grad optimization, AdalComponent, Trainer, and
  optimize_anything workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# AdalFlow evaluation and optimization

Use this sub-skill when the user wants to score task outputs, select or load AdalFlow benchmark datasets, make `Parameter` objects trainable, wrap a task in `AdalComponent`, run `Trainer.diagnose` or `Trainer.fit`, configure few-shot/text-gradient optimizers, or use `optimize_anything` for bounded text-artifact search.

## Route boundaries

Stay here for:

- `AnswerMatchAcc`, `RetrieverEvaluator`, and cautious `LLMasJudge` evaluation.
- Dataset loaders for GSM8K, TREC, HotpotQA, and BBH-style tasks, including small-size and skip-expensive guidance.
- `Parameter`, `ParameterType`, `GradComponent`, `EvalFnToTextLoss`, `LLMAsTextLoss`, `BootstrapFewShot`, `TGDOptimizer`, `AdalComponent`, `Trainer`, and `optimize_anything` workflows.

Route away instead of duplicating guidance:

- RAG construction, document splitting, local/vector retrievers, and index pipelines: use `retrieval-rag-and-data-pipelines`.
- Provider model-client configuration, credentials, `Generator`, and fake provider clients: use `model-client-and-generator-workflows`.
- Tracing/logging artifacts and callback storage: use `tracing-observability-and-configuration`.

## Reference map

- [Evaluation metrics](references/evaluation-metrics.md): metric APIs, input shapes, output objects, and no-network smoke examples.
- [Optimization and training](references/optimization-and-training.md): `Parameter`/gradient concepts, `AdalComponent` contracts, `Trainer.fit`/`diagnose`, few-shot/text-gradient optimizer setup, and `optimize_anything`.
- [Datasets and benchmarks](references/datasets-and-benchmarks.md): loader classes, fields, optional dependencies, downloads, and benchmark constraints.
- [Troubleshooting](references/troubleshooting.md): evaluator shape errors, metric extras, dataset misses, checkpoint/resume, validation-set requirements, provider cost, runtime limits, and multiprocessing issues.
- [Metric smoke script](scripts/evaluation_metrics_smoke.py): service-free exact/fuzzy/F1/retriever metric check.

## Safe operating defaults

1. **Score before optimizing.** Build a deterministic metric with `AnswerMatchAcc` or `RetrieverEvaluator` and run a tiny local smoke case before any model-backed judge or optimizer.
2. **Treat live judging and text gradients as expensive.** `LLMasJudge`, `LLMAsTextLoss`, backward engines, teacher generators, and `TGDOptimizer` can invoke model providers. Require explicit provider setup, credentials, budget, sample limits, and cache/checkpoint choices.
3. **Use bounded data.** Dataset loaders may download external data and optional packages. Prefer `size=...` or pre-existing local data for first tests.
4. **Make `AdalComponent` contracts explicit.** `prepare_task` returns `(callable, kwargs)` for one sample; `prepare_eval` returns `(eval_fn, kwargs)` for inference scoring; `prepare_loss` returns `(loss_fn, kwargs)` with `Parameter` inputs and correct `eval_input` values.
5. **Prefer diagnosis before training.** `Trainer.diagnose` is useful for identifying failing samples and prompt/output issues. Use `num_workers=1` for minimal debugging, then raise concurrency only after stable.
6. **Do not imply full benchmark training is safe.** Benchmark scripts and full prompt optimization runs are optional, network/provider/dataset dependent, and should be reduced to a tiny user-approved run before scaling.

## Minimal decision checklist

- What is being scored: final answer strings, structured labels, retrieved contexts/IDs, or model-judged quality?
- Is the metric service-free, optional-package-backed, or provider-backed?
- Are predictions raw values, `GeneratorOutput.data`, or `Parameter.full_response.data`?
- Are trainable values marked with the right `ParameterType` (`PROMPT` for instructions, `DEMOS` for examples)?
- Does the training data provide stable `id` fields and a real validation set?
- What are the maximum samples, optimizer steps, worker count, and checkpoint/resume plan?
