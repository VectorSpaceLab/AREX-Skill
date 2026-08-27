# DeepFilterNet export and evaluation reference

This reference is self-contained for operating an installed DeepFilterNet package. It covers ONNX export artifacts, model inspection, objective evaluation command shapes, DNSMOS prerequisites, metric dependencies, CSV outputs, and skip conditions.

## 1. ONNX export workflow

### Preconditions

- DeepFilterNet and its Rust-backed `deepfilterlib` Python package import successfully.
- The model selector is either a known pretrained model name or a local model directory with a checkpoint and `config.ini`.
- Export dependencies are installed for the requested mode:
  - always for export: `onnx`, `onnxruntime`, `MonkeyType`, `torch`, `numpy`;
  - additionally for `--simplify`: `onnxsim`.
- Network access is allowed if the model selector would trigger a pretrained model download. For no-network work, use an explicit local model directory.

### Command shapes

Basic export with default checking:

```bash
python -m df.scripts.export --model-base-dir /path/to/model-dir --epoch best /path/to/export-dir
```

Export a named/pretrained model only when downloads are allowed or already cached:

```bash
python -m df.scripts.export --model-base-dir DeepFilterNet3 /path/to/export-dir
```

Skip ONNX checker/ONNX Runtime parity checking when dependencies or numerical checks are intentionally deferred:

```bash
python -m df.scripts.export --model-base-dir /path/to/model-dir --no-check /path/to/export-dir
```

Simplify exported ONNX graphs and select an opset:

```bash
python -m df.scripts.export --model-base-dir /path/to/model-dir --simplify --opset 14 /path/to/export-dir
```

Inherited model arguments accepted by the export command include:

- `--model-base-dir` / `-m`: model directory or pretrained model name.
- `--pf`: enable the post-filter while loading the model for the export script's smoke enhancement pass.
- `--log-level` and `--debug`: logging verbosity.
- `--epoch` / `-e`: checkpoint epoch selector; commonly `best`, `latest`, or an integer.
- `--version`: print package version.
- `--output-dir` is inherited by the shared parser, but it is not the ONNX export target. The positional `export_dir` is the export target.

Export-specific arguments:

- positional `export_dir`: directory where ONNX/config/version/debug artifacts are written.
- `--no-check`: disables `onnx.checker` and ONNX Runtime output comparison.
- `--simplify`: runs `onnxsim` and overwrites each component with the simplified model when simplification validates.
- `--opset`: ONNX opset for `torch.onnx.export`; parser default is `12`. Raise this only for a consumer that requires it and can load it.

### Generated artifacts

A normal component export writes the following files:

| File | Required for deployment? | Meaning |
|---|---:|---|
| `enc.onnx` | yes | Encoder component. Inputs: `feat_erb`, `feat_spec`. Outputs include encoder skip tensors, `emb`, `c0`, and `lsnr`. |
| `erb_dec.onnx` | yes | ERB decoder component. Inputs: `emb`, `e3`, `e2`, `e1`, `e0`. Output: `m`. |
| `df_dec.onnx` | yes | Deep-filter decoder component. Inputs: `emb`, `c0`. Output: `coefs`. |
| `config.ini` | yes | Model/config parameters copied beside the exported components. |
| `version.txt` | yes | Export provenance string in the form `<model-name>_epoch_<epoch>`. |
| `<model-name>_onnx.tar.gz` | recommended | Archive containing only `enc.onnx`, `erb_dec.onnx`, `df_dec.onnx`, `config.ini`, and `version.txt`. |
| `enc_input.npz` | debug/reference | Compressed numpy inputs `feat_erb`, `feat_spec`. |
| `enc_output.npz` | debug/reference | Compressed numpy outputs `e0`, `e1`, `e2`, `e3`, `emb`, `c0`, `lsnr`. |
| `erb_dec_input.npz` | debug/reference | Compressed numpy inputs `emb`, `e0`, `e1`, `e2`, `e3`. |
| `erb_dec_output.npz` | debug/reference | Compressed numpy output `m`. |
| `df_dec_input.npz` | debug/reference | Compressed numpy inputs `emb`, `c0`. |
| `df_dec_output.npz` | debug/reference | Compressed numpy output `coefs`. |

The export API can also produce a full-model `deepfilternet2.onnx`, but the standard CLI path exports the three deployable components above.

### Completed export validation

From this sub-skill directory, validate a deployment-ready export:

```bash
python scripts/check_export_artifacts.py /path/to/export-dir
```

Strictly validate the debug/reference NPZ files too:

```bash
python scripts/check_export_artifacts.py /path/to/export-dir --check-npz
```

Optionally require a tar archive and emit machine-readable JSON:

