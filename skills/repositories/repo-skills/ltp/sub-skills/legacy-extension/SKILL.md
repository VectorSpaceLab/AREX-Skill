---
name: legacy-extension
description: "Guides LTP legacy perceptron and ltp_extension workflows for fast
  CWS/POS/NER, custom segmentation rules, and trainer APIs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: CC BY-NC 4.0
---

# Legacy Extension

Use this sub-skill for the Rust-backed Python extension surface: fast legacy CWS/POS/NER, sentence splitting utilities, custom word hooks, CWS character-type rules, direct model files, and perceptron trainer APIs.

## Choose this route when

- The user asks for `LTP("LTP/legacy")`, `ltp_extension`, `CWSModel`, `POSModel`, `NERModel`, `CharacterType`, `Algorithm`, `Trainer`, `CWSTrainer`, `POSTrainer`, or `NERTrainer`.
- Speed is more important than the full neural task set and only CWS/POS/NER are needed.
- The task involves direct legacy model binary files, custom CWS rules for digits/roman/kanji, or legacy perceptron training data.
- The user needs to understand benchmark/performance claims without running large benchmark scripts.

For neural SRL/DEP/SDP/SDPG, use [../python-pipeline/SKILL.md](../python-pipeline/SKILL.md). For Rust-native crate use, use [../rust-bindings/SKILL.md](../rust-bindings/SKILL.md).

## Main workflow

1. Verify imports without model downloads:

   ```bash
   python ../../scripts/check_ltp_install.py --json
   python scripts/legacy_rules_smoke.py --no-model
   ```

2. For high-level legacy inference, use the factory when a complete legacy model directory or cache is available:

   ```python
   from ltp import LTP
   ltp = LTP("LTP/legacy")
   output = ltp.pipeline(["他叫汤姆去拿外衣。"], tasks=["cws", "pos", "ner"])
   ```

3. For direct model files, use specialized extension classes:

   ```python
   from ltp_extension.perceptron import CWSModel, POSModel, NERModel
   cws = CWSModel.load("cws_model.bin")
   pos = POSModel.load("pos_model.bin")
   ner = NERModel.load("ner_model.bin")
   words = cws.predict("他叫汤姆去拿外衣。")
   tags = pos.predict(words)
   entities = ner.predict(words, tags)
   ```

4. Validate trainer inputs before training:

   ```bash
   python scripts/legacy_trainer_config_check.py --task cws --train-file train.txt --eval-file dev.txt --algorithm AP
   ```

## Read these references

- [references/perceptron-api.md](references/perceptron-api.md) for inspected classes, methods, and trainer properties.
- [references/workflows.md](references/workflows.md) for high-level legacy, direct model, custom-rule, and trainer recipes.
- [references/performance-and-benchmarks.md](references/performance-and-benchmarks.md) for what the benchmark numbers mean and why bundled helpers do not run large benchmarks.
- [references/troubleshooting.md](references/troubleshooting.md) for missing model files, task dependencies, labels/data, model-type mismatches, and parallelism issues.

## Bundled helpers

- [scripts/legacy_rules_smoke.py](scripts/legacy_rules_smoke.py) checks extension imports, `CharacterType`, and optional local CWS model rule setup without downloads.
- [scripts/legacy_trainer_config_check.py](scripts/legacy_trainer_config_check.py) validates legacy trainer task, labels, train/eval file presence, and algorithm choice without training.

## Boundaries

- Legacy only covers CWS/POS/NER. Do not route SRL/DEP/SDP/SDPG here.
- Direct model classes require local model binary files. The skill does not ship pretrained model weights.
- Trainer APIs can run training, but the bundled script only validates configuration; running training is a user-approved expensive action.
