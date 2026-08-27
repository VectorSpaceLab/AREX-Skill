# Rust Realtime Troubleshooting

Use this guide when a native Rust, LADSPA, PipeWire, demo, tract, or WASM deployment request fails. Do not switch to Python unless the failure is really a Python/PyTorch/GPU task; route those cases to the sibling Python enhancement sub-skill.

## Fast Triage

1. Identify the failing surface: `deep-filter` binary, Cargo build, model archive, LADSPA `.so`, PipeWire config/service, demo/UI, tract, or WASM.
2. Collect exact command, stderr, OS, and whether the user authorized installation or service changes.
3. Run read-only checks first: `command -v`, `--help`, `test -r`, and `scripts/check_pipewire_config.py` for PipeWire configs.
4. Stop before host-level mutations: package installs, rustup changes, `/etc` writes, PipeWire restarts, or live audio launches require explicit user approval.

## Missing Cargo, Rustc, Or Nightly

Symptoms:

- `cargo: command not found`
- `rustc: command not found`
- `rustc` version older than `1.70`
- `error: toolchain 'nightly' is not installed`
- `cargo +nightly ...` fails before compiling the demo

Diagnosis:

```bash
command -v cargo || true
command -v rustc || true
rustc --version || true
cargo --version || true
rustup toolchain list || true
```

Action:

- For the Rust binary or LADSPA plugin, Rust 1.70+ is expected.
- For the demo UI command, nightly is used in the documented recipe.
- If toolchain installation is not authorized, stop and recommend a release binary/plugin instead of pretending the build can proceed.
- If toolchain installation is authorized, prefer rustup-managed installation or update; then re-run `cargo --version` and `rustc --version` before building.

## Rust Build Fails

Common causes and responses:

| Symptom | Likely cause | Response |
|---|---|---|
| `target package ... not found` | Command is not being run in a compatible DeepFilterNet source tree. | Ask for the correct source tree or use release artifacts. |
| `the package requires rustc 1.70` | Rust compiler too old. | Update Rust or stop. |
| Feature-related `deep-filter` binary not built | Required features missing. | Use `--features bin,tract,wav-utils,transforms`; if `--no-default-features`, decide whether to add `default-model`/`default-model-ll` or pass `--model` at runtime. |
| Crate download/network failure | Cargo registry or git dependency unavailable. | Respect network budget; retry only if authorized. |
| Long compile time | Source build is expensive. | Confirm the user still wants source build; release binary may be better. |

Do not claim build verification unless the specific Cargo command completed successfully in the user's environment.

## `deep-filter` Runtime Or Model Archive Fails

Symptoms:

- `deep-filter was not compiled with a default model`
- `Error opening model ...`
- Model path is a `.zip` or missing file
- Output directory empty or no enhanced WAV appears
- User expects CUDA/GPU acceleration

Checks:

```bash
deep-filter --help
test -r /path/to/input.wav
# If using --model:
test -r /path/to/model.tar.gz
```

Responses:

- Use `--model /absolute/or/user/path/to/*_onnx*.tar.gz` for Rust/tract archives.
- Do not pass Python `.zip` model archives to the Rust binary.
- If no default model is compiled in, `--model` is required.
- Prefer 48 kHz WAV input because that is the documented binary support boundary.
- Output defaults to `out/` unless `--out-dir` is set; the binary writes output WAVs using input basenames.
- GPU/PyTorch requests belong to Python enhancement, not the Rust binary.

## Missing LADSPA `.so`

Symptoms:

- PipeWire cannot load LADSPA plugin.
- `libdeep_filter_ladspa.so` is missing.
- Validator with `--require-plugin-exists` reports a missing file.

Checks:

```bash
find /usr/lib /usr/local/lib "$HOME/.ladspa" -name 'libdeep_filter_ladspa*' 2>/dev/null | head
python scripts/check_pipewire_config.py /path/to/deepfilter.conf --expected-label deep_filter_mono --require-plugin-exists
```

Responses:

- If a release plugin is available, point `plugin = ...` to its absolute path.
- If source build is requested, build with `cargo build --release -p deep-filter-ladspa` only after Cargo/Rust checks pass.
- Do not use `~`, `$HOME`, or relative plugin paths inside the PipeWire config.

