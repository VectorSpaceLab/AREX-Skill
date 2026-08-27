---
name: imagededup
description: "Route image deduplication tasks for the imagededup package:
  hash-based duplicate detection, CNN-based duplicate detection with custom
  models, and evaluation or plotting of duplicate maps."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# imagededup

Use this skill for the `imagededup` package when the task is about finding exact or near-duplicate images, generating encodings, comparing duplicate maps, or plotting duplicate relationships.

## Start here

- Use [`sub-skills/hashing/SKILL.md`](sub-skills/hashing/SKILL.md) for perceptual, average, difference, or wavelet hashing; duplicate search by Hamming distance; or remove-list generation.
- Use [`sub-skills/cnn/SKILL.md`](sub-skills/cnn/SKILL.md) for CNN-based encodings, pretrained or custom models, cosine-similarity duplicate search, or GPU/CPU behavior.
- Use [`sub-skills/evaluation/SKILL.md`](sub-skills/evaluation/SKILL.md) for evaluating retrieved duplicate maps and plotting duplicate groups.

## What this skill covers

- Encoding one image or a directory of images.
- Finding duplicates from a directory or from a precomputed encoding map.
- Removing duplicate filenames with a heuristic list, not deleting files.
- Evaluating retrieved duplicate maps against a symmetric ground-truth map.
- Plotting one image and its duplicates.
- Custom CNN model wrappers and the bundled pretrained CNN backbones.

## What this skill does not cover

- Package release automation.
- Docs building or site generation.
- Benchmark reproduction as a maintainer task.
- External dataset downloads such as the CIFAR10 Colab example.

## Quick install for inspection or verification

Create an isolated Python 3.11 environment, then install the package from PyPI plus the runtime imports that this version uses but does not fully declare in metadata.

```bash
python -m pip install "imagededup==0.3.3.post2" numpy scipy
```

If you plan to run package tests in a separate source checkout, also install `pytest` and `pytest-mock` there.

## Minimal import check

```python
from imagededup.methods import PHash, AHash, DHash, WHash, CNN
from imagededup.evaluation import evaluate
from imagededup.utils import plot_duplicates, CustomModel
```

## Routing guidance

Read the matching sub-skill when the user asks for any of the following:

- exact or near duplicate lookup with `PHash`, `AHash`, `DHash`, or `WHash`
- hash generation from files, directories, or image arrays
- `find_duplicates` / `find_duplicates_to_remove` with Hamming thresholds
- `search_method`, `bktree`, `brute_force`, or `brute_force_cython`
- CNN encodings, cosine similarity, or `CustomModel`
- pretrained MobileNetV3, ViT, or EfficientNet backbones
- `evaluate`, MAP, NDCG, Jaccard, precision, recall, or F1
- `plot_duplicates`

## Common first checks

1. Confirm the image paths or encoding map are valid.
2. Confirm the threshold type matches the workflow.
3. Decide whether the task is hash-based or CNN-based.
4. Use evaluation only after you already have a ground-truth map and a retrieved map.
5. Use plotting only after the duplicate map is non-empty.

## Helpful bundled references

- Read [`references/installation.md`](references/installation.md) for repo-specific install notes, including missing metadata dependencies and CNN weight downloads.
- Read [`references/troubleshooting.md`](references/troubleshooting.md) for cross-cutting import, image-format, backend, and Windows multiprocessing issues.
- Read [`references/repo-provenance.md`](references/repo-provenance.md) when you need the source revision behind this skill.
- Read [`references/repo-routing-metadata.json`](references/repo-routing-metadata.json) when another agent needs to route tasks into this repo skill.

## Script helpers

- Run [`sub-skills/hashing/scripts/hash_smoke.py`](sub-skills/hashing/scripts/hash_smoke.py) to generate a synthetic hash workflow smoke check.
- Run [`sub-skills/cnn/scripts/cnn_smoke.py`](sub-skills/cnn/scripts/cnn_smoke.py) to exercise CNN encoding and duplicate search with a safe synthetic fixture.
- Run [`sub-skills/evaluation/scripts/evaluate_plot_smoke.py`](sub-skills/evaluation/scripts/evaluate_plot_smoke.py) to exercise metrics and duplicate plotting with generated data.

## Fast routing summary

- Hashes and Hamming distance -> hashing sub-skill.
- CNN encodings and custom models -> CNN sub-skill.
- Metrics and plots -> evaluation sub-skill.

When in doubt, prefer the most specific sub-skill that owns the user-visible workflow, then use the shared references only for install or troubleshooting context.