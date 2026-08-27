# Audio Analysis CLI and API

## Audio Classification

```bash
paddlespeech cls --input audio.wav --topk 10
paddlespeech cls --model panns_cnn14 --input audio.wav
```

Options:

- `--model`: `panns_cnn6`, `panns_cnn10`, or `panns_cnn14`.
- `--topk`: number of labels to return.
- `--config`, `--ckpt_path`, `--label_file`: custom model resources.
- Default model tags use 32 kHz resources; input is loaded/resampled by audio backend where supported.

Python executor:

```python
import paddle
from paddlespeech.cli.cls import CLSExecutor

cls = CLSExecutor()
labels = cls(audio_file="audio.wav", model="panns_cnn14", topk=5, device=paddle.get_device())
```

## Speaker Vector and Scoring

```bash
paddlespeech vector --task spk --input speaker_16k.wav
paddlespeech vector --task score --input pairs.job
```

Vector options:

- `--model`: `ecapatdnn_voxceleb12`.
- `--task`: `spk` for embedding extraction, `score` for cosine score between two embeddings.
- `--sample_rate`: only `16000` in the CLI parser.
- `--yes`: accept resampling/format conversion.

Vector score job format uses the vector-specific parser:

```text
pair1 enroll.wav test.wav
pair2 another_enroll.wav another_test.wav
```

## Keyword Spotting

```bash
paddlespeech kws --input input_16k.wav --threshold 0.8
paddlespeech kws --model mdtc_heysnips --input input_16k.wav
```

KWS output is a score, threshold, and boolean keyword decision. The released model family in this checkout is MDTC trained for HeySnips-style keyword spotting.

## SSL Vector Extraction

`paddlespeech ssl --task vector` belongs to the SSL command family; use `../speech-to-text/SKILL.md` for model/tag details.
