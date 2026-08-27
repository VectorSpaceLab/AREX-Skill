# Inference and Model-Zoo Troubleshooting

## Purpose

Use this file to diagnose Python API, model registry, pretrained inference, custom checkpoint, speaker/language, download/cache/TOS, and `split_sentences` failures. Cross-cutting installation issues may also be covered by the root skill troubleshooting reference once integrated.

## Failure matrix

| Symptom or error fragment | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'TTS'` | Coqui TTS is not installed in the active Python environment. | Install distribution `TTS` into a supported Python 3.9-3.11 environment, then run `python -c "import TTS; print(TTS.__version__)"`. Do not rely on an original source checkout. |
| Import succeeds for `TTS` but `from TTS.api import TTS` fails with `torch`, `torchaudio`, `librosa`, or `soundfile` import errors | Incomplete runtime dependencies or incompatible audio/PyTorch stack. | Repair the package install, PyTorch/torchaudio ABI, and audio system libraries before model loading. Registry-only helper help still works, but inference will not. |
| Python is 3.12+ or 3.13+ | Package metadata supports `>=3.9,<3.12`; newer Python may import partially or fail in dependencies. | Use Python 3.9, 3.10, or 3.11 for supported behavior. Treat Python 3.12+ behavior as unsupported even if a small import appears to work. |
| `model_type ... does not exist`, `lang ... does not exist`, `dataset ... does not exist`, or `model ... does not exist` | Model name does not match registry grammar. | Use `python scripts/inspect_tts_models.py --contains <term>` and verify `<model_type>/<language>/<dataset>/<model>`. For Fairseq use dynamic `tts_models/<iso3_language_code>/fairseq/vits`. |
| `TTS().list_models()` printed an object instead of model names | `TTS.list_models()` returns a `ModelManager`; it is not itself a list. | Use `manager = TTS().list_models(); manager.list_models()` or `python scripts/inspect_tts_models.py --count`. |
| Download hangs, fails with network errors, or reports a bad archive | Released model loading downloads large files through registry URLs; network, proxy, disk, or remote availability failed. | Do not retry blindly. Confirm network and disk budget; choose a smaller model; pre-populate cache under user control; or switch to custom checkpoint paths. Use registry inspection for planning-only tasks. |
| Prompt says the user must agree to terms of service | Model registry has `tos_required`, commonly XTTS CPML models. | Stop for explicit user approval. Do not answer prompts, pipe `yes`, or set `COQUI_TOS_AGREED=1` unless the user has accepted the applicable terms for this task. |
| Model repeatedly redownloads or says cache changed | Model hash/config check detected stale or mismatched cached files. | Confirm cache writes are allowed, enough disk exists, and no concurrent process is mutating the cache. If not allowed, use a custom local checkpoint path instead. |
| `AssertionError: CUDA is not availabe on this machine.` | `Synthesizer(use_cuda=True)` or equivalent GPU path was requested without available CUDA. | Use CPU (`use_cuda=False` or `.to("cpu")`) or select a valid CUDA environment. CUDA is optional for metadata checks but may be needed for practical XTTS/Bark/Tortoise speed. |
| CPU inference is extremely slow | Large model family, long input, or no GPU acceleration. | Use a smaller released model for smoke tests, shorten text, keep `split_sentences=True`, or request a GPU budget. Do not claim performance from CPU-only checks. |
| `Model is multi-speaker but no speaker is provided` | `TTS.api.TTS` loaded a multi-speaker model and neither `speaker` nor `speaker_wav` was passed. | Inspect `tts.speakers` after loading and pass `speaker=...`, or provide `speaker_wav=...` for cloning-capable models. |
| `Looks like you are using a multi-speaker model. You need to define either a speaker_idx or a speaker_wav` | Direct `Synthesizer` path lacks multi-speaker selection. | Provide `speaker_name` from the speaker manager, provide `speaker_wav`, or provide the correct speakers file when using a custom checkpoint. |
| `Model is multi-lingual but no language is provided` or `You need to define either a language_name...` | Multilingual model was loaded without `language`/`language_name`. | Inspect `tts.languages` or the language manager and pass a valid language code/name, for example `language="en"` for XTTS. |
| `Language <x> is not in the available languages` | Language code does not match loaded model's language manager. | Print `tts.languages` or direct model language names and choose an exact value. Do not assume docs and registry language counts are identical. |
| `Model is not multi-speaker but speaker is provided` | A speaker argument was passed to a single-speaker model. | Remove `speaker`; if the user needs voice cloning from a single-speaker model, use `tts_with_vc_to_file` and route details to the voice-conversion sub-skill. |
| `Model is not multi-lingual but language is provided` | A language argument was passed to a monolingual model. | Remove `language` or choose a multilingual model such as XTTS/YourTTS/Fairseq. |
| `Phonemizer is not defined in the TTS config` | Custom checkpoint config sets `use_phonemes` without a configured phonemizer. | Fix the config to specify a supported phonemizer and ensure any system dependency is installed, or use a checkpoint/config pair that matches the model. |
| `Model file not found in the output path` or `Config file not found in the output path` | Downloaded/custom model directory lacks expected files, or wrong path was provided. | For normal checkpoints, provide a `.pth`/`.pth.tar` and `config.json`. For multi-file models, load by model directory when appropriate. Re-query the registry if using a released model. |
| Custom checkpoint loads but synthesis shape/audio fails | TTS checkpoint, config, speakers/languages files, vocoder config, or vocoder checkpoint do not match. | Verify checkpoint/config pair, speaker/language metadata, mel dimensions, sample rate, hop length, and vocoder normalization. Route deep vocoder analysis to `../vocoder-and-audio-tools/SKILL.md`. |
| Output audio is clipped, silent, wrong speed, or wrong sample rate | Vocoder mismatch, sample-rate mismatch, audio processor settings, or unsupported model kwargs. | Validate TTS and vocoder audio configs; try the model's default vocoder; keep extra kwargs minimal; route audio diagnostics to `../vocoder-and-audio-tools/SKILL.md`. |
| Long text OOMs or loses context | `split_sentences` tradeoff: `True` reduces memory/context pressure by segmenting; `False` preserves context but can exceed model context/VRAM. | Start with `split_sentences=True`. For coherence-critical short passages, try `False` only with enough memory and a fallback plan. Split user text manually for deterministic control. |
| XTTS/Bark/Tortoise/Fairseq load behaves differently from normal checkpoints | These families can use multi-file model directories and no default external vocoder. | Treat them as large model-directory loads; require download approval; avoid overriding vocoders unless the model docs/API supports it; inspect model-specific properties after load. |
| `tts_with_vc_to_file` fails around missing `speaker_wav` or FreeVC download/cache | Mixed TTS+VC path needs a target speaker reference and may lazily load FreeVC. | Confirm `speaker_wav` exists and user approved any FreeVC download/cache use. Route source/target conversion details to `../voice-conversion/SKILL.md`. |

## Minimal diagnostic sequence

1. Run `python scripts/inspect_tts_models.py --count`. If this fails, fix package import/version first.
2. Query the chosen model: `python scripts/inspect_tts_models.py --query <full-model-name> --format table`.
3. Run `python scripts/synthesize_text.py ... --dry-run` with all intended text, model, speaker, language, and output arguments.
4. Only after user approval for download/cache/TOS, rerun the helper with `--allow-download` or use the equivalent Python API directly.

## When to stop and ask the user

Stop before continuing when:

- Model loading would require a new download or TOS acceptance and the user has not approved it.
- The user did not provide required `speaker`, `speaker_wav`, or `language` values and the model requires them.
- The requested model family is likely too slow or large for the available budget.
- A custom checkpoint/config/vocoder mismatch cannot be resolved from local files.
