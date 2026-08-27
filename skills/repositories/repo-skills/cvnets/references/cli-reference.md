# CVNets CLI Reference

## Purpose

Read this when you need the canonical command families, top-level flags, and reliable wrapper entry points for CVNets. The installed console scripts are convenient when they work, but the bundled wrappers in this skill tree are the safer entry points for future agents.

## Canonical command families

| Command family | Public entry point | Typical purpose | Common flags |
| --- | --- | --- | --- |
| Training | `main_train.main_worker` | Launch a training or finetuning run. | `--common.config-file`, `--common.results-loc`, `--common.resume`, `--common.finetune`, `--common.auto-resume`, `--ddp.rank`, `--ddp.world-size`, `--ddp.dist-url`, `--ddp.backend`, `--common.mixed-precision`, `--common.channels-last` |
| Generic eval | `main_eval.main_worker` | Evaluate a classification or generic model. | `--common.config-file`, `--common.results-loc`, `--model.<category>.pretrained`, `--common.override-kwargs` |
| Detection eval | `main_eval.main_worker_detection` | Run detection evaluation or image-level detection inference. | `--common.config-file`, `--common.results-loc`, `--model.detection.pretrained`, `--model.detection.n-classes`, `--evaluation.detection.mode`, `--evaluation.detection.path`, `--model.detection.ssd.conf-threshold` |
| Segmentation eval | `main_eval.main_worker_segmentation` | Run segmentation evaluation or image-level segmentation inference. | `--common.config-file`, `--common.results-loc`, `--model.segmentation.pretrained`, `--model.segmentation.n-classes`, `--evaluation.segmentation.mode`, `--evaluation.segmentation.path`, `--evaluation.segmentation.save-masks`, `--evaluation.segmentation.apply-color-map` |
| CoreML conversion | `main_conversion.main_worker_conversion` | Convert a trained PyTorch model to CoreML and JIT artifacts. | `--common.config-file`, `--common.results-loc`, `--model.<category>.pretrained`, `--conversion.coreml-extn`, `--conversion.input-image-path`, `--model.<category>.n-classes` for detection/segmentation |
| Benchmark | `main_benchmark.main_benchmark` | Measure throughput on a selected model. | `--common.config-file`, `--benchmark.batch-size`, `--benchmark.warmup-iter`, `--benchmark.n-iter`, `--benchmark.use-jit-model`, `--common.mixed-precision` |
| Loss landscape | `main_loss_landscape.main_worker_loss_landscape` | Evaluate a loss landscape on a trained model. | `--common.config-file`, `--common.results-loc`, `--loss-landscape.n-points`, `--loss-landscape.min-x`, `--loss-landscape.max-x`, `--loss-landscape.min-y`, `--loss-landscape.max-y` |

## Reliable wrapper commands

Use the bundled wrappers in the skill tree when you want a self-contained invocation that does not depend on the installed console script resolving `main_*` modules from the environment.

- `sub-skills/training-and-evaluation/scripts/cvnets_train.py`
- `sub-skills/training-and-evaluation/scripts/cvnets_eval.py`
- `sub-skills/training-and-evaluation/scripts/cvnets_eval_det.py`
- `sub-skills/training-and-evaluation/scripts/cvnets_eval_seg.py`
- `sub-skills/conversion-and-profiling/scripts/cvnets_convert.py`
- `sub-skills/conversion-and-profiling/scripts/cvnets_benchmark.py`
- `sub-skills/conversion-and-profiling/scripts/cvnets_loss_landscape.py`

All wrappers accept `--repo-root <repo-root>` and then pass the remaining args through to the underlying public entry point.

## Common flag families

- `common.*` for run metadata, checkpointing, mixed precision, and override behavior.
- `dataset.*` for roots, batch sizes, workers, and collate behavior.
- `model.<category>.*` for architecture selection and pretrained weights.
- `sampler.*` for the sampler family and crop-size controls.
- `ddp.*` for distributed training and evaluation.
- `conversion.*`, `benchmark.*`, and `loss-landscape.*` for the export/profiling workflows.

## When to read this instead of a sub-skill

- You already know the workflow and only need the exact top-level flag family.
- You need to check whether a command is a train, eval, convert, benchmark, or loss-landscape invocation before opening the deeper workflow docs.
