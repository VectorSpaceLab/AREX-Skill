---
name: wenet
description: "Use WeNet for ASR package transcription, data preparation,
  training and decoding recipes, model export, and production runtime
  deployment."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# WeNet Repo Skill

Use this skill when the task involves WeNet, an end-to-end speech recognition
(ASR) toolkit with package transcription, staged training recipes, model export,
and production runtime deployment.

## Quick install/import check

For package transcription or API inspection, install WeNet in the target Python
environment and verify imports:

```bash
python - <<'PY'
import wenet
from wenet import load_model, load_feature, load_tokenizer
print("WeNet import OK")
PY
```

For broader workflow checks, run the bundled environment checker:

```bash
python scripts/check_wenet_environment.py --device cpu
```

Prefer `device=cpu` for safe diagnostics. CUDA, NPU, OpenVINO, IPEX, BPU, XPU,
mobile, and Triton/TensorRT paths require target-specific dependencies and
hardware.

## Route by task

| User task | Read |
|---|---|
| Transcribe one audio file with the installed `wenet` CLI/API; load a built-in or local model; validate a model directory; debug package import/backend selection. | [sub-skills/package-transcription/SKILL.md](sub-skills/package-transcription/SKILL.md) |
| Build or validate `wav.scp`, `text`, raw/shard `data.list`, dictionaries, tokenizer resources, CMVN inputs, or custom ASR data layout. | [sub-skills/data-preparation/SKILL.md](sub-skills/data-preparation/SKILL.md) |
| Adapt staged recipes; train/fine-tune; resume checkpoints; average models; run offline recognition; compare decoding modes; compute WER/CER; use LM/k2/context/LoRA paths. | [sub-skills/training-and-decoding/SKILL.md](sub-skills/training-and-decoding/SKILL.md) |
| Export a trained checkpoint/config to TorchScript/JIT, quantized JIT, ONNX CPU/GPU, IPEX, or Horizon BPU artifacts. | [sub-skills/model-export/SKILL.md](sub-skills/model-export/SKILL.md) |
| Choose and prepare production runtime deployment for libtorch, ONNX Runtime, OpenVINO, Android/iOS, web, Raspberry Pi, Triton/TensorRT, IPEX, BPU, or XPU. | [sub-skills/runtime-deployment/SKILL.md](sub-skills/runtime-deployment/SKILL.md) |

## Shared references and scripts

- Read [references/troubleshooting.md](references/troubleshooting.md) for
  cross-cutting installation, optional backend, artifact mismatch, network, and
  long-job issues.
- Read [references/repo-provenance.md](references/repo-provenance.md) before
  deciding whether this skill is current for a WeNet checkout.
- `references/repo-routing-metadata.json` contains structured router metadata
  for managed repo-skill importers.
- Run [scripts/check_wenet_environment.py](scripts/check_wenet_environment.py)
  to safely inspect package import and CPU/CUDA/NPU visibility.

## Operating rules

- Do not launch downloads, full training, shard packaging, CMVN over large
  corpora, runtime builds, or services until the user approves network,
  storage, hardware, port, and runtime cost.
- Keep model artifacts together: `train.yaml`, checkpoint, `units.txt`,
  tokenizer resources, optional `global_cmvn`, and export metadata must match.
- Use the bundled scripts for safe validation; use WeNet's installed package or
  module entry points for real workflows in the user's environment.
- When a workflow spans multiple stages, validate data first, then train/decode,
  then export, then deploy.
