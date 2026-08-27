# Troubleshooting evaluation and optimization

Use this guide when AdalFlow metrics, datasets, `AdalComponent`, or `Trainer` runs fail. Start with service-free metric checks, then isolate dataset, task-call, evaluator, and optimizer issues one at a time.

## Fast isolation flow

1. Run `scripts/evaluation_metrics_smoke.py` to prove core metrics import and behave as expected.
2. Score two hand-written predictions with the intended metric.
3. Call `adal_component.prepare_task(sample)` for one sample and inspect the returned callable/kwargs without invoking a provider unexpectedly.
4. Run one inference call and pass its output to `prepare_eval`.
5. If training, call `prepare_loss` for one sample and confirm all loss kwargs are `Parameter` objects with correct `eval_input`.
6. Only then run `Trainer.diagnose` or `Trainer.fit` on a tiny dataset with `num_workers=1`.

## Common failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| `AnswerMatchAcc.compute` gives a surprising average | Predicted and ground-truth lists have different lengths; `compute` zips and ignores unmatched tail items. | Check equal lengths before calling; print paired `(pred, gt)` values. |
| Exact match fails for a visually similar answer | Normalization removes case, punctuation, articles, and whitespace, but not synonyms or numeric format differences. | Extract a cleaner final answer, choose fuzzy/F1, or write a task-specific normalizer. |
| Rouge/BLEU/BERTScore metric import fails | Optional `torchmetrics`/model dependencies are missing. | Use `exact_match`, `fuzzy_match`, or `f1_score` for smoke runs; install metric extras only when needed. |
| BERTScore or other semantic metric is slow | Model-backed metric downloads/loads model weights. | Use a sample limit; cache model files; do not put this in default CI/smoke checks. |
| `RetrieverEvaluator` raises division by zero | Empty retrieved list or empty ground-truth list. | Validate per-query lists before scoring; represent no retrieval as a defined custom score if needed. |
| Retriever recall is lower than expected | Evaluator uses normalized exact set intersection, not substring/semantic matching. | Compare IDs/titles instead of full passages, or implement a custom evaluator. |
| `LLMasJudge` tries to use a provider unexpectedly | No custom `llm_judge` was provided, so the default model-backed judge is constructed. | Route provider setup first or pass a deterministic/custom judge component for tests. |
| Model-judge scores vary | LLM judging is non-deterministic and prompt-sensitive. | Use low temperature, caching, a fixed rubric, manual audit samples, and multiple runs if high-stakes. |
| Dataset loader import fails | Optional `datasets` or `torch` packages are missing. | Install the needed extras or replace with tiny synthetic examples exposing the same fields. |
| Dataset loader downloads too much data | Cache missing and full benchmark loader started. | Stop, set `size` where supported, use a user-approved cache root, or pre-create local tiny data. |
| `ValueError: val_dataset should be provided` in `Trainer.fit` | `fit` requires a validation dataset even if test data exists. | Provide a small validation split; for a smoke run, use a tiny held-out list distinct from training examples when possible. |
| `train_loader or train_dataset should be provided` | No training source was passed to `fit`. | Pass `train_dataset`, `train_loader`, or set them in `Trainer(...)`. |
| `Task should be an instance of AdalComponent` | `Trainer` received a raw task pipeline instead of a wrapper. | Create a subclass of `AdalComponent` implementing `prepare_task` and `prepare_eval`. |
| Eval step says prediction is a `Parameter` | Task is still in training/forward mode during inference. | Ensure eval calls use `task.call`/`task.bicall` as intended and `AdalComponent` switches task to eval mode. |
| Training step says prediction is not a `Parameter` | Training path called inference `call` instead of trainable `forward`/`bicall`. | In `prepare_task`, use a callable that returns a `Parameter` when the task is in training mode. |
| `EvalFnToTextLoss: All inputs must be Parameters` | `prepare_loss` passed raw strings/numbers in `kwargs`. | Wrap prediction and ground truth as `Parameter` objects; set `requires_opt=False` for ground truth. |
| Loss/eval gets wrong values | `eval_input` not set or points to full response instead of extracted answer/label. | Set `y_pred.eval_input` to the scalar/string the evaluator expects; set `y_gt.eval_input` too. |
| Backward/text optimizer complains about missing model client/kwargs | Text gradients require a backward engine or model config. | Route provider setup; populate `backward_engine_model_config` and `text_optimizer_model_config`, or disable backward for debug. |
| Prompt optimizer makes costly calls | `TGDOptimizer` and backward engine are model-backed. | Require a user-approved model, max steps, max proposals, worker count, and budget. Start with `max_steps=1`. |
| Few-shot optimizer says dataset/raw/bootstrap shots missing | `BootstrapFewShot` needs a dataset and configured `raw_shots`/`bootstrap_shots`. | Pass `train_dataset` to `Trainer.fit`; set shot counts in `Trainer` or optimizer. |
| Weighted few-shot sampling raises score errors | Scores must be floats in `[0, 1]` and present for weighted augmented demos. | Use unweighted sampling first or ensure teacher/student scores are recorded for every demo id. |
| Checkpoint resume restores unexpected prompt | Resume chooses prompt data from the best validation score in the checkpoint. | Inspect checkpoint summary, confirm validation scores, and use the desired checkpoint file explicitly. |
| Checkpoint path fails or is unwritable | Path missing, permission denied, or unsuitable default location. | Ask the user for a writable checkpoint directory; do not hard-code local private paths in reusable code. |
| `Trainer.diagnose` fails because sample has no `id` | Diagnosis sorts and aligns logs by sample ids. | Add stable ids to dataset items and pass ids through task calls. |
| Diagnose log alignment error | Generator output id does not match sample id. | Ensure `prepare_task` passes `id=sample.id` and the task preserves it in outputs. |
| Run appears hung with multiple workers | Threaded provider calls, dataset transforms, or notebook event loops can deadlock or saturate rate limits. | Retry with `num_workers=1`; disable multiprocessing/thread-heavy data transforms; then increase cautiously. |
| Max-step run takes too long | `max_steps`, batch size, proposal count, validation size, or provider latency too high. | Reduce `max_steps`, `train_batch_size`, `max_proposals_per_step`, validation size, and worker count; use early `stop_score` for `optimize_anything`. |
| `optimize_anything` evaluator error | Evaluator returned a dict without `score`, a non-numeric score, or raised internally. | Return `float`, `int`, or `{"score": float_value}`; add small evaluator unit tests before search. |

