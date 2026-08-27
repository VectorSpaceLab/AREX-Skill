# Sequence Tagging Pipeline

## What this surface covers

Use `SequenceTaggingPipeline` for token/character-level tagging such as Chinese NER. The public class lives at:

```python
from fengshen.pipelines.sequence_tagging import SequenceTaggingPipeline
```

The parser can be inspected through the `sequence_tagging` console route, but real prediction/training should normally use the Python API because the generic console wrapper passes arguments in a way that does not match this class perfectly. See [cli-reference.md](cli-reference.md).

## Safe fixture generation

Create a minimal data directory without downloading a dataset:

```bash
python scripts/make_sequence_tagging_fixture.py --out-dir ./fengshen-sequence-tagging-fixture
```

The script writes:

```text
fengshen-sequence-tagging-fixture/
  labels.txt
  train.all.bmes
  dev.all.bmes
  test.all.bmes
```

## Required data layout

`DataProcessor` expects `data_dir` files named `<mode>.all.bmes`, especially `train.all.bmes` and `dev.all.bmes`. Each sentence is separated by a blank line. Each non-empty line contains a token or character followed by its label:

```text
小 B-PER
明 E-PER
在 O
北 B-LOC
京 E-LOC

华 B-ORG
为 E-ORG
发 O
布 O
手 O
机 O
```

`labels.txt` contains one label per line and should not include special labels; the loader prepends `[PAD]`, `[START]`, and `[END]` internally.

```text
O
B-PER
I-PER
E-PER
B-LOC
I-LOC
E-LOC
B-ORG
I-ORG
E-ORG
```

The loader normalizes `M-` tags to `I-` while creating examples. It calls entity extraction with BIOES-style markup, so BMES/BIOES inputs are safer than arbitrary tag schemes.

## Decode type choices

| `--decode_type` | Model key | Label interpretation | When to use |
|---|---|---|---|
| `linear` | `bert-linear` | Token-level labels from `labels.txt` | Default, simplest CPU/parser path. |
| `crf` | `bert-crf` | Token-level labels from `labels.txt` with CRF decoding | Use when the checkpoint was trained with CRF. |
| `span` | `bert-span` | Entity-type labels derived from tag suffixes such as `PER` and `LOC` | Use only with span checkpoints/data expectations. |
| `biaffine` | `bert-biaffine` | Entity-type span labels derived from tag suffixes | Use only with biaffine checkpoints/data expectations. |

`model_type` defaults to `bert`; the class combines it with `decode_type` as `<model_type>-<decode_type>`. Supported built-in combinations are `bert-linear`, `bert-crf`, `bert-span`, and `bert-biaffine`.

## Programmatic prediction skeleton

```python
import argparse
from fengshen.pipelines.sequence_tagging import SequenceTaggingPipeline

parser = argparse.ArgumentParser()
parser.add_argument('--model', default='MODEL_OR_LOCAL_DIR')
parser = SequenceTaggingPipeline.add_pipeline_specific_args(parser)
args = parser.parse_args([
    '--model', 'MODEL_OR_LOCAL_DIR',
    '--data_dir', './fengshen-sequence-tagging-fixture',
    '--model_type', 'bert',
    '--decode_type', 'linear',
    '--max_seq_length', '128',
])

pipe = SequenceTaggingPipeline(model_path=args.model, args=args)
entities = pipe('小明在北京工作')
```

Model/config/tokenizer loading happens at `SequenceTaggingPipeline(...)`; use a local model directory or a cached model id if downloads are not allowed.

## Training route notes

`SequenceTaggingPipeline.train()` loads data internally from `args.data_dir` through `get_datasets(args)`. It does not accept a dataset object argument. This is why the generic console `train` path is not the right route for NER training.

Minimum parser flags for a local run shape are:

```bash
--data_dir ./fengshen-sequence-tagging-fixture \
--model_type bert \
--decode_type linear \
--max_seq_length 128 \
--train_batchsize 8 \
--val_batchsize 8 \
--gpus 0
```

Route detailed Trainer/checkpoint/deepspeed/debugging questions to `data-training`.

## Common mistakes

- Missing `labels.txt`: the pipeline fails before model use because `DataProcessor.get_labels(args)` opens this file during initialization.
- Missing `train.all.bmes` or `dev.all.bmes`: training data construction fails. The default helper writes both.
- Label file contains only entity types (`PER`, `LOC`) but decode type is `linear` or `crf`: token labels such as `B-PER` and `E-PER` are needed for token-label decoders.
- Label file contains only `B-` labels with no ending/inside labels: entity extraction and model labels may not match the intended BMES/BIOES scheme.
- Running original test scripts: they contain hard-coded model/data paths and CUDA settings; do not use them as portable checks.
- Treating `--help` as a model test: help only checks import/parser construction, not checkpoint compatibility.
