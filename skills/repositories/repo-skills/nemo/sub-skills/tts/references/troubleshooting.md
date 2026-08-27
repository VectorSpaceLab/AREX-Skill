# TTS Troubleshooting

Use this reference when NeMo Speech TTS synthesis, training, MagpieTTS, EasyMagpie, G2P, audio codec, or evaluation work fails.

## Quick Triage

| Symptom | First checks | Likely fix |
| --- | --- | --- |
| Import fails before model loading | Python, PyTorch, NeMo install, optional TTS deps | Install workflow-specific dependencies only; avoid broad extras unless needed |
| Text normalization fails | `nemo_text_processing`, language support, platform | Install compatible text-processing package or provide pre-normalized text |
| Phoneme/G2P errors | Dictionary path, tokenizer language, phonemizer package | Match checkpoint tokenizer and install language-specific resources |
| Noisy/chipmunk/slow audio from cascade | FastPitch/vocoder sample-rate or mel mismatch | Use matched acoustic/vocoder checkpoints and mel settings |
| Magpie repeats/skips words | Long text, attention prior off, poor punctuation, max steps | Enable attention prior, add punctuation, use long-form mode, raise max steps |
| Magpie wrong voice | Context audio mismatch, too short context, speaker field mismatch | Use same-speaker context audio, 3–10 second context, fix speaker metadata |
| Old Magpie checkpoint shape errors | Special-token/codebook layout changed | Use legacy flags or forced special-token overrides; reject invalid layouts |
| Hydra override rejected | Missing `+`, wrong key path, shell quoting | Add `+` for new keys, quote list overrides, verify config name |
| Evaluation metric fails | ASR/SV/UTMOS/FCD/EoU optional dependency or download | Disable metric or provide local model paths |

## Install and Import Failures

Current NeMo Speech docs expect Python 3.12+, PyTorch 2.7+, and GPU/CUDA for normal training. Optional broad extras were not installed during this skill's evidence pass, so future agents should not assume every TTS dependency is present.

Check environment basics:

```python
import torch
import nemo.collections.tts as nemo_tts
print(torch.__version__)
print(torch.cuda.is_available())
```

Common issues:

- `ModuleNotFoundError: nemo_text_processing`: text normalization is optional. Install a compatible `nemo_text_processing` package or pass already-normalized text and disable/bypass normalization where possible.
- `ModuleNotFoundError` for `phonemizer`, `inflect`, language dictionaries, or tokenizer libraries: install only the phoneme/G2P dependencies required by the selected language/checkpoint.
- `ImportError` from `soundfile` or `libsndfile`: install the Python package and the system audio library required by the platform.
- `librosa`/audio backend failures: verify NumPy/librosa compatibility and avoid opening audio in read-only manifest checks.
- CUDA unavailable or incompatible: training should not proceed; for inference, reduce batch size or run a small CPU smoke only if acceptable.
- `from_pretrained()` hangs or fails: the method may download from a model registry. Use local `.nemo` paths when offline or cache policy forbids network.

`nemo_text_processing` can have platform constraints; do not promise it works on every operating system. For restricted platforms, normalize text outside NeMo and set configs/API calls to avoid runtime TN.

## Manifest and Data Errors

Run the bundled checker first:

```bash
python scripts/check_tts_manifest.py manifest.jsonl --mode tts --require-audio --check-files --style-summary
```

Common failures:

- Blank lines: remove them; NeMo manifests use one JSON object per line.
- Missing `audio_filepath`: allowed only for text-only inference or G2P input; training/evaluation needs audio.
- Empty `text`: invalid for TTS training and most inference. For G2P inference, use `text_graphemes` instead.
- Nonpositive or nonnumeric `duration`: fix metadata before batching/filtering.
- Duplicate `id`, `audio_filepath`, or context paths: deduplicate or split records intentionally.
- Relative paths fail: set `audio_dir`, `feature_dir`, `--audio-base-dir`, or make paths absolute in caller-owned private manifests.
- `normalized_text` contradicts `text`: choose one convention and regenerate normalization.
- Missing `speaker` in multispeaker work: add stable speaker IDs or use a single-speaker config.
- Missing Magpie `context_audio_filepath` or `context_text`: either use a checkpoint/config that does not require them or add context metadata.
- Cached code paths point to the wrong codec output: regenerate codes with the exact codec checkpoint expected by Magpie.

## Text Normalization and Tokenization

Text issues often sound like model quality problems:

- Digits, currency, abbreviations, dates, and symbols require text normalization unless the checkpoint was trained to handle raw forms.
- FastPitch `parse(text, normalize=True)` uses the model's normalizer when configured; if it is absent, normalize text before calling.
- Long-form Magpie relies on punctuation for sentence splitting. Add periods/question marks/exclamation marks to long text.
- Mandarin currently falls back from Magpie long-form to standard inference in documented behavior; do not promise robust chunked Mandarin long-form.
- Do not strip punctuation for G2P models trained with punctuation.
- Avoid mixing languages in one utterance unless the tokenizer/config explicitly supports it.

