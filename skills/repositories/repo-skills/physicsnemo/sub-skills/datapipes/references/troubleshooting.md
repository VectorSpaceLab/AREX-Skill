# Datapipe troubleshooting

## Missing fields or wrong file patterns

- Symptom: the reader returns empty samples, missing keys, or a zero-length dataset.
- Likely cause: the file pattern or field list does not match the on-disk layout.
- Fix: inspect one sample directly, then tighten the reader configuration.

## Collation or shape mismatch

- Symptom: batching fails when the loader encounters variable shapes or missing dimensions.
- Likely cause: the collator expects fixed-size tensors but the dataset is ragged or graph-like.
- Fix: choose a concat/custom collator or normalize the sample shape before batching.

## Device / stream confusion

- Symptom: the data appears on the wrong device or prefetch behavior is hard to reason about.
- Likely cause: dataset device transfer and transform execution order were not verified first.
- Fix: debug the raw reader output synchronously before turning prefetch/streams back on.

## Optional dependency failure

- Symptom: VTK or TensorStore readers fail at import/runtime.
- Likely cause: optional format-specific dependencies are not installed.
- Fix: install only the needed extra for the selected route.

## Iterable dataset confusion

- Symptom: `len(loader)` fails or `shuffle` is ignored.
- Likely cause: the source is an `IterableDatasetBase` and uses the main-thread generator path.
- Fix: treat iterable loaders differently from map-style datasets and seed by iteration position.

## Large domain example overrun

- Symptom: a domain example appears to be a smoke test but needs a lot of data or time.
- Likely cause: the example is a full recipe rather than a tiny validation check.
- Fix: use the bundled tiny fixture helper for validation and keep the full recipe reference-only.