```bash
python scripts/check_export_artifacts.py /path/to/export-dir --check-npz --require-tar --json
```

Treat missing `df_dec.onnx`, `version.txt`, or any other required core artifact as a hard failure. Treat missing NPZ files as a hard failure only when `--check-npz` is requested.

## 2. Model summary and inspection

Use model summaries when a user wants parameter structure, when export loaded an unexpected checkpoint, or before comparing model families.

```bash
python -m df.scripts.model_summary --model-base-dir /path/to/model-dir --type table
python -m df.scripts.model_summary --model-base-dir /path/to/model-dir --type torch
python -m df.scripts.model_summary --model-base-dir /path/to/model-dir --type ptflops
```

- `--type table` prints trainable leaf modules and parameter counts plus a sum.
- `--type torch` prints the PyTorch module tree.
- `--type ptflops` needs `ptflops` and logs a more detailed summary.

A simpler print-only path is also available:

```bash
python -m df.scripts.print_model /path/to/model-dir
```

Diagnostic plotting helpers are optional and require plotting/audio dependencies:

```bash
python -m df.scripts.plot_spec /path/to/audio.wav
python -m df.scripts.plot_summaries /path/to/summary-dir --snr 0 --save
```

Skip plotting on headless/minimal environments unless the user explicitly needs visual artifacts.

## 3. Objective evaluation workflows

### VoiceBank-DEMAND

Dataset layout:

```text
voicebank-root/
  clean_testset_wav/*.wav
  noisy_testset_wav/*.wav
```

Command shape:

```bash
python -m df.scripts.test_voicebank_demand \
  --model-base-dir /path/to/model-dir \
  --metric-workers 4 \
  --csv-path-enh results/voicebank_enhanced.csv \
  --output-dir results/enhanced_wavs \
  /path/to/voicebank-root
```

To also write noisy baseline metrics:

```bash
python -m df.scripts.test_voicebank_demand \
  --model-base-dir /path/to/model-dir \
  --metric-workers 4 \
  --compute-noisy-metric \
  --csv-path-enh results/voicebank_enhanced.csv \
  --csv-path-noisy results/voicebank_noisy.csv \
  /path/to/voicebank-root
```

Do not pass `--csv-path-noisy` without `--compute-noisy-metric`; the noisy metric table is empty unless noisy metric computation is enabled.

Metrics: STOI, composite speech metrics (`PESQ`, `CSIG`, `CBAK`, `COVL`, `SSNR`), and SI-SDR. Enhanced audio is optionally saved under `--output-dir` with the model suffix.

### DNS2020 clean/noisy reference evaluation

Dataset layout:

```text
dns2020-root/
  no_reverb/
    clean/*.wav
    noisy/*.wav
  with_reverb/          # optional, only used with --with-reverb
    clean/*.wav
    noisy/*.wav
```

Command shape:

```bash
python -m df.scripts.test_dns_2020 \
  --model-base-dir /path/to/model-dir \
  --metric-workers 4 \
  --output-dir results/dns2020_enhanced \
  /path/to/dns2020-root
```

Include the reverberant subset:

```bash
python -m df.scripts.test_dns_2020 \
  --model-base-dir /path/to/model-dir \
  --metric-workers 4 \
  --with-reverb \
  /path/to/dns2020-root
```

The DNS2020 script expects exactly 150 clean/noisy pairs per subset and derives clean filenames from noisy filenames. Stop on layout or count assertion failures instead of renaming files blindly.

### Noisy directory DNSMOS after enhancement

Dataset layout: one directory containing noisy `.wav` clips.

```bash
python -m df.scripts.test_noisy_dnsmos \
  --model-base-dir /path/to/model-dir \
  --metric-workers 4 \
  --csv-path-enh results/dnsmos_enhanced.csv \
  --output-dir results/dnsmos_enhanced_wavs \
  /path/to/noisy-wav-dir
```

The script enhances every noisy clip and computes DNSMOS v5-style scores for enhanced output. Expected enhanced CSV columns are `filename` plus DNSMOS names `SIG`, `BAK`, `OVRL`, and `P808_MOS`. In the current package command, `--csv-path-noisy` is parsed but noisy DNSMOS CSV is not produced because noisy scoring is disabled in that script path.

### Standalone DNSMOS commands

Local P.835-style DNSMOS for one file:

```bash
python -m df.scripts.dnsmos --method p835 /path/to/audio.wav
```

DNSMOS API scoring for one file:

```bash
DNS_AUTH_KEY=... python -m df.scripts.dnsmos --api --method p835 /path/to/audio.wav
python -m df.scripts.dnsmos --api --api-key "$DNS_AUTH_KEY" --method p808 /path/to/audio.wav
```

