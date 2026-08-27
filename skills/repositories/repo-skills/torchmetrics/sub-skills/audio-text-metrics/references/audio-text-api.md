# Audio and text metric API reference

This reference groups the TorchMetrics audio/speech and no-download text metrics by input contract so future agents can choose the right call quickly.

## Audio and speech quality metrics

| Metric | Class / functional | Core inputs | Key args | Output | Notes |
| --- | --- | --- | --- | --- | --- |
| Signal-to-noise ratio | `SignalNoiseRatio` / `signal_noise_ratio` | `preds`, `target` float tensors with matching shape and time on the last axis | `zero_mean` | Scalar tensor | Simple waveform quality metric. |
| Scale-invariant SNR | `ScaleInvariantSignalNoiseRatio` / `scale_invariant_signal_noise_ratio` | Matching waveform tensors | none beyond base `Metric` kwargs | Scalar tensor | Useful when overall scale should not matter. |
| Complex SI-SNR | `ComplexScaleInvariantSignalNoiseRatio` / `complex_scale_invariant_signal_noise_ratio` | Complex or real-valued waveform tensors with matching shapes | `zero_mean` | Scalar tensor | Specialized separation metric. |
| SDR / SI-SDR | `SignalDistortionRatio`, `ScaleInvariantSignalDistortionRatio`, `SourceAggregatedSignalDistortionRatio` | Matching waveform tensors | `use_cg_iter`, `filter_length`, `zero_mean`, `load_diag`, `scale_invariant` | Scalar tensor | `SignalDistortionRatio` can use `fast_bss_eval`; the other variants are simpler special cases. |
| PIT | `PermutationInvariantTraining` / `permutation_invariant_training` | Predicted and target source tensors, typically `[batch, speakers, time]` | `metric_func`, `mode`, `eval_func` | Scalar tensor | Wrap a source metric and evaluate the best permutation. |
| PESQ | `PerceptualEvaluationSpeechQuality` / `perceptual_evaluation_speech_quality` | Waveform tensors with matching shapes | `fs`, `mode`, `n_processes` | Scalar tensor | `fs` must be `8000` or `16000`; `mode` must be `"nb"` or `"wb"`. The wrapper moves computation to CPU. |
| STOI | `ShortTimeObjectiveIntelligibility` / `short_time_objective_intelligibility` | Matching waveform tensors | `fs`, `extended` | Scalar tensor | Speech intelligibility metric. |
| SRMR | `SpeechReverberationModulationEnergyRatio` / `speech_reverberation_modulation_energy_ratio` | Matching waveform tensors | `fs`, `n_cochlear_filters`, `low_freq`, `fast` | Scalar tensor | Requires `gammatone` and `torchaudio`. |

## No-download text metrics

| Metric | Class / functional | Core inputs | Key args | Output | Notes |
| --- | --- | --- | --- | --- | --- |
| BLEU | `BLEUScore` / `bleu_score` | Predicted strings and one or more reference strings | `n_gram`, `smooth`, `weights` | Scalar tensor | Pure text overlap score. |
| SacreBLEU | `SacreBLEUScore` / `sacre_bleu_score` | Predicted strings and grouped references | `n_gram`, `smooth`, `tokenize`, `lowercase`, `weights` | Scalar tensor | Tokenizer choice can require `regex`, MeCab, `ipadic`, `mecab_ko`, or `sentencepiece`. |
| ChrF | `CHRFScore` / `chrf_score` | Predicted and reference strings | `n_char_order`, `n_word_order`, `beta`, `lowercase`, `whitespace` | Scalar tensor | Character n-gram metric. |
| ROUGE | `ROUGEScore` / `rouge_score` | Predicted and reference strings | `use_stemmer`, `normalizer`, `tokenizer`, `accumulate`, `rouge_keys` | Dict of tensors | Use `rouge_keys` without `rougeLsum` when you want to avoid sentence-tokenizer downloads. |
| CER / WER / MER / WIL / WIP / TER | `CharErrorRate`, `WordErrorRate`, `MatchErrorRate`, `WordInfoLost`, `WordInfoPreserved`, `TranslationEditRate` | Decoded text strings | usually none beyond base `Metric` kwargs | Scalar tensor | Treat these as edit-distance style metrics for ASR and translation. |
| Edit distance | `EditDistance` / `edit_distance` | Strings or token sequences depending on the helper | `substitution_cost`, `reduction` | Scalar or reduced tensor | General edit-distance primitive. |
| Perplexity | `Perplexity` / `perplexity` | Logits or unnormalized scores shaped `[batch, seq_len, vocab]` plus integer targets shaped `[batch, seq_len]` | `ignore_index` | Scalar tensor | TorchMetrics does not shift language-model labels for you. |
| SQuAD | `SQuAD` / `squad` | QA predictions and references | task-specific QA fields | Dict of tensors | Text QA scoring without model downloads. |

## Route elsewhere

- Read `../core-api/` for `Metric` lifecycle, synchronization, device placement, persistence, and Lightning logging.
- Read `../model-based-metrics/` for BERTScore, InfoLM, CLIPScore, DNSMOS, NISQA, and any metric that needs pretrained weights, caches, or network planning.
- Read `../collections-wrappers-plotting/` for `MetricCollection`, wrappers, trackers, and plotting mechanics.
