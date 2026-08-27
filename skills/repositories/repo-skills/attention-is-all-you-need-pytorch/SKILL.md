---
name: attention-is-all-you-need-pytorch
description: "Use jadore801120 attention-is-all-you-need-pytorch for Transformer
  architecture inspection, preprocessing, training, and checkpoint translation
  workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# attention-is-all-you-need-pytorch

Use this repo skill when a task involves the PyTorch implementation of the
Transformer paper in `jadore801120/attention-is-all-you-need-pytorch`: model
internals, German-English preprocessing, training commands, or checkpoint
translation. The repository is script/source based rather than a packaged Python
distribution, so future users normally work from a checkout that contains
`transformer/`, `preprocess.py`, `train.py`, and `translate.py`.

## Quick Setup And Smoke Check

Use a legacy-compatible Python environment with PyTorch, legacy torchtext APIs,
spaCy, dill, tqdm, and NumPy. The source expects `torchtext.data.Field`; modern
torchtext releases that removed this API will not work unchanged.

Minimal import check from a user's checkout:

```bash
python - <<'PY'
from transformer.Models import Transformer
from transformer.Translator import Translator
print(Transformer)
print(Translator)
PY
```

Run the bundled environment checker when diagnosing an existing checkout:

```bash
python scripts/check_environment.py --repo-root /path/to/attention-is-all-you-need-pytorch --device cpu
```

## Route Map

- [model-architecture](sub-skills/model-architecture/SKILL.md): instantiate or
  debug `Transformer`, masks, positional encoding, attention layers,
  feed-forward blocks, weight sharing, tensor shapes, and `ScheduledOptim`.
- [data-preparation](sub-skills/data-preparation/SKILL.md): prepare or inspect
  Multi30k/spaCy and WMT+BPE data artifacts, pickle schemas, torchtext Fields,
  vocabularies, and BPE helper behavior.
- [training](sub-skills/training/SKILL.md): build and troubleshoot `train.py`
  commands, hyperparameters, scheduler/loss behavior, logs, checkpoints,
  TensorBoard, CPU/CUDA selection, and safe training preflights.
- [translation](sub-skills/translation/SKILL.md): validate checkpoints and data
  pickles for `translate.py`, run checkpoint translation, or use
  `transformer.Translator` beam search programmatically.

## Repo-Level References

- Read [references/package-overview.md](references/package-overview.md) for the
  source layout, dependency expectations, workflow map, and known caveats.
- Read [references/troubleshooting.md](references/troubleshooting.md) for
  cross-cutting install/import, torchtext, spaCy, CUDA, pickle, and stale README
  issues.
- Read [references/repo-provenance.md](references/repo-provenance.md) before
  deciding whether this skill is current for a checkout or should be refreshed.

## Decision Hints

- If the user asks about tensor dimensions, masks, weight sharing, or custom
  model construction, route to model-architecture before training or translation.
- If the user asks why training cannot read a pickle, route to data-preparation
  first, then training after the schema is identified.
- If the user asks about a `.chkpt` file, route to translation for checkpoint
  inspection unless they are asking how the checkpoint was produced.
- If the prompt mentions BPE, keep the repository caveat visible: BPE is marked
  not fully tested and `translate.py` leaves BPE decoding as TODO.
- If a README command fails with an unrecognized `-log` flag, prefer the
  inspected `train.py` parser over the README example for this commit.
