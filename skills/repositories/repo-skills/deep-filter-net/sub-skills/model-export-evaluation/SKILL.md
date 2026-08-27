---
name: model-export-evaluation
description: "Operate DeepFilterNet ONNX export, exported-artifact validation,
  model inspection, and objective/DNSMOS evaluation workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# DeepFilterNet model export and evaluation

Use this sub-skill when the task is to export a DeepFilterNet model to ONNX, inspect a model summary, validate a completed export directory, or run objective speech-enhancement evaluation such as VoiceBank-DEMAND, DNS2020, or DNSMOS.

## Route first

- For basic model loading, Python enhancement, audio I/O, or `deepFilter`/`deep-filter-py` usage, use [python-enhancement](../python-enhancement/SKILL.md).
- For HDF5 dataset creation, training-data configuration, or training input generation, use [training-data](../training-data/SKILL.md).
- For Rust binaries, model archives used by realtime runtimes, LADSPA, PipeWire, or deployment to live audio paths, use [rust-realtime-deployment](../rust-realtime-deployment/SKILL.md).

## Required starting facts

Before acting, identify:

1. The installed DeepFilterNet environment to run package modules in.
2. The model selector: a pretrained model name or a local model directory containing a checkpoint and `config.ini`.
3. The requested action: export, export validation, summary/inspection, benchmark evaluation, or DNSMOS.
4. Whether optional network access, benchmark datasets, DNSMOS API credentials, and metric dependencies are available.

If these facts are missing, ask for them or stop with the smallest explicit prerequisite list. Do not silently download models, benchmark datasets, or DNSMOS assets unless the user has allowed network access for this task.

## Core references

- Export, artifact, model-summary, and evaluation commands: [references/export-and-evaluation.md](references/export-and-evaluation.md)
- Failure diagnosis and stop/route decisions: [references/troubleshooting.md](references/troubleshooting.md)
- Export directory validator: [scripts/check_export_artifacts.py](scripts/check_export_artifacts.py)

## Fast operating patterns

### Validate a completed export directory

From this sub-skill directory:

```bash
python scripts/check_export_artifacts.py /path/to/export-dir
python scripts/check_export_artifacts.py /path/to/export-dir --check-npz
```

Use the first command for the deployable ONNX/config/version core. Use `--check-npz` when the debug/reference NPZ files should also be present and readable.

### Export a model to ONNX

```bash
python -m df.scripts.export --model-base-dir /path/to/model-dir --epoch best /path/to/export-dir
```

Add `--no-check` only when ONNX Runtime parity checking is intentionally skipped. Add `--simplify` only when `onnxsim` is installed and simplification is desired. See the reference before changing `--opset`.

### Inspect model structure before export/evaluation

```bash
python -m df.scripts.model_summary --model-base-dir /path/to/model-dir --type table
python -m df.scripts.model_summary --model-base-dir /path/to/model-dir --type torch
```

Use summaries to confirm that the intended checkpoint/model family loaded. If model loading fails, route to [python-enhancement](../python-enhancement/SKILL.md) before continuing here.

### Run benchmark evaluation

Use benchmark scripts only after the dataset layout and optional metric dependencies are present. VoiceBank-DEMAND and DNS2020 use paired clean/noisy references; DNSMOS uses noisy/enhanced clips and may require local ONNX downloads or API credentials. Command shapes and skip conditions are in [references/export-and-evaluation.md](references/export-and-evaluation.md).

## Stop conditions

Stop and report rather than guessing when:

- `config.ini`, `version.txt`, `enc.onnx`, `erb_dec.onnx`, or `df_dec.onnx` is missing from an export intended for deployment.
- `--check-npz` validation fails for generated `*_input.npz` or `*_output.npz` files.
- `onnx`, `onnxruntime`, `MonkeyType`, or `onnxsim` is missing for a requested export/check/simplify mode.
- A benchmark dataset does not match the documented directory layout.
- DNSMOS needs network downloads or `DNS_AUTH_KEY`/`--api-key`, but those are unavailable or unauthorized.