## Safe debug recipes

### Metric-only smoke

```bash
python scripts/evaluation_metrics_smoke.py
```

Expected: the script prints a small JSON object with exact, fuzzy, F1, and retriever metric results and exits 0.

### Tiny `AdalComponent` validation

- Build two synthetic samples with `id`, input field, and answer/label.
- Use `AnswerMatchAcc(type="exact_match")`.
- Run `prepare_eval` manually before constructing `Trainer`.
- If task inference needs a provider, use a fake deterministic task until provider configuration is complete.

### Cheap diagnosis

```python
trainer = adal.Trainer(adaltask=adal_component, num_workers=1)
trainer.diagnose(dataset=tiny_dataset, split="debug")
```

Use this to inspect failures before any text-gradient run. If diagnosis fails, fix task/eval plumbing before adding `loss_fn` or optimizers.

### One-step optimization smoke

```python
trainer = adal.Trainer(
    adaltask=adal_component,
    max_steps=1,
    train_batch_size=1,
    num_workers=1,
    raw_shots=0,
    bootstrap_shots=1,
    debug=True,
)
ckpt, result = trainer.fit(
    train_dataset=tiny_train,
    val_dataset=tiny_val,
    debug=True,
)
```

Run this only after provider-backed backward/text optimizer configuration is explicit and budget-approved.

## Review questions before scaling

- Is the chosen metric aligned with the task output, or are we optimizing to a proxy that can be gamed?
- Are parser failures assigned a clear sentinel value and included in scores?
- Does the validation set represent the target behavior, or should a separate held-out set be created?
- Are prompt and demo parameters named/described clearly enough for the optimizer?
- Is the run bounded by max examples, max steps, max proposals, and a provider budget?
- Is there a resume plan if the run is interrupted after checkpoint files are written?
