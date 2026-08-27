# Metrics and scoring

SpeechBrain provides metric accumulator classes and edit-distance/WER utilities that are commonly used inside `Brain` hooks.

## Verified signatures

```python
speechbrain.utils.metric_stats.MetricStats.append(ids, *args, **kwargs)
speechbrain.utils.metric_stats.ErrorRateStats.append(ids, predict, target, predict_len=None, target_len=None, ind2lab=None)
speechbrain.utils.metric_stats.BinaryMetricStats.append(ids, scores, labels)
speechbrain.utils.metric_stats.ClassificationStats.append(ids, predictions, targets, categories=None)
```

## Recipe metric pattern

```python
class MyBrain(sb.Brain):
    def on_stage_start(self, stage, epoch=None):
        if stage != sb.Stage.TRAIN:
            self.error_metrics = self.hparams.error_stats()

    def compute_objectives(self, predictions, batch, stage):
        loss = self.hparams.compute_cost(predictions, batch.targets)
        if stage != sb.Stage.TRAIN:
            self.error_metrics.append(batch.id, predictions, batch.targets)
        return loss

    def on_stage_end(self, stage, stage_loss, epoch=None):
        if stage != sb.Stage.TRAIN:
            print(self.error_metrics.summarize("error_rate"))
```

## WER/PER/CER utilities

SpeechBrain's edit-distance utilities support utterance-level details, summary metrics, top-error utterances/speakers, and alignment output. Use the bundled `scripts/compute_wer_cli.py` for Kaldi-style `utt tokens...` text files.

Input example:

```text
utt1 THE QUICK BROWN FOX
utt2 HELLO WORLD
```

Run:

```bash
python scripts/compute_wer_cli.py ref.txt hyp.txt --mode strict --print-top-wer
```

Scoring modes:

- `strict`: missing hypothesis keys raise an error.
- `present`: score only references that have hypotheses.
- `all`: treat missing hypotheses as empty.

## Choosing metric classes

- ASR/G2P/token sequences: `ErrorRateStats` or edit-distance utilities.
- Binary frame or event decisions: `BinaryMetricStats`.
- Multi-class predictions: `ClassificationStats`.
- Custom scalar functions: `MetricStats` with a metric callable.
- Multiple metrics together: `MultiMetricStats` when needed.

## Common mistakes

- Passing logits where decoded token sequences are expected.
- Passing absolute lengths where relative lengths are expected, or vice versa.
- Using an `ind2lab` mapping that does not match the tokenizer/encoder.
- Treating tiny debug metrics as production model quality.
- Comparing metrics generated from different tokenization or normalization conventions.
