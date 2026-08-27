# Pretrained inference workflows

## Standard Hugging Face model load

```python
from speechbrain.inference.ASR import EncoderDecoderASR

model = EncoderDecoderASR.from_hparams(
    source="speechbrain/asr-conformer-transformerlm-librispeech",
    savedir="pretrained_models/asr-conformer-transformerlm-librispeech",
    run_opts={"device": "cpu"},
)
print(model.transcribe_file("audio.wav"))
```

Change only the class, source, and method for other task families. Keep `savedir` stable across runs so fetched files can be reused.

## Local/offline model folder

Use a local directory containing `hyperparams.yaml` and the files expected by the model's `Pretrainer`.

```python
from speechbrain.inference.classifiers import EncoderClassifier
from speechbrain.utils.fetching import FetchConfig, LocalStrategy

classifier = EncoderClassifier.from_hparams(
    source="/path/to/local/model-folder",
    savedir="pretrained_models/local-classifier",
    local_strategy=LocalStrategy.COPY,
    fetch_config=FetchConfig(allow_network=False),
    run_opts={"device": "cpu"},
)
```

If the local folder is the durable model artifact, `LocalStrategy.NO_LINK` can avoid extra copies, but some code expects files under `savedir`. Use `COPY` when portability matters.

## Download-only preflight

When diagnosing cache, permissions, tokens, or revisions, fetch first without running model code:

```python
from speechbrain.inference.ASR import EncoderASR
from speechbrain.utils.fetching import FetchConfig

EncoderASR.from_hparams(
    source="speechbrain/asr-wav2vec2-commonvoice-fr",
    savedir="pretrained_models/asr-wav2vec2-commonvoice-fr",
    fetch_config=FetchConfig(revision="main", allow_network=True),
    download_only=True,
)
```

Then run a separate construction/inference step. This separates network/cache failures from model-load or forward-pass failures.

## Tensor batch inference

For already-loaded audio, provide a batch tensor and relative lengths:

```python
import torch
from speechbrain.inference.classifiers import EncoderClassifier

classifier = EncoderClassifier.from_hparams(
    source="speechbrain/spkrec-ecapa-voxceleb",
    savedir="pretrained_models/spkrec-ecapa-voxceleb",
    run_opts={"device": "cpu"},
)
wavs = torch.zeros(2, 16000)      # batch, time
wav_lens = torch.ones(2)          # both examples are full length
out_prob, score, index, labels = classifier.classify_batch(wavs, wav_lens)
```

Use `model.load_audio(path)` when you need the model-specific normalizer before batching.

## File output workflows

Enhancement and separation models can produce waveform tensors and may write files:

```python
from speechbrain.inference.enhancement import SpectralMaskEnhancement

enhancer = SpectralMaskEnhancement.from_hparams(
    source="speechbrain/metricgan-plus-voicebank",
    savedir="pretrained_models/metricgan-plus-voicebank",
)
enhanced = enhancer.enhance_file("noisy.wav", output_filename="enhanced.wav")
```

Confirm sample rate and channel assumptions with `speechbrain.dataio.audio_io.info` before and after writing.

## Custom interface workflow

`foreign_class` loads a custom class from a fetched Python file:

```python
from speechbrain.inference.interfaces import foreign_class

model = foreign_class(
    source="trusted-owner/trusted-model",
    pymodule_file="custom.py",
    classname="CustomInterface",
    savedir="pretrained_models/trusted-model",
)
```

Security rule: the fetched Python file is executed. Only use this for sources you would trust as normal code dependencies.

## Device and precision workflow

Use `run_opts` for device, JIT/compile, precision, and runtime controls supported by `RunOptions`:

```python
model = EncoderDecoderASR.from_hparams(
    source="speechbrain/asr-conformer-transformerlm-librispeech",
    savedir="pretrained_models/asr-conformer-transformerlm-librispeech",
    run_opts={"device": "cuda", "eval_precision": "fp16"},
)
```

Validate CUDA separately before constructing large models. For CPU-only fallback, set `device` explicitly to `cpu` so tasks do not silently choose an unintended GPU/driver path.
