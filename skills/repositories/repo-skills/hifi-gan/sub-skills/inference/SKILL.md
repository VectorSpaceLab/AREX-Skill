---
name: "inference"
description: "Routes HiFi-GAN wav-to-wav and mel-to-wav inference,
  checkpoint/config pairing, output naming, and smoke checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# HiFi-GAN Inference

Use this sub-skill when you need to synthesize waveforms with a trained HiFi-GAN generator.

## Use this route for

- Self-contained `scripts/infer_hifigan.py --mode wav` synthesis from a directory of input wavs.
- Self-contained `scripts/infer_hifigan.py --mode mel` synthesis from a directory of mel `.npy` files.
- Loading a generator checkpoint that sits beside its matching `config.json`.
- Choosing input and output directories and understanding generated filename suffixes.
- CPU/GPU selection, checkpoint/config mismatch recovery, and synthetic smoke checks.

## Do not use this route for

- Training, fine-tuning, or checkpoint creation/resume. Use the training sub-skill instead.
- Upstream text-to-mel generation. Prepare those mel files first, then return here.

## Read first

- [references/root-material.md](references/root-material.md)
- [references/workflows.md](references/workflows.md)
- [references/troubleshooting.md](references/troubleshooting.md)

## Bundled helpers

- [scripts/infer_hifigan.py](scripts/infer_hifigan.py) — self-contained wav/mel inference entrypoint using bundled HiFi-GAN runtime source.
- [scripts/make_dummy_checkpoint.py](scripts/make_dummy_checkpoint.py) — create a synthetic generator checkpoint from bundled source and copy or intentionally mismatch the paired `config.json`.
- [scripts/make_tiny_inference_fixtures.py](scripts/make_tiny_inference_fixtures.py) — create tiny wav and mel fixtures for smoke tests and negative cases.
- [scripts/run_inference_smoke.py](scripts/run_inference_smoke.py) — build the synthetic inputs and run both inference modes end to end.

## Key contracts

- `scripts/infer_hifigan.py` wraps the bundled `inference.py` and `inference_e2e.py`; both underlying paths read `config.json` from the checkpoint directory and do not accept a separate config flag.
- The checkpoint must be a generator checkpoint dict with a `generator` entry. Training checkpoints named `do_########` are not valid inference inputs.
- `scripts/infer_hifigan.py --mode wav` expects mono wav files, computes mels with the loaded config, and writes `<stem>_generated.wav`.
- `scripts/infer_hifigan.py --mode mel` expects mel `.npy` files and writes `<stem>_generated_e2e.wav`.
- Both scripts auto-select CUDA when `torch.cuda.is_available()` is true and fall back to CPU otherwise.
- The bundled inference entrypoint ultimately runs code that iterates `os.listdir(...)` directly, so keep the input directory clean and populated only with the intended files.
- Use the matching config family for the checkpoint. The skill bundles `config_v1.json`, `config_v2.json`, and `config_v3.json` under `../../scripts/hifigan_runtime/configs/`.

## Known-good inspection environment

- Verified inspection facts: `torch 2.3.1+cu121` imported on an NVIDIA A100-SXM4-40GB host; `torch.cuda.is_available()` returned true; `torch.cuda.get_device_name(0)` worked; `torch.utils.tensorboard` imported; `librosa.util.normalize` was present in `librosa 0.10.2.post1`.
