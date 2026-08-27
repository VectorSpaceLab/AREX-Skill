# Metrics

## Metric wrappers

- `ImageSim`
  - Perceptual similarity based on the model's vision backbone.
  - Used directly by MCTS and by model-based evaluation.
- `ClipScore`
  - Text-to-image similarity wrapper.
- `CrystalBLEU`
  - TeX-aware corpus BLEU variant that filters trivially shared n-grams.
- `DreamSim`
  - Perceptual similarity metric backed by DreamSim.
- `KernelInceptionDistance`
  - KID wrapper configured with a CLIP-style feature extractor.
- `TexEditDistance`
  - TeX-aware extended edit distance wrapper.

## Dependency notes

- `CrystalBLEU` needs `crystalbleu`, `sacremoses`, and the TeX tokenization stack.
- `DreamSim` needs `dreamsim` and may download assets the first time it is used.
- `ClipScore` and `ImageSim` rely on transformer vision models and image processors.
- `KernelInceptionDistance` depends on `torchmetrics` and image feature extraction support.

## Scoring behavior

- Most metrics accumulate state and compute a final scalar later.
- `ImageSim` can compare image-image or image-text pairs depending on the call path.
- `TexEditDistance` tokenizes TeX content before computing the score.
- `CrystalBLEU` caches shared n-grams so repeated runs can be cheaper.