Grapheme-vs-phoneme pitfalls:

- ARPABET and IPA checkpoints expect different phoneme inventories.
- Mixed grapheme/phoneme tokenizers can be valid, but random record-level mixing is a data bug.
- Heteronyms should be resolved consistently using dictionary/G2P/aligner logic.
- If OOV words are pronounced poorly, use G2P or manually provide phoneme form expected by the tokenizer.
- If a tokenizer reports unsupported characters, inspect Unicode normalization and language-specific punctuation.

## FastPitch and HiFi-GAN Cascade Failures

| Symptom | Cause | Fix |
| --- | --- | --- |
| `parse()` errors on characters | Unsupported tokenizer/language | Normalize text, choose matching language checkpoint, or use G2P/phoneme input |
| `generate_spectrogram()` shape/speaker error | Multispeaker checkpoint expects speaker/reference input | Pass valid `speaker` ID or required reference spec fields |
| Robotic/noisy audio | Vocoder and mel generator mismatch | Use matching HiFi-GAN checkpoint and sample-rate/mel settings |
| Audio speed/pitch wrong | `pace`, pitch stats, sample rate mismatch | Adjust `pace`, verify pitch normalization and output sample rate |
| CUDA OOM | Batch too large or long text | Generate one utterance at a time, reduce precision carefully, shorten text |
| Training diverges | Bad durations, silence, pitch/align priors, LR too high | Filter manifest, regenerate supplementary data, lower LR |

When finetuning:

- Use `+init_from_nemo_model`, `+init_from_pretrained_model`, or `+init_from_ptl_ckpt` with the `+` prefix for keys absent from the base config.
- Remove schedulers with `~model.optim.sched` only when the config has that key.
- Keep train/validation sample rates and tokenizer settings identical.
- Inspect a small validation batch before long training.

## MagpieTTS and EasyMagpie Failures

### Loading and checkpoint mode

- Provide exactly one loading mode: `--nemo_files` or `--hparams_files` plus `--checkpoint_files`.
- Always provide `--codecmodel_path` for Magpie/EasyMagpie inference.
- If `hparams.yaml` came from WandB, use the corresponding flag from the inference contract.
- If the checkpoint config references stale local paths, override tokenizer or codec paths with caller-owned paths.

### Legacy codebooks and special tokens

Old Magpie checkpoints may predate the current special-token layout.

Use `--legacy_codebooks` for old checkpoints when the inference script supports it. Equivalent forced overrides for a 2048-token legacy decoder-context model are:

```bash
+model.forced_num_all_tokens_per_codebook=2048 \
+model.forced_audio_bos_id=2046 \
+model.forced_audio_eos_id=2047 \
+model.forced_context_audio_bos_id=2044 \
+model.forced_context_audio_eos_id=2045
```

For old multi-encoder or single-encoder context models, context BOS/EOS match audio BOS/EOS:

```bash
+model.forced_num_all_tokens_per_codebook=2048 \
+model.forced_audio_bos_id=2046 \
+model.forced_audio_eos_id=2047 \
+model.forced_context_audio_bos_id=2046 \
+model.forced_context_audio_eos_id=2047
```

Warnings:

- A short-lived 2018-token layout overwrote codec token IDs. Treat those checkpoints as suspect and do not force them unless the user has strong evidence.
- Some 2024-token intermediate checkpoints may need manual forced IDs with special tokens at the end.
- `--legacy_text_conditioning` and EasyMagpie `--disable_cas_for_context_text` solve different compatibility issues; apply only when the checkpoint history indicates them.

### Repetition, skipping, and long-form artifacts

- Enable attention prior for challenging text.
- Increase `max_decoder_steps` for long utterances.
- Use `--longform_mode auto` or `always` for long text, especially English text above threshold.
- Add sentence punctuation. Long-form splitting depends on punctuation and handles common abbreviations but cannot infer missing boundaries reliably.
- Lower `temperature` for more deterministic output; increase only if output is overly flat.
- Use `topk=80` as a safe baseline; extreme top-k can increase artifacts.
- Use `--use_cfg --cfg_scale 2.5` as a baseline, then tune. Too high CFG can over-constrain style or degrade intelligibility.

### Context and speaker problems

- Ensure `context_audio_filepath` is same speaker and similar recording domain when voice cloning.
- Use a context duration around 3–10 seconds; 5 seconds is a common finetuning value.
- Ensure `context_text` matches the context audio when text conditioning is used.
- For multilingual context, set `language` and tokenizer metadata correctly; source code can add language tags to context text when configured.
- Do not mix target and context speakers unless intentionally testing style transfer failure modes.

### EasyMagpie-specific issues

