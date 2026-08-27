# FastReID evaluation and metric outputs

Use this reference for eval-only commands, the default evaluation loop, ReID
metrics, AQE/rerank options, and metric output interpretation.

## Eval-only flow

The standard eval-only path performs:

1. Merge config and `opts`.
2. Defrost the config and set `MODEL.BACKBONE.PRETRAIN = False` so model
   construction does not request backbone pretraining.
3. Build the model with `DefaultTrainer.build_model(cfg)`.
4. Load the local checkpoint from `cfg.MODEL.WEIGHTS` with `Checkpointer`.
5. Call `DefaultTrainer.test(cfg, model)`.

Eval-only still needs the configured test dataset. It is not a pure checkpoint
inspection command.

## DefaultTrainer.test

`DefaultTrainer.test(cfg, model)` loops over every name in `cfg.DATASETS.TESTS`:

1. Build the test loader and evaluator with `build_evaluator`.
2. Run `inference_on_dataset(model, data_loader, evaluator,
   flip_test=cfg.TEST.FLIP.ENABLED)`.
3. On the main process, add a `dataset` field and print CSV-style metrics.
4. Return a single metrics dictionary for one test dataset, or an ordered mapping
   from dataset name to metric dictionary when multiple test datasets are used.

Override `build_evaluator` if a custom dataset needs a custom evaluator, but
preserve the return shape `(data_loader, evaluator)`.

## ReidEvaluator

`ReidEvaluator(cfg, num_query, output_dir=None)` expects the test loader to emit
batches with at least:

- `images`: model input tensor;
- `targets`: person IDs;
- `camids`: camera IDs.

During `process(inputs, outputs)`, features are moved to CPU as `float32`, and
person/camera IDs are accumulated. During `evaluate()`:

1. Predictions are gathered across distributed ranks.
2. Features are split into query and gallery sections using `num_query`.
3. Optional average query expansion (AQE) is applied when enabled.
4. A distance matrix is built with `cfg.TEST.METRIC`.
5. Optional reranking combines Jaccard and original distances.
6. Rank metrics are computed with `fastreid.evaluation.rank.evaluate_rank`.
7. An ordered result dictionary is returned.

The top-level evaluation package in this version does not export
`evaluate_rank`; import it from `fastreid.evaluation.rank` in custom code.

## Metrics

Default ReID metrics are:

| Metric | Meaning |
|---|---|
| `Rank-1` | CMC rank-1 retrieval accuracy, percentage. |
| `Rank-5` | CMC rank-5 retrieval accuracy, percentage. |
| `Rank-10` | CMC rank-10 retrieval accuracy, percentage. |
| `mAP` | Mean average precision, percentage. |
| `mINP` | Mean inverse negative penalty, percentage. |
| `metric` | FastReID's selection metric: `(mAP + Rank-1) / 2`. |
| `TPR@FPR=...` | Optional ROC true positive rate at selected false positive rates when ROC is enabled. |

Training checkpoints use `metric` to choose `model_best.pth`. If multiple test
datasets are configured, metric flattening uses dataset-prefixed keys such as
`DatasetName/metric`.

## `inference_on_dataset`

`inference_on_dataset(model, data_loader, evaluator, flip_test=False)`:

- temporarily switches the model to eval mode and restores its previous training
  mode after evaluation;
- wraps inference in `torch.no_grad()`;
- calls `evaluator.reset()` before iteration;
- optionally averages normal and horizontally flipped features when
  `flip_test=True`;
- synchronizes CUDA timing when CUDA is available;
- logs total inference time and pure compute time;
- returns `{}` instead of `None` on non-main processes.

Flip test doubles model forward work, so it can affect runtime and memory.

## AQE, rerank, ROC, and metric options

Useful evaluation `opts`:

```text
TEST.METRIC cosine
TEST.FLIP.ENABLED True
TEST.AQE.ENABLED True
TEST.AQE.QE_TIME 1
TEST.AQE.QE_K 5
TEST.AQE.ALPHA 3.0
TEST.RERANK.ENABLED True
TEST.RERANK.K1 20
TEST.RERANK.K2 6
TEST.RERANK.LAMBDA 0.3
TEST.ROC.ENABLED True
```

Guidance:

- Use AQE/rerank only when the user wants the corresponding benchmark protocol;
  they alter metric values and runtime.
- Rerank can require more memory because it builds extra pairwise distances.
- For cosine rerank, features are normalized before Jaccard distance is built.
- ROC metrics require labels/scores to be valid for the dataset protocol.

## Output interpretation

Evaluation prints CSV-style metrics through FastReID's logger. Training writes
metric scalars through event writers; eval-only primarily returns and logs
metrics rather than writing a separate metrics artifact by default.

Expected output locations and signals:

- `OUTPUT_DIR/config.yaml`: merged config written by default setup.
- terminal or log output: command arguments, environment info, full config,
  inference progress, CSV metric table.
- `OUTPUT_DIR/metrics.json`: training scalar history when a training loop is run.
- `OUTPUT_DIR/model_best.pth` and `model_final.pth`: training checkpoint outputs.

When comparing results, keep the exact config, checkpoint, dataset split,
`TEST.FLIP`, AQE, rerank, and metric settings attached to the report.

## Cython rank acceleration and Python fallback

FastReID attempts to use optional Cython rank evaluation for speed. If the
extension is unavailable, it warns and falls back to Python evaluation. The
fallback is acceptable for correctness but can be slow on large benchmarks. Do
not treat the warning as a metrics failure unless runtime is unacceptable for
the task.
