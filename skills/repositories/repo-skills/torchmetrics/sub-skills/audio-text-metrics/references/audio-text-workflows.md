# Audio and text workflows

## 1) Audio SNR and PESQ on synthetic waveforms

```python
import math
import torch
from torchmetrics.audio import SignalNoiseRatio, PerceptualEvaluationSpeechQuality

fs = 16000
wave = torch.sin(torch.linspace(0, 2 * math.pi, fs))
noisy = wave + 0.01 * torch.randn_like(wave)

snr = SignalNoiseRatio()
pesq = PerceptualEvaluationSpeechQuality(fs=fs, mode="wb")

print(snr(noisy, wave))
print(pesq(wave, noisy))
```

Practical notes:

- Keep waveform tensors the same shape and dtype.
- PESQ only accepts `fs=8000` or `fs=16000` and `mode='nb'` or `'wb'`.
- PESQ internally moves computation to CPU.

## 2) Speech separation with PIT

```python
import torch
from torchmetrics.audio import PermutationInvariantTraining
from torchmetrics.functional.audio import signal_distortion_ratio

preds = torch.randn(2, 3, 8000)
target = torch.randn(2, 3, 8000)
pit = PermutationInvariantTraining(signal_distortion_ratio, mode="speaker-wise", eval_func="max")
print(pit(preds, target))
```

Practical notes:

- Use `[batch, speakers, time]` shapes.
- `metric_func` should match the separation goal.
- For speaker counts greater than 3, the SDR docs recommend `scipy` for better performance.

## 3) ASR decoding quality

```python
from torchmetrics.text import WordErrorRate, CharErrorRate

preds = ["this is the prediction", "there is an other sample"]
target = ["this is the reference", "there is another one"]

wer = WordErrorRate()
cer = CharErrorRate()

print(wer(preds, target))
print(cer(preds, target))
```

Practical notes:

- These metrics expect decoded strings, not token ids or logits.
- Keep the same number of predictions and references.

## 4) Translation and text overlap

```python
from torchmetrics.text import BLEUScore, SacreBLEUScore, ROUGEScore, CHRFScore

preds = ["the cat sat on the mat"]
target = [["the cat is on the mat", "a cat is on the mat"]]

print(BLEUScore()(preds, target))
print(SacreBLEUScore()(preds, target))
print(CHRFScore()(preds, ["the cat is on the mat"]))
print(ROUGEScore(use_stemmer=False)(preds, ["the cat is on the mat"]))
```

Practical notes:

- ROUGE-Lsum can require `nltk` sentence tokenization resources.
- SacreBLEU tokenizers such as `intl`, `ja-mecab`, `ko-mecab`, and `flores` tokenizers need optional packages.

## 5) Perplexity from logits

```python
import torch
from torchmetrics.text import Perplexity

logits = torch.randn(2, 4, 1000)
target = torch.randint(1000, (2, 4))

perplexity = Perplexity(ignore_index=None)
print(perplexity(logits, target))
```

Practical notes:

- Pass logits or unnormalized scores with shape `[batch, seq_len, vocab]`.
- Pass integer targets with shape `[batch, seq_len]`.
- If your language model produces shifted labels, shift them before calling TorchMetrics.
- Use `ignore_index` to exclude padding tokens.

## 6) Smoke script workflow

Run the bundled smoke helper when you want a no-download sanity check.

```bash
python scripts/audio_text_metric_smoke.py --audio --text
python scripts/audio_text_metric_smoke.py --all
```

Use the smoke script only after the package is installed in the current environment; it avoids model downloads and interactive playback.
