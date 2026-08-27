# DeepFilterNet Troubleshooting

## Start with route selection

1. Python package import, `deepFilter`, audio file enhancement, or `libdf`: use [python-enhancement](../sub-skills/python-enhancement/SKILL.md).
2. HDF5 data, `dataset.cfg`, training launch, checkpoints, or batch-size configs: use [training-data](../sub-skills/training-data/SKILL.md).
3. ONNX export, model-summary, objective metrics, DNSMOS, VoiceBank, or DNS2020: use [model-export-evaluation](../sub-skills/model-export-evaluation/SKILL.md).
4. Rust `deep-filter`, LADSPA, PipeWire, realtime audio, model archives, or demo UI: use [rust-realtime-deployment](../sub-skills/rust-realtime-deployment/SKILL.md).

## Safe first checks

From the generated skill directory:

```bash
python scripts/check_deepfilternet_install.py
```

If it fails, fix required imports or CLI entry points before running enhancement, training, export, or realtime workflows.

For workflow-specific checks:

```bash
python sub-skills/python-enhancement/scripts/libdf_smoke.py
python sub-skills/training-data/scripts/validate_dataset_config.py --config dataset.cfg --data-dir data --require-files
python sub-skills/model-export-evaluation/scripts/check_export_artifacts.py /path/to/export-dir
python sub-skills/rust-realtime-deployment/scripts/check_pipewire_config.py /path/to/filter-chain.conf
```

## Common failure surfaces

| Symptom | Likely cause | Next action |
|---|---|---|
| `ModuleNotFoundError: df` | DeepFilterNet main package is not installed in the active environment | Install `deepfilternet` into the environment used by the command. |
| `ModuleNotFoundError: libdf` | Rust-backed `deepfilterlib` wheel/source extension missing or built for a different Python | Reinstall `deepfilterlib`/`deepfilternet`; verify with the root checker or `libdf_smoke.py`. |
| `ModuleNotFoundError: libdfdata` during training | Training extra/dataloader extension missing | Install `deepfilternet[train]` or a compatible `deepfilterdataloader`; read the training-data troubleshooting reference. |
| `torch.cuda.is_available()` differs from expectation | CPU PyTorch wheel, missing GPU passthrough, driver/wheel mismatch, or config chooses CPU/GPU automatically | Decide whether CUDA is required; run a PyTorch CUDA smoke if claiming GPU support; otherwise force CPU for debugging. |
| Default model load tries to download | Pretrained model name selected and cache is missing | Use a local model directory or explicitly approve network access. The Python helper is no-network by default. |
| `config.ini` or checkpoint not found | Model directory is incomplete or wrong epoch selected | Ensure the model directory has `config.ini` and a `checkpoints/` directory; use `--epoch best`, `latest`, an integer, or `none` deliberately. |
| Audio load/save fails | Unsupported codec/backend, wrong path, permissions, or malformed WAV | Validate with torchaudio, convert to a standard WAV, and check the Python enhancement troubleshooting reference. |
| Dataset validator reports missing splits/files | `dataset.cfg` schema or `--data-dir` is wrong | Fix `train`/`valid`/`test` entries before running data conversion or training. |
| ONNX export fails on missing `onnx`/`onnxruntime`/`onnxsim` | Export extras not installed | Install only export deps needed for the requested export/check mode. |
| DNSMOS fails on key/download/model | API credentials, network, or ONNX assets unavailable | Stop for approval/credentials or choose local metrics that do not require those resources. |
| LADSPA plugin not found | PipeWire config points to a non-existent or non-absolute `.so` path | Edit bundled template with an absolute plugin path and validate with `check_pipewire_config.py`. |
| Cargo build requested but `cargo` is absent | Rust toolchain missing | Ask before installing Rust/system packages or recommend a release binary if source build is not required. |

## Do not hide these limitations

- CPU checks do not verify CUDA acceleration or throughput.
- CLI `--help` does not verify model checkpoints or audio quality.
- HDF5 config validation does not run a full training epoch.
- Export artifact validation does not run ONNX Runtime parity unless the export workflow has already produced artifacts and optional deps are installed.
- PipeWire config validation does not load the LADSPA plugin or restart audio services.

When any limitation matters to the user's task, state it explicitly and either run the required native check with approval or ask for the missing model/data/system dependency.
