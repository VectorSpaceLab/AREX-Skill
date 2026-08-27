# Audio and text troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `PerceptualEvaluationSpeechQuality` rejects your input | `fs` is not `8000` or `16000`, `mode` is not `nb` or `wb`, or the tensors do not align | Pass a supported sampling rate and mode, and keep waveform shapes identical. |
| PESQ is slower than expected or pinned to CPU | PESQ is a CPU wrapper and can also use multiprocessing for batches | Keep the smoke script tiny; do not expect a GPU speedup from PESQ. |
| SDR/SI-SDR/PIT look inconsistent | The source/target ordering or speaker axis is wrong | Check whether the metric expects `[batch, speakers, time]` or pairwise waveforms and keep the tensors aligned. |
| `SignalDistortionRatio` complains about missing `fast_bss_eval` | The optional package is not installed | Install the `audio` extra or the missing package, or use a simpler audio metric. |
| `STOI` or `PESQ` import fails | Their optional packages are missing | Install `torchmetrics[audio]` or the exact dependency named in the metric error. |
| ROUGE-Lsum fails or tries to download `nltk` data | NLTK sentence segmentation resources are missing | Install `nltk` and its punkt resources, or avoid `rougeLsum` when you only need overlap scores. |
| SacreBLEU tokenizer errors mention `regex`, `MeCab`, `ipadic`, `mecab_ko`, `mecab_ko_dic`, or `sentencepiece` | The selected tokenizer needs extra packages | Either install the tokenizer extras or switch to a simpler tokenizer such as `13a`, `none`, or `char`. |
| WER/CER/MER look too large | The inputs are token ids, not decoded strings | Decode to strings first; these metrics operate on text strings. |
| Perplexity is unexpectedly high | The targets were not shifted or padding tokens were not ignored | Shift logits/targets before calling the metric and pass `ignore_index` for padding. |
| Perplexity refuses a tensor shape | Logits and target shape do not match `[batch, seq_len, vocab]` / `[batch, seq_len]` | Check the time dimension and vocabulary dimension explicitly. |
| BERTScore/CLIPScore complaints appear in this route | The task actually needs pretrained model execution | Switch to `../model-based-metrics/` rather than forcing a no-download text route. |
