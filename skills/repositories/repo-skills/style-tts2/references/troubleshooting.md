# Cross-cutting troubleshooting

## Source checkout is not importable

Symptoms:
- `ModuleNotFoundError` for `models`, `Modules`, `Utils`, or `meldataset`.
- A custom snippet works only when run from a notebook cell but fails elsewhere.

Likely causes:
- The repository root is not the current working directory and is not on `PYTHONPATH`.
- The user tried `pip install -e .`, but the checkout has no packaging metadata.

Recovery:
- Run commands from the checkout root, or use bundled helpers with `--repo-root`.
- For custom snippets, insert the checkout root into `sys.path` before importing repository modules.
- Run [../scripts/check_runtime.py](../scripts/check_runtime.py) to confirm source imports.

## Missing hidden runtime dependencies

Symptoms:
- `ImportError: No module named pandas` from `meldataset.py`.
- `ImportError` or `ModuleNotFoundError` around TensorBoard / `torch.utils.tensorboard`.
- Training `--help` fails even though `requirements.txt` was installed.

Likely causes:
- The requirements file omits `pandas` and `tensorboard`.

Recovery:

```bash
python -m pip install pandas tensorboard
```

Then re-run safe help/import checks before launching training.

## Torch import fails with Intel OpenMP / MKL symbol errors

Symptom:
- `ImportError` from `libtorch_cpu.so` mentioning `undefined symbol: iJIT_NotifyEvent`.

Likely cause:
- A conda PyTorch build is paired with an incompatible Intel OpenMP/MKL runtime.

Recovery:
- Use a tested CUDA PyTorch/Torchaudio wheel or conda stack.
- In conda environments, try a compatible `intel-openmp`/MKL version rather than editing StyleTTS2 source.
- Re-run `python -c "import torch; print(torch.__version__, torch.cuda.is_available())"` after the environment fix.

## CUDA is unavailable

Symptoms:
- `torch.cuda.is_available()` is false.
- Training fails while moving tensors to `cuda`.

Recovery:
- Training/fine-tuning require CUDA for native behavior. Use a CUDA-enabled PyTorch/Torchaudio build and visible NVIDIA GPU.
- Do not claim CPU-only training verification for this repo.
- For inference-only tasks, CPU is acceptable but slower.

## Model/helper assets are missing

Symptoms:
- `torch.load` fails for ASR/F0/PLBERT paths.
- Inference checker reports missing `Models/LJSpeech` or `Models/LibriTTS` files.
- LibriTTS demo has no `Demo/reference_audio` wavs.

Recovery:
- For training, verify `F0_path`, `ASR_config`, `ASR_path`, and `PLBERT_dir` with the data/config inspector.
- For pretrained inference, read [../sub-skills/inference/references/model-assets.md](../sub-skills/inference/references/model-assets.md) and run the inference asset checker.

## Phonemizer / espeak failures

Symptoms:
- `phonemizer.backend.EspeakBackend` cannot be constructed.
- `espeak-ng` or `espeak` is missing from `PATH`.
- NLTK `word_tokenize` raises a missing-data `LookupError`.

Recovery:
- Install Python `phonemizer`.
- Provide an `espeak-ng` or `espeak` host binary.
- Provide the NLTK tokenizer data needed by `word_tokenize`.
- Re-run the inference checker with `--check-phonemizer`.

## WavLM / Transformers cache issues

Symptoms:
- Training fails in `AutoModel.from_pretrained`.
- First real run stalls on model download.
- Offline runs cannot fetch `microsoft/wavlm-base-plus`.

Recovery:
- Allow network for the first real training run, or pre-populate the Transformers cache.
- Use standard Hugging Face/Transformers cache environment variables outside this skill if needed.
- Do not edit StyleTTS2 model code before confirming cache/download state.

## Need workflow-specific recovery

- Data/list/config failures: [data-and-config troubleshooting](../sub-skills/data-and-config/references/troubleshooting.md).
- Training launch, checkpoint, OOM, NaN, DDP, or CUDA failures: [training troubleshooting](../sub-skills/training/references/troubleshooting.md).
- Pretrained inference, reference audio, phonemizer, CPU/CUDA, and voice-permission failures: [inference troubleshooting](../sub-skills/inference/references/troubleshooting.md).
