# API Reference

## Purpose

This file records the verified anchor constructors and the main parameters a user is likely to tune.

## Constructors

- `AnchorTabular(predictor, feature_names, categorical_names=None, dtype=np.float32, ohe=False, seed=None)`
- `AnchorText(predictor, sampling_strategy='unknown', nlp=None, language_model=None, seed=0, **kwargs)`
- `AnchorImage(predictor, image_shape, dtype=np.float32, segmentation_fn='slic', segmentation_kwargs=None, images_background=None, seed=None)`

## Main call patterns

- `AnchorTabular.fit(train_data, disc_perc=(25, 50, 75), **kwargs)`
- `AnchorTabular.explain(X, threshold=0.95, delta=0.1, tau=0.15, batch_size=100, coverage_samples=10000, beam_size=1, stop_on_first=False, max_anchor_size=None, min_samples_start=100, n_covered_ex=10, binary_cache_size=10000, cache_margin=1000, verbose=False, verbose_every=1, **kwargs)`
- `AnchorText.explain(text, threshold=0.95, delta=0.1, tau=0.15, batch_size=100, coverage_samples=10000, beam_size=1, stop_on_first=True, max_anchor_size=None, min_samples_start=100, n_covered_ex=10, binary_cache_size=10000, cache_margin=1000, verbose=False, verbose_every=1, **kwargs)`
- `AnchorImage.explain(image, p_sample=0.5, threshold=0.95, delta=0.1, tau=0.15, batch_size=100, coverage_samples=10000, beam_size=1, stop_on_first=False, max_anchor_size=None, min_samples_start=100, n_covered_ex=10, binary_cache_size=10000, cache_margin=1000, verbose=False, verbose_every=1, **kwargs)`

## Output notes

- All three anchor explainers return anchor terms plus precision and coverage.
- `AnchorImage` also returns masked-image and segment metadata.
- `AnchorText` depends on the sampling strategy you choose at construction time.

## Gotchas

- `AnchorTabular` needs fitting before `explain`.
- `AnchorText` needs raw text batches and the correct sampling strategy.
- `AnchorImage` needs a segmentation function that returns sensible superpixels.