## Non-Absolute Or Wrong Plugin Path

Symptoms:

- Validator error: `plugin path is not absolute`.
- PipeWire logs show plugin load failure even though the file exists.

Fix:

```text
plugin = /absolute/path/to/libdeep_filter_ladspa.so
```

Rules:

- Absolute path only.
- No `~` or environment variables.
- If installed under a user home directory, expand it manually before writing the config.
- Re-run `scripts/check_pipewire_config.py` after editing.

## PipeWire Config Location Or Service Issues

Symptoms:

- No `DeepFilter Noise Canceling Source` appears.
- No `DeepFilter Noise Canceling Sink` appears.
- `pipewire -c ...` exits immediately.
- Restarting audio services drops existing audio devices.

Checks:

```bash
command -v pipewire || true
systemctl --user status pipewire pipewire-pulse wireplumber --no-pager || true
python scripts/check_pipewire_config.py /path/to/deepfilter.conf --expected-label deep_filter_mono
```

Responses:

- User-level configs usually go under `~/.config/pipewire/filter-chain.conf.d/`; system-level configs under `/etc/pipewire/filter-chain.conf.d/` require elevated privileges and explicit approval.
- Some sessions need a user-service restart (`pipewire`, `pipewire-pulse`, and/or `wireplumber`) before new filter-chain configs are visible.
- A one-off launch `pipewire -c /path/to/filter-chain.conf` should only be done in an interactive audio session and after validation.
- If the desktop audio stack is not PipeWire-based, stop and ask whether the user wants PipeWire setup help; do not assume PulseAudio/JACK equivalence.

## Attenuation And Latency Surprise

Symptoms:

- Too much residual noise.
- Speech sounds overprocessed.
- User expects zero latency.
- Logs mention underruns or processing too slow.

Facts:

- `Attenuation Limit (dB)` range is `0..100`.
- `0` means no noise reduction.
- `6..12` is light reduction; `18..24` is medium; `100` means no attenuation cap/full reduction.
- LADSPA minimum latency is 20 ms STFT processing plus host/PipeWire latency.
- Runtime can increase latency if processing RTF is too high.

Responses:

- Use a smaller attenuation limit for less aggressive noise suppression.
- If underruns occur, reduce CPU load, close other realtime work, increase buffer tolerance if a template exposes it, or use a faster machine.
- Do not promise zero-latency realtime processing.

## Demo/UI Or Live Audio Device Fails

Symptoms:

- `no output device available` or no input device.
- ALSA/CPAL errors.
- UI/window/font errors.
- Build fails on font/audio system dependencies.

Checks:

```bash
command -v cargo
rustup toolchain list || true
# On Debian/Ubuntu-style systems, verify package names only if package queries are allowed.
```

Responses:

- The documented demo path is Linux-oriented.
- Ubuntu prerequisite packages are `build-essential`, `cmake`, `libfontconfig1-dev`, and `libasound2-dev`.
- The UI run command uses `cargo +nightly run -p df-demo --features ui --bin df-demo --release`.
- The demo needs working default audio input/output devices and, for UI, a GUI session.
- Ask before installing packages or changing audio services.

## Tract Or WASM Issues

Tract symptoms:

- `tract: command not found`
- Missing `enc.onnx`, `erb_dec.onnx`, `df_dec.onnx`, `config.ini`, or NPZ bundles
- Numeric comparison failures on exported artifacts

Response: route export/artifact validation to model-export-evaluation first. Only use tract commands after the export directory is complete and tract CLI is installed.

WASM symptoms:

- `wasm-pack: command not found`
- No source crate directory
- User expected a local audio binary but asked for WASM

Response: WASM is a source-build packaging path. Preflight `wasm-pack` and Cargo, confirm a JS/browser target, and stop if the user only wants local WAV enhancement or PipeWire deployment.

## When To Stop And Ask

Stop rather than guessing when:

- Toolchain or host packages must be installed.
- A live PipeWire restart or `/etc` write is needed.
- The user supplied a Python `.zip` model but asked for Rust `--model`.
- The plugin path is non-absolute or the `.so` is missing.
- Cargo is absent and the user asked for source build.
- The requested task is actually Python/GPU enhancement, training, export, or evaluation.