- Use `--model_type easy_magpie`; otherwise the runner will assume encoder-decoder Magpie.
- Set `--phoneme_input_type gt` only when the dataset provides ground-truth phonemes.
- Use `--phoneme_input_type predicted` when the model should predict phonemes.
- Use `--phoneme_sampling_method argmax` for stable evaluation and `multinomial` for sampled diversity.
- Use `--phoneme_tokenizer_path` if the checkpoint-stored tokenizer path is invalid.

## G2P Failures

| Symptom | Cause | Fix |
| --- | --- | --- |
| Missing `text_graphemes` | Wrong manifest schema | Add grapheme field or set `grapheme_field` override |
| Missing phoneme labels during training | Inference manifest used for training | Add `text` phoneme labels or switch to inference mode |
| Poor heteronym handling | Word-level data lacks context | Use sentence-level G2P training/evaluation data |
| CTC tokenizer error | Missing tokenizer dir or punctuation mismatch | Provide tokenizer dir and match lowercase/punctuation settings |
| Unexpected punctuation output | Training/inference punctuation policy mismatch | Keep punctuation preprocessing consistent |

G2P requires NeMo ASR collection support in addition to TTS. If ASR imports are absent, install the ASR dependency set needed for G2P rather than unrelated TTS extras.

## Audio Codec Failures

- If codec training rejects samples, check segment duration and min-duration filtering.
- If Magpie cannot load cached codes, verify paths, tensor format, and codec compatibility.
- If generated audio is distorted, verify codec sample rate and codebook layout before blaming TTS decoder.
- If training OOMs, reduce batch duration, batch size, segment duration, or number of workers.
- If DDP shard behavior is wrong, verify Lhotse/tarred dataset shard strategy (`scatter` vs `replicate`) before launching multi-GPU jobs.

## Hydra and Config Errors

Hydra patterns:

- Use `key=value` for existing keys.
- Use `+key=value` for keys absent from the config.
- Use `~key` to delete keys.
- Quote list overrides in the shell, for example `'+train_ds_meta.en.tokenizer_names=[english_phoneme]'`.
- Choose the config directory/name that matches the model family and sample rate.
- Prefer explicit `trainer.accelerator=gpu trainer.devices=1` over relying on defaults.

Common fixes:

- If `Could not override` mentions a missing key, add `+` or correct the key path.
- If a list is parsed incorrectly, quote it.
- If a config interpolation fails, set all required dataset, codec, and output fields explicitly.
- If a model class cannot instantiate, verify `_target_` paths and optional dependencies.

## Evaluation Metric Failures

Magpie inference/evaluation can compute CER/WER, speaker similarity, UTMOSv2, Frechet Codec Distance, EoU metrics, RTF, and FLOPs. These are optional-heavy.

- If ASR model loading fails, provide a local ASR model path or skip CER/WER.
- If speaker similarity fails, switch `--sv_model titanet`/`wavlm` or provide dependencies.
- If UTMOSv2 fails, pass `--disable_utmosv2`.
- If FCD fails, pass `--disable_fcd`.
- If EoU model download is blocked, provide a local `--eou_model_name` path or skip EoU analysis.
- If repeated inference fills disk, use `--num_repeats 1` first and clean output roots deliberately.

## Difficult Case Playbooks

### Old Magpie checkpoint sweep

For multiple old checkpoints, create a table before running:

| Checkpoint | Model type | Codec path | Legacy codebooks | Legacy text conditioning | EasyMagpie CAS disabled | Context type | Output dir |
| --- | --- | --- | --- | --- | --- | --- | --- |

Then run one smoke item per checkpoint before batch generation. Fail fast on shape mismatches and do not reuse generated output directories across incompatible flags.

### Mixed G2P/TTS dataset cleanup

For a dataset with grapheme and phoneme fields, missing speakers, empty text, and duration outliers:

1. Run `python scripts/check_tts_manifest.py data.jsonl --mode magpie --require-audio --min-duration 0.2 --max-duration 20 --style-summary`.
2. Separately run `python scripts/check_tts_manifest.py data.jsonl --mode g2p --grapheme-field text_graphemes --phoneme-field text --allow-missing-phonemes` if G2P inference labels are expected.
3. Split TTS records from G2P-only records instead of forcing one manifest to satisfy both schemas.
4. Add speaker IDs for multispeaker work or choose a single-speaker config.
5. Normalize text/phoneme conventions per language before finetuning.

## When to Stop and Ask

Ask the user before:

- Installing broad optional extras or changing a shared environment.
- Downloading checkpoints, metrics models, datasets, or Hugging Face resources.
- Launching GPU training, preference optimization, or large batch inference.
- Overwriting output directories or generated audio.
- Using voice-cloning context audio in a way that could expose private speaker data.
- Proceeding with suspect legacy checkpoints whose codebook layout cannot be identified.
