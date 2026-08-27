# Package Overview

## Source Layout

This repository is a script-oriented PyTorch implementation of the Transformer
model from "Attention Is All You Need". It does not expose packaging metadata in
this checkout; use a repository checkout or put the checkout on `PYTHONPATH` for
scripts and helpers.

| Source artifact | User-facing role | Skill owner |
| --- | --- | --- |
| `transformer/Models.py` | `Transformer`, `Encoder`, `Decoder`, masks, positional encoding. | `model-architecture` |
| `transformer/Modules.py` | `ScaledDotProductAttention`. | `model-architecture` |
| `transformer/SubLayers.py` | `MultiHeadAttention`, `PositionwiseFeedForward`. | `model-architecture` |
| `transformer/Layers.py` | Encoder and decoder layer composition. | `model-architecture` |
| `transformer/Optim.py` | Noam-style scheduled optimizer wrapper. | `model-architecture`, `training` |
| `preprocess.py` | Multi30k/spaCy and WIP WMT+BPE preprocessing. | `data-preparation` |
| `apply_bpe.py`, `learn_bpe.py` | BPE code learning and encoding borrowed from subword-nmt. | `data-preparation` |
| `train.py` | Training CLI, dataloaders, loss, logs, checkpoints. | `training` |
| `train_multi30k_de_en.sh` | Long-running shell command template. | `training` |
| `translate.py` | Checkpoint translation CLI. | `translation` |
| `transformer/Translator.py` | Beam-search translation class. | `translation` |

## Dependency Expectations

The historical `requirements.txt` pins very old versions, including Python 3.6,
PyTorch 1.3.1, spaCy 2.3.5, TensorBoard/TensorFlow, and torchtext-era APIs. For
modern inspection, the key compatibility requirement is legacy torchtext API
support for `torchtext.data.Field`, `Dataset`, and `BucketIterator`.

Practical environment surfaces:

- PyTorch for all model/training/translation operations.
- torchtext legacy APIs for preprocessing, dataloaders, and translation test
  dataset wrapping.
- spaCy language models for the default preprocessing tokenizer path.
- dill for loading/saving preprocessing pickles.
- tqdm and NumPy for progress and numeric utilities.
- TensorBoard only when training uses `-use_tb`.

## Workflow Map

1. Data preparation creates a trusted pickle and optional BPE encoded files.
2. Training reads those artifacts, trains a Transformer, writes logs, and writes
   checkpoint dictionaries with `epoch`, `settings`, and `model` keys.
3. Translation reads the checkpoint and default non-BPE data pickle, rebuilds a
   `Transformer`, wraps it in `Translator`, and writes one decoded output line
   per test example.
4. Architecture APIs can also be used directly for experiments and smoke tests
   without full preprocessing or training.

## Known Caveats

- The README says BPE parts are not fully tested.
- `translate.py` marks BPE source input and BPE post-decoding as TODO.
- The README training command contains `-log`, but the inspected parser does not
  define that flag at this commit.
- `train.py -save_mode all` writes checkpoint files in the current working
  directory rather than joining `output_dir`.
- Pickle-based workflows should load only trusted files.
