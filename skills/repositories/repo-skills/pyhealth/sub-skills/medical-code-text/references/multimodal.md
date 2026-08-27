# Multimodal processing

`ModalityType` names `code`, `text`, `image`, `numeric`, `audio`, and `signal`.
PyHealth processors include image, audio, signal/EEG, time-image, graph,
text, tuple-time-text, and temporal-timeseries families. A temporal processor
should expose named outputs such as `value`, `time`, and optionally `mask`; the
shape and modality determine the model encoder.

For a multimodal model, specify:

- per-modality raw schema and processor;
- value dtype/shape and time units;
- token versus continuous semantics;
- alignment/windowing and missing-modality handling;
- encoder and fused representation dimensions;
- task label/output mode;
- CPU/GPU memory budget and external data/weight requirements.

`UnifiedMultimodalEmbeddingModel`, `MedFuse`, vision/text embedding classes,
and EEG/CXR examples are useful routes but often require trained or downloaded
assets. Use processor unit tests and tiny local tensors/images/signals for
verification. Do not claim full modality or CUDA coverage from a package import.
