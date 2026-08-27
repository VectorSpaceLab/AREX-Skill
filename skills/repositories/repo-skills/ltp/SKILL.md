---
name: ltp
description: "Guides LTP Chinese NLP package workflows for Python pipelines,
  legacy perceptron models, optional training data/configs, and Rust/C
  bindings."
disable-model-invocation: true
metadata:
  disco-role: operating
license: CC BY-NC 4.0
---

# LTP Repo Skill

Use this skill when a task involves **LTP / Language Technology Platform** for Chinese NLP: sentence splitting, Chinese word segmentation (CWS), POS tagging, NER, SRL, dependency parsing, semantic dependency parsing, legacy perceptron models, optional `ltp_core` training/config work, or Rust/C bindings.

This is a self-contained operating guide. Do not depend on the source checkout that produced the skill; use the bundled references and scripts here.

## Fast route map

| User task | Read next |
| --- | --- |
| Install/import LTP, check package split, diagnose `ltp`, `ltp_core`, or `ltp_extension` imports | [references/packaging-and-install.md](references/packaging-and-install.md), then run [scripts/check_ltp_install.py](scripts/check_ltp_install.py) |
| Load `LTP(...)`, run `pipeline`, choose tasks, interpret `LTPOutput`, use sentence splitting, add custom words, or handle local/HF model paths | [sub-skills/python-pipeline/SKILL.md](sub-skills/python-pipeline/SKILL.md) |
| Use fast legacy CWS/POS/NER, `LTP("LTP/legacy")`, `ltp_extension.perceptron`, custom CWS type rules, or legacy trainer APIs | [sub-skills/legacy-extension/SKILL.md](sub-skills/legacy-extension/SKILL.md) |
| Prepare data/configs for optional deep-learning training/evaluation with `ltp_core`, Hydra overrides, checkpoints, or task data formats | [sub-skills/training-and-data/SKILL.md](sub-skills/training-and-data/SKILL.md) |
| Use the Rust `ltp` crate or `ltp-cffi` C bindings for legacy CWS/POS/NER | [sub-skills/rust-bindings/SKILL.md](sub-skills/rust-bindings/SKILL.md) |
| Compare model/task coverage, label sets, output shapes, and backend expectations | [references/model-catalog-and-tasks.md](references/model-catalog-and-tasks.md) |
| Debug model downloads, package version mismatches, CUDA, missing model files, training dependencies, or Rust toolchain issues | [references/troubleshooting.md](references/troubleshooting.md) plus the nearest sub-skill troubleshooting reference |
| Check whether this skill matches a checkout/version before refreshing it | [references/repo-provenance.md](references/repo-provenance.md) |

## Package shape to remember

LTP 4 is split across three Python distributions:

```bash
pip install torch transformers
pip install ltp ltp-core ltp-extension
python - <<'PY'
from ltp import LTP, StnSplit
print(LTP, StnSplit().split('汤姆生病了。他去了医院。'))
PY
```

- `ltp` is the high-level Python interface with the `LTP(...)` factory and `LTPOutput`.
- `ltp-core` contains the neural model, task heads, data modules, training/eval code, and algorithms.
- `ltp-extension` is the Rust-backed Python extension for sentence splitting, legacy perceptron CWS/POS/NER, hooks, and utility algorithms.
- Rust users use the separate `ltp` crate; C users use the `ltp-cffi` crate/library surface.

## Safe first checks

Run the bundled environment probe before attempting model downloads or training:

```bash
python scripts/check_ltp_install.py --json
python scripts/check_ltp_install.py --check-cuda
```

The probe imports the package, checks distribution versions, runs a sentence split and utility-function smoke, and optionally checks CUDA availability. It does **not** download Hugging Face models, run training, or build Rust crates.

## Common decision points

- Choose `LTP("LTP/tiny")`, `LTP("LTP/small")`, `LTP("LTP/base")`, `LTP("LTP/base1")`, or `LTP("LTP/base2")` for neural tasks (`cws`, `pos`, `ner`, `srl`, `dep`, `sdp`, `sdpg`). Use `LTP("LTP/legacy")` for fast legacy `cws`, `pos`, `ner` only.
- Pass a local model directory when offline. The directory must contain `config.json`; neural models also need tokenizer/model weights, and legacy models need the files named by their config.
- If you omit `cws` from `pipeline(tasks=...)`, provide pre-tokenized words, not raw text.
- For legacy NER, include POS or pass POS results explicitly; NER depends on words and POS tags.
- Treat CUDA as optional acceleration unless the user explicitly asks for GPU validation. CPU is sufficient for import/API checks and many small diagnostics.
- Treat training and Rust/C builds as advanced workflows with extra dependencies/toolchains; use the bundled command builders and validators before running expensive commands.

## Scope boundaries

This skill helps future agents use and troubleshoot LTP. It is not a model cache, benchmark dataset, or replacement for large pretrained weights. It intentionally avoids automatic network downloads, long training runs, and Rust/C builds unless a user explicitly asks for those actions in a suitable environment.
