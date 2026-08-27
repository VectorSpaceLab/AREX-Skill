---
name: xlnet
description: "Operate the legacy TensorFlow 1.x XLNet repository for model APIs,
  classification, SQuAD, RACE, and pretraining workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# XLNet repo skill

Use this skill when a Researcher task involves the original `zihangdai/xlnet` TensorFlow 1.x repository: released XLNet checkpoints, `xlnet_config.json`, `spiece.model`, source-script fine-tuning, SQuAD/RACE workflows, pretraining data, or direct XLNet graph APIs.

## Before you act

1. Confirm the caller wants the original TensorFlow 1.x XLNet code, not modern Hugging Face `transformers.XLNet*` APIs.
2. Collect the model bundle paths: `xlnet_config.json`, `spiece.model`, and, for training, the TensorFlow checkpoint prefix.
3. Identify the workflow family and route to the focused sub-skill below.
4. Run `scripts/check_xlnet_environment.py --help` when you need a safe import/config diagnostic. It does not download data, open checkpoints, or launch training.
5. Read [references/model-overview.md](references/model-overview.md) for released model artifacts, memory anchors, and hardware expectations.
6. Read [references/troubleshooting.md](references/troubleshooting.md) for cross-cutting TensorFlow 1.x, protobuf, Abseil flag, checkpoint, and backend failures.
7. Read [references/repo-provenance.md](references/repo-provenance.md) before deciding whether this skill is stale for a checkout.

## Runtime prerequisites

- Legacy TensorFlow 1.x runtime. TensorFlow 2.x lacks several `tf.contrib` APIs used by the repository.
- `sentencepiece`, `numpy`, and task-specific metric packages such as `scipy`/`scikit-learn` for RACE metrics.
- An XLNet source checkout or runtime where source modules such as `xlnet`, `modeling`, `run_classifier`, `run_squad`, and `run_race` are importable.
- Released or fine-tuned model artifacts supplied by the user; this skill does not bundle checkpoints, tokenizer models, or datasets.
- GPU/TPU hardware only when the selected workflow requires actual training or large evaluation. Many checks and command builders are CPU-safe.

Minimal diagnostic from a runtime where XLNet source is importable:

```bash
python scripts/check_xlnet_environment.py --repo-root /path/to/xlnet --config /path/to/xlnet_config.json
```

If no checkout path is needed because the modules are already importable, omit `--repo-root`.

## Route map

| User task | Read next | Why |
| --- | --- | --- |
| Use `XLNetConfig`, `RunConfig`, `XLNetModel`, tokenizer helpers, losses, checkpoint loading, or custom TensorFlow graph code. | [sub-skills/model-api/SKILL.md](sub-skills/model-api/SKILL.md) | Covers verified signatures, tensor shapes, config validation, and runtime helpers. |
| Fine-tune/evaluate/predict GLUE MNLI, STS-B, IMDB, Yelp-5, or processor-backed classification/regression through `run_classifier.py`. | [sub-skills/classification/SKILL.md](sub-skills/classification/SKILL.md) | Covers task names, data layouts, train/eval/predict flags, and command generation. |
| Preprocess or fine-tune SQuAD 1.1/2.0, generate predictions, decode n-best answers, or handle no-answer thresholds. | [sub-skills/squad-qa/SKILL.md](sub-skills/squad-qa/SKILL.md) | Covers SQuAD JSON, feature caches, GPU/TPU recipes, prediction outputs, and threshold metrics. |
| Run RACE multiple-choice reading-comprehension training/evaluation or adapt TPU RACE recipes. | [sub-skills/race-reading-comprehension/SKILL.md](sub-skills/race-reading-comprehension/SKILL.md) | Covers RACE directory layout, high/middle filtering, four-candidate batching, and TPU command templates. |
| Prepare raw text or token-id corpora for pretraining, generate TFRecords, or build `train_gpu.py`/`train.py` pretraining commands. | [sub-skills/data-pretraining/SKILL.md](sub-skills/data-pretraining/SKILL.md) | Covers corpus format, SentencePiece assumptions, record_info files, and pretraining command builders. |

## Operating guardrails

- Do not import several task scripts in the same long-lived Python process; their Abseil flags collide. Inspect one CLI module per process.
- Keep `data_dir`, `output_dir`, `model_dir`, `predict_dir`, and `init_checkpoint` conceptually separate.
- Treat `output_dir` as a cache. Use a new cache or overwrite flag when sequence length, task data, tokenizer, or split changes.
- For multi-GPU task fine-tuning, `num_core_per_host` means number of GPUs and `train_batch_size` is per GPU.
- Prefer command-builder scripts in the sub-skills when assembling long commands. They print commands only and avoid accidental training, downloads, or GCS writes.
- Do not treat README result numbers as proof for a new run. They are context anchors; real results require matching data, checkpoints, hardware, and training time.

## Bundled root files

- [references/model-overview.md](references/model-overview.md): released models, artifact contracts, memory table, and result anchors.
- [references/troubleshooting.md](references/troubleshooting.md): shared runtime, artifact, and backend troubleshooting.
- [references/repo-provenance.md](references/repo-provenance.md): source snapshot and refresh baseline.
- [references/repo-routing-metadata.json](references/repo-routing-metadata.json): structured metadata for a future managed repo-skill import.
- [scripts/check_xlnet_environment.py](scripts/check_xlnet_environment.py): safe runtime/config diagnostic helper.
