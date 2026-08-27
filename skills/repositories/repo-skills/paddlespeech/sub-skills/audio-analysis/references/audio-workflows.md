# Audio Workflows

## ESC-50 Audio Classification

The ESC-50 recipe uses PANN backbones and fine-tunes classification models. It includes training, prediction, export, and Paddle Inference deployment stages. Treat it as long-running and dataset-dependent.

Use it for planning:

- CNN14: largest/strongest PANN variant.
- CNN10/CNN6: smaller alternatives.
- Deployment exports dynamic checkpoints to static Paddle Inference files.

Do not run training/export stages without approval.

## VoxCeleb Speaker Verification

The speaker verification workflow centers on ECAPA-TDNN and VoxCeleb-style 16 kHz WAV data. VoxCeleb2 source audio may require conversion from `.m4a` to `.wav` with ffmpeg and a `voxceleb2/wav/id*/*.wav` layout.

Use `paddlespeech vector --task spk` for embedding extraction and `--task score` for pair scoring when using pretrained resources.

## HeySnips Keyword Spotting

The KWS example reports false alarm / false reject behavior for MDTC. CLI inference exposes a threshold; raising the threshold usually reduces false alarms and increases false rejects.

## Audio Augmentation Utilities

PaddleSpeech vector tests exercise augmentation primitives such as `AddNoise`, `SpeedPerturb`, `AddBabble`, `DropFreq`, and `DropChunk` with tiny generated tensors. These are good native verification candidates for CPU utility behavior, but they do not validate pretrained vector model quality.

## Audio Search Apps

The audio search demos combine PaddleSpeech embeddings with external services such as Milvus and MySQL. The app workflow includes vector extraction, index/storage setup, and retrieval. It is reference-only for this repo skill unless the user explicitly asks for service orchestration.
