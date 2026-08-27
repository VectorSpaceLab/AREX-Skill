---
name: preprocessing-and-utilities
description: "Routes numpy-ml preprocessing, tokenization, signal-processing,
  kernel, distance, graph, and data-structure utility tasks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# Preprocessing and Utilities

Use this sub-skill when a task is about preparing arrays or using `numpy-ml`
helper objects before a model workflow:

- standardization, one-hot encoding, and feature hashing;
- tokenization, vocabularies, TF-IDF, BPE, and Huffman coding;
- DFT, DCT, MFCC, framing, interpolation, and signal windows;
- kernels, distance metrics, priority queues, ball trees, samplers, graph
  helpers, and testing utilities.

## First Checks

1. Run the smoke helper for the exact method names and output shapes:

   ```bash
   python sub-skills/preprocessing-and-utilities/scripts/preprocessing_utils_smoke.py
   ```

2. Read [`references/api-reference.md`](references/api-reference.md) before
   using an encoder or utility whose method names differ from scikit-learn.
3. Read [`references/workflows.md`](references/workflows.md) for tiny tabular,
   text, signal, kernel, and graph utility recipes.
4. Read [`references/troubleshooting.md`](references/troubleshooting.md) for
   unknown labels, hasher sparse/dense issues, MFCC/audio assumptions, and
   optional comparison dependency questions.

## Route by Task

| User asks for | Use this route |
| --- | --- |
| standardize arrays or encode labels | general preprocessing API/workflow. |
| hash feature dictionaries | `FeatureHasher.encode` guidance. |
| tokenize or build text vocab/TF-IDF | NLP preprocessing workflow. |
| compute DFT/DCT/MFCC/window functions | DSP and window workflow. |
| kernels, distances, BallTree, priority queue, graph helpers | utility API/workflow. |
| fit a supervised, probabilistic, neural, or RL model | route to the model sub-skill after preprocessing. |

## Operating Notes

- `OneHotEncoder` uses `transform` / `inverse_transform`; do not assume
  `fit_transform` exists.
- `FeatureHasher` uses `encode` on dictionaries or lists of dictionaries.
- Utilities are intended for small explicit NumPy examples. Keep validation
  scripts deterministic and avoid downloads or large data.
