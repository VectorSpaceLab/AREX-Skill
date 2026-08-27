# ESPnet Installation and Diagnostics Matrix

## Public install paths

ESPnet's package metadata requires Python 3.10 or newer. For package users, start with the narrowest install that matches the task:

```bash
python -m pip install espnet
python -c "import espnet2, espnet3; print('ESPnet imports ok')"
```

For a source checkout used for development or recipe work, install editable mode with one or more focused extras:

```bash
python -m pip install -e ".[asr]"      # ASR and recognition-oriented extras
python -m pip install -e ".[tts]"      # TTS, TTS2, SVS frontends and G2P helpers
python -m pip install -e ".[enh]"      # Enhancement/separation metrics
python -m pip install -e ".[spk]"      # Speaker task dependency surface
python -m pip install -e ".[speechlm]" # SpeechLM/distributed-oriented extras
python -m pip install -e ".[egs2]"     # Recipe helper surface
```

Avoid `.[all]`, `.[dev]`, `.[test]`, and `.[doc]` unless the user explicitly needs broad lab, contributor, CI, or documentation workflows. These groups substantially widen the dependency and optional-kernel surface.

## Extras and common failure modes

| Extra or package area | Use when | Important notes |
| --- | --- | --- |
| `asr`, `asr2` | ASR, ASR2, language-model assisted recognition, CTC segmentation | `ctc-segmentation` is installed from a pinned Git URL; use a network-capable build environment. |
| `tts` | TTS, TTS2, SVS, text frontend, G2P, pitch extraction | `pyworld`, `jaconv`, `jamo`, and `pypinyin` are common parser/import needs. Some G2P packages are source/Git installs. |
| `enh` | Enhancement/separation training, evaluation metrics | `ci_sdr` and `fast-bss-eval` support metric-heavy paths. |
| `spk` | Speaker embeddings/classification/verification | Includes `asteroid_filterbanks`. |
| `egs2` | Recipe utilities beyond base package use | Pulls dataset/download/scoring/helper packages; still does not supply all external shell tools. |
| `speechlm` | SpeechLM, self-supervised, distributed speech language modeling | Linux-only `torchtitan` and `liger-kernel` may be GPU/CUDA-oriented. |
| `dev`, `test`, `doc` | Maintaining ESPnet source, running CI, building docs | Not needed for normal package use. |

## Host tools

ESPnet recipes and utilities can require shell tools that are not Python packages. Treat missing tools as workflow-specific diagnostics, not universal installation failure.

| Tool | Typical owner | Why it matters |
| --- | --- | --- |
| `sox`, `ffmpeg`, `flac` | recipes/data | Audio conversion, pipe entries in `wav.scp`, compressed audio handling. |
| `sph2pipe` | recipes/data | NIST Sphere corpus decoding through command pipes. |
| `spm_train`, `spm_encode`, `spm_decode` | tokenization | SentencePiece BPE training and encoding. |
| `sclite`, `PESQ`, `BeamformIt` | scoring/enhancement | Optional scoring and beamforming workflows. |
| `cmake` | compiled optional packages | Needed by some extensions, installers, or wheels built from source. |

## Backend policy

- CPU import/parser checks are enough for installation guidance, data validation, CLI help, config inspection, and many synthetic usability checks.
- CUDA claims require `torch.cuda.is_available()`, matching CUDA runtime, and a tiny tensor allocation or the selected native case on actual GPU.
- Distributed/NCCL claims require PyTorch distributed/NCCL availability plus a workflow-specific run plan; a CUDA import alone is not distributed verification.
- FlashAttention, k2, S3PRL, Whisper, Longformer, RawNet, and many G2P paths are optional specialized routes. Install them only when the selected config/API uses them.
- Full recipe training, model downloads, demos, uploads, and benchmark runs require explicit user approval.

## Recommended diagnostic order

1. Run the bundled checker for base imports:
   ```bash
   python sub-skills/installation-and-diagnostics/scripts/check_espnet_environment.py --groups base torch --json
   ```
2. Add focused groups that match the user workflow, e.g. `--groups base tts torch`.
3. If the workflow is CUDA-specific, add `--require-cuda --strict` and verify a tiny torch allocation before claiming GPU readiness.
4. If `pip check` reports conflicts, avoid repairing a user-owned environment without approval; prefer a fresh environment or a minimal extra install.
