---
name: once-for-all
description: "Routes Once-for-All/OFA pretrained model loading, subnet
  evaluation, and predictor-driven architecture-search workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Once-for-All

Use this skill for the public **Once-for-All (OFA)** package when the request is about pretrained supernets, specialized subnet evaluation, PyTorch Hub entry points, or predictor-driven architecture search.

## What this skill covers

- Load OFA supernets with `ofa.model_zoo.ofa_net`.
- Load specialized OFA models with `ofa.model_zoo.ofa_specialized`.
- Sample, freeze, and extract active subnets from the OFA supernets.
- Evaluate subnet or specialized-model behavior on ImageNet-style folders.
- Run the tutorial-style accuracy, FLOPs, latency, and evolutionary-search helpers.

## What this skill does not cover

- Distributed OFA training with Horovod/MPI.
- ImageNet-scale training runs or long fine-tuning jobs.
- Maintainer release automation.

## Install and smoke-check

Read `references/dependencies.md` before choosing extras. A practical baseline is:

```bash
pip install ofa torch torchvision filelock
pip install numpy gdown tqdm pyyaml matplotlib thop
```

If you are working from a source checkout, prefer a normal install over editable mode when modern packaging tools reject the repo's timestamped version string.

Minimal import smoke:

```bash
python - <<'PY'
from ofa.model_zoo import ofa_net
m = ofa_net('ofa_resnet50', pretrained=False)
print(type(m).__name__)
PY
```

For a broader install check, run `scripts/check_install.py`.

Specialized-model ids may still resolve small public config files even when you are not fetching pretrained weights.

## Route map

### `sub-skills/inference/`
Read this for model loading, subnet sampling, PyTorch Hub names, and ImageNet-style evaluation.

Typical user intents:
- "load an OFA supernet"
- "evaluate a specialized OFA model"
- "sample a subnet"
- "run `eval_ofa_net.py` or `eval_specialized_net.py`"
- "use the hubconf entry points"

### `sub-skills/search/`
Read this for accuracy predictors, FLOPs or latency tables, and evolutionary architecture search.

Typical user intents:
- "search for the best subnet"
- "use the accuracy predictor"
- "run the latency or FLOPs constrained tutorial"
- "build an OFA tradeoff curve"

## Cross-cutting references

- `references/repo-provenance.md` — snapshot of the source checkout used to generate this skill.
- `references/repo-routing-metadata.json` — router metadata consumed by `repo-skills-router`.
- `references/dependencies.md` — package groups and backend notes.
- `references/troubleshooting.md` — install, import, download, and dataset pitfalls.

## Cross-cutting script

- `scripts/check_install.py` — safe install smoke for the installed package and the core OFA helpers.

## How to choose this skill

Choose `once-for-all` when the user names OFA, `ofa_net`, `ofa_specialized`, `AccuracyPredictor`, `EvolutionFinder`, `eval_ofa_net.py`, `eval_specialized_net.py`, or the Once-for-All tutorial notebook.

Choose a more generic computer-vision skill only when the task is not OFA-specific.