DNSMOS v5 sample, directory, and CSV-mean workflows:

```bash
python -m df.scripts.dnsmos_dns5 eval-sample /path/to/audio.wav
python -m df.scripts.dnsmos_dns5 eval-dir /path/to/wav-dir -o results/dnsmos_v5.csv --num-workers 4
python -m df.scripts.dnsmos_dns5 mean results/dnsmos_v5.csv
```

DNSMOS v5 directory CSVs include per-file metadata (`filename`, length, sample rate, hop count) plus raw and calibrated MOS columns (`SIG`, `BAK`, `OVRL`, `P808_MOS` and raw variants).

### HDF5 filtering by DNSMOS

Filtering HDF5 speech data by DNSMOS is a data-preparation/mutation workflow. If the user asks to create or filter training datasets, route to [training-data](../../training-data/SKILL.md). Only discuss it here as a dependency-heavy DNSMOS use case: it needs HDF5, audio decoding, local DNSMOS ONNX models, and explicit permission to write a filtered HDF5 output.

## 4. Dependency matrix

| Capability | Required packages/tools | External prerequisites | Typical outputs | Skip/stop when |
|---|---|---|---|---|
| ONNX export | `torch`, `numpy`, DeepFilterNet package, `deepfilterlib`, `onnx`, `onnxruntime`, `MonkeyType`; optional `onnxsim` | model checkpoint/config; optional cached/pretrained model | ONNX components, `config.ini`, `version.txt`, NPZ debug files, tar archive | export deps missing, model directory/config missing, network needed but unauthorized |
| Export validation | Python standard library; optional `numpy` for `--check-npz` | completed export directory | pass/fail report or JSON | required core files missing; NPZ requested but unreadable/missing |
| Model summary | DeepFilterNet package; optional `ptflops` for flops summary | model loads successfully | printed module tree/table/flops log | model loading fails; route to Python enhancement basics |
| VoiceBank/DNS2020 metrics | `pystoi`, `pesq`, `scipy`, `torch`, `torchaudio`, DeepFilterNet package | benchmark datasets with exact clean/noisy layout | logs; VoiceBank CSVs; optional enhanced wavs | metrics deps missing; dataset layout/count invalid |
| DNSMOS local/API | `onnxruntime`, `requests`; v5 additionally `librosa`, `pandas`, `soundfile`, `tqdm`; package import path may also require eval deps | local ONNX model downloads or preseeded cache; API needs `DNS_AUTH_KEY`/`--api-key` | MOS logs/CSVs; optional enhanced wavs | network/download/API key unavailable; DNSMOS model files missing |
| Plotting/visual diagnostics | `matplotlib`, `torchaudio`; some helpers need `icecream` | audio file or training summary directory | PDF plots | headless/minimal env or no explicit plot request |

## 5. CSV expectations

- `evaluation_loop` CSV format is `filename,<metric-1>,<metric-2>,...` with one row per processed file.
- VoiceBank enhanced CSV normally includes `STOI`, `PESQ`, `CSIG`, `CBAK`, `COVL`, `SSNR`, and `SISDR` columns.
- VoiceBank noisy CSV uses the same metric names, but only if noisy baseline metrics were computed.
- DNSMOS enhanced CSV from the noisy-directory workflow uses `SIG`, `BAK`, `OVRL`, and `P808_MOS`.
- DNSMOS v5 directory CSV is a pandas CSV and may include an index column plus file metadata and raw/calibrated MOS columns.
- The printed mean metric labels may include `Enhanced ...` or `Noisy ...`; per-file CSV headers use metric names without those prefixes.

## 6. Skip conditions and safe alternatives

- **No ONNX stack:** do not export; validate any already-created directory with `scripts/check_export_artifacts.py` instead.
- **No `MonkeyType`:** the export entry point stops before loading the model; install it or report the missing prerequisite.
- **No `onnxsim`:** run export without `--simplify`.
- **No model config/checkpoint:** route to [python-enhancement](../../python-enhancement/SKILL.md) to resolve model selection/loading.
- **No benchmark dataset:** do not synthesize benchmark claims; provide the expected layout and ask for the dataset.
- **No `pystoi`, `pesq`, or `scipy`:** do not run VoiceBank/DNS2020 objective metrics; install eval dependencies or skip metrics.
- **No DNSMOS network/cache/API key:** skip DNSMOS and report whether local model download or API credentials are the blocker.
- **Training dataset mutation requested:** route to [training-data](../../training-data/SKILL.md).
- **Realtime model archive/deployment requested:** route to [rust-realtime-deployment](../../rust-realtime-deployment/SKILL.md).
