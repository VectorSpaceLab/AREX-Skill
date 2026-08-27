---
name: audio-text-metrics
description: "Use TorchMetrics audio/speech quality metrics and no-download text
  metrics safely."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# audio-text-metrics

Use this sub-skill when a task needs TorchMetrics audio/speech quality scores or text scores that can run without loading pretrained models or downloading datasets.

## Route here

- Intrusive audio quality: SNR, SI-SNR, SDR, SI-SDR, source-aggregated SDR, complex SI-SNR, PESQ, and STOI.
- Speech separation matching: permutation invariant training (PIT) over waveform or source-separation metrics.
- Non-intrusive classical audio metric: SRMR, when its local optional packages are installed.
- Decoded-text metrics: BLEU, SacreBLEU, ChrF/ChrF++, ROUGE without model embeddings, CER, WER, MER, WIL, WIP, TER, EditDistance, and SQuAD.
- Logit metric: Perplexity from language-model logits or unnormalized scores.

## Route elsewhere

- Read `../core-api/SKILL.md` for Metric lifecycle, `update`/`compute`/`reset`, device placement, distributed synchronization, Lightning logging, and custom metrics.
- Read `../collections-wrappers-plotting/SKILL.md` for MetricCollection, wrappers, trackers, and plotting mechanics.
- Read `../model-based-metrics/SKILL.md` for BERTScore, InfoLM, CLIP or embedding metrics, DNSMOS, NISQA, and any metric that needs pretrained weights, caches, or network/cache planning.

## Read and run

- Read [references/audio-text-api.md](references/audio-text-api.md) when choosing metric classes/functions, input shapes, target nesting, optional dependencies, and higher/lower-is-better interpretation.
- Read [references/audio-text-workflows.md](references/audio-text-workflows.md) when scoring generated waveforms, speech separation outputs, ASR transcripts, summaries, translations, SQuAD answers, or language-model logits.
- Read [references/troubleshooting.md](references/troubleshooting.md) when imports fail, PESQ/STOI reject audio, ROUGE/SacreBLEU tokenization surprises occur, or perplexity looks wrong.
- Run [scripts/audio_text_metric_smoke.py](scripts/audio_text_metric_smoke.py) to perform a deterministic no-network smoke check for installed TorchMetrics audio/text metrics; use `--audio`, `--text`, or `--all`.

## Safe defaults

1. Treat `preds` as the model output and `target` as the reference/ground truth.
2. For waveform-pair metrics, pass float tensors with identical shape and time along the last dimension.
3. For text overlap/error metrics, pass already-decoded strings; do not pass token IDs or logits.
4. For Perplexity, pass float logits shaped `[batch, sequence, vocabulary]` and integer targets shaped `[batch, sequence]`; TorchMetrics does not shift language-model outputs for you.
5. Avoid network-sensitive metric choices unless the task explicitly asks for them and the environment/cache is approved.
