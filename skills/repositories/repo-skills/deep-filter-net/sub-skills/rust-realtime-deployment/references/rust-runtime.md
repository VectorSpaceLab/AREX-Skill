# Rust Runtime Reference

This reference covers the native Rust `deep-filter` path: binary usage, model archive expectations, Cargo feature planning, tract runtime notes, WASM build shape, and source-build limitations. For Python/PyTorch enhancement, use the sibling Python enhancement sub-skill instead.

## 1. Choose A Runtime Path

| User goal | Recommended path | Stop if |
|---|---|---|
| Enhance one or more WAV files without Python | Use an existing `deep-filter` binary first; build from source only if requested. | No binary, no source tree, or no model/default model. |
| Build `deep-filter` from source | Verify Rust/Cargo first, then run the Cargo recipe below in the user's source tree. | `cargo`/`rustc` missing, Rust < 1.70, network-disabled crate download, or user disallows source build. |
| Use GPU/PyTorch | Route away from Rust; Rust binary uses the tract/ONNX path, not PyTorch/CUDA. | User expects CUDA speedups from `deep-filter`. |
| Validate exported ONNX with tract | Use this file only for the command shape; route export/artifact validation to model-export-evaluation. | Missing exported `enc.onnx`/`erb_dec.onnx`/`df_dec.onnx` and NPZ bundles. |
| Build WASM | Treat as source-build only with `wasm-pack`; not a general Python/package install. | No source crate, no `wasm-pack`, or no JS/WASM deployment target. |

## 2. `deep-filter` Binary Usage

The Rust binary suppresses noise in WAV audio files. The README documents 48 kHz WAV support; the source runtime can resample around the model sample rate, but operational guidance should still prefer 48 kHz WAV input because that is the documented support boundary.

Published command shape:

```bash
deep-filter [OPTIONS] [FILES]...
```

Common examples:

```bash
# Use the binary's compiled-in default model when available.
deep-filter --out-dir enhanced noisy_48k.wav

# Use an explicit tract/ONNX model archive and compensate algorithmic delay.
deep-filter --model /path/to/DeepFilterNet2_onnx.tar.gz --out-dir enhanced --pf --compensate-delay noisy_48k.wav

# Multi-channel input with a less aggressive attenuation cap.
deep-filter --model /path/to/DeepFilterNet3_ll_onnx.tar.gz --atten-lim-db 24 --reduce-mask 2 noisy_multichannel_48k.wav
```

### Binary Flags

README-published flags:

| Flag | Meaning | Notes |
|---|---|---|
| `<FILES>...` | Input WAV files. | Output files keep the input basenames in the output directory. |
| `-m`, `--model <MODEL>` | Path to a model `.tar.gz`. | If omitted, a binary compiled with a default model uses that built-in model. README says the precompiled default is DeepFilterNet2. |
| `-o`, `--out-dir <OUT_DIR>` | Output directory. | Default: `out`; the binary creates it if needed. |
| `--pf` | Enable post-filter. | Slightly over-attenuates very noisy sections. |
| `-D`, `--compensate-delay` | Compensate STFT/model lookahead delay. | Useful when waveform alignment matters. |
| `-v`, `--verbose` | Increase logging verbosity. | Repeating `-v` raises library and tract logging detail. |
| `-h`, `--help` | Print help. | Use this to verify the installed binary before running audio. |
| `-V`, `--version` | Print version. | Useful for provenance/debugging. |

Additional source-parser controls visible in the Rust binary implementation:

| Flag | Default | Meaning |
|---|---:|---|
| `--pf-beta <FLOAT>` | `0.02` | Post-filter beta; higher means stronger post-filtering. |
| `-a`, `--atten-lim-db <DB>` | `100` | Attenuation limit in dB. `0` means no noise reduction; `100` means no attenuation limit/full reduction. |
| `--min-db-thresh <DB>` | `-15` | Minimum local SNR threshold for running decoder processing. |
| `--max-db-erb-thresh <DB>` | `35` | Maximum local SNR threshold for ERB decoder processing. |
| `--max-db-df-thresh <DB>` | `35` | Maximum local SNR threshold for DF decoder processing. |
| `--reduce-mask <1-or-2>` | `1` | For multiple channels, reduce masks with max (`1`) or mean (`2`). |

Validation checks before running audio:

```bash
command -v deep-filter
deep-filter --help
test -r /path/to/noisy_48k.wav
# If not using a compiled-in default model:
test -r /path/to/DeepFilterNet2_onnx.tar.gz
```

## 3. Model Archive Expectations

Do not copy model archives or binaries into the skill tree. Ask the user to provide or download release assets into their own workspace/cache.

The Rust `--model` argument expects a model archive path ending in `.tar.gz`. Use ONNX/tract archives for the Rust binary; Python `.zip` archives are not interchangeable with the Rust `--model` path.

Distilled model archive names from the source distribution:

| Archive name | Expected role |
|---|---|
| `DeepFilterNet.zip` | Python/pretrained model archive; route Python use to the Python enhancement sub-skill. |
| `DeepFilterNet2.zip` | Python/pretrained model archive; route Python use to the Python enhancement sub-skill. |
| `DeepFilterNet3.zip` | Python/pretrained model archive; route Python use to the Python enhancement sub-skill. |
| `DeepFilterNet2_onnx.tar.gz` | Rust/tract model archive candidate for `deep-filter --model`. |
| `DeepFilterNet2_onnx_ll.tar.gz` | Rust/tract low-latency archive candidate. |
| `DeepFilterNet3_onnx.tar.gz` | Rust/tract model archive candidate for DeepFilterNet3. |
| `DeepFilterNet3_ll_onnx.tar.gz` | Rust/tract low-latency DeepFilterNet3 archive candidate. |

Stop and ask for a correct archive when:

- The user supplies a `.zip` for `deep-filter --model`.
- The path is unreadable or not a file.
- The binary reports that it was compiled without a default model and no `--model` was supplied.
- A model path opens but the binary reports missing config/model members; this usually means the archive type does not match the Rust/tract runtime.

## 4. Cargo Build Planning

Only run these commands when the user wants a source build and has provided a source tree or release source archive. This skill does not claim that the build has already been executed or verified.

Preflight:

```bash
command -v cargo
command -v rustc
rustc --version
cargo --version
```

The Rust package declares `rust-version = 1.70`. If `rustc --version` is older than 1.70, stop and ask whether to install/update Rust (usually through rustup) or use a release binary instead.

Build the `deep-filter` binary with the required feature set:

```bash
# From the root of a user-provided DeepFilterNet source tree.
cargo build --release -p deep_filter --bin deep-filter --features bin,tract,wav-utils,transforms

# Result, on typical Linux builds:
./target/release/deep-filter --help
```

If you intentionally disable default features, choose whether a model is compiled in:

```bash
# No compiled-in model; users must pass --model <archive.tar.gz> at runtime.
cargo build --release -p deep_filter --bin deep-filter \
  --no-default-features --features bin,tract,wav-utils,transforms

# Low-latency compiled-in model feature; users may omit --model if the build succeeds.
cargo build --release -p deep_filter --bin deep-filter \
  --no-default-features --features bin,tract,wav-utils,transforms,default-model-ll
```

Relevant libDF feature facts:

| Feature | Purpose |
|---|---|
| `default` | Includes `default-model`, `vorbis`, and `flac`. |
| `bin` | Enables CLI dependencies such as `clap`, `env_logger`, `ctrlc`, and logging. |
| `wav-utils` | Enables WAV read/write support. |
| `transforms` | Enables transforms/resampling support. |
| `tract` | Enables the tract ONNX runtime path (`tract-core`, `tract-onnx`, `tract-pulse`, `tract-hir`) and tar/gzip model archive handling. |
| `default-model` | Compiles in the default model asset. |
| `default-model-ll` | Compiles in a low-latency default model asset. |
| `capi` | Builds C API-oriented library features. |
| `wasm` | Enables tract plus `wasm-bindgen`, JS random support, panic hook, and JS interop dependencies. |

Build troubleshooting is in [troubleshooting.md](troubleshooting.md).

## 5. Tract Runtime And Exported Model Checks

The Rust runtime uses the tract/ONNX path. A full tract numeric check requires a completed export directory containing files such as:

- `enc.onnx`, `erb_dec.onnx`, `df_dec.onnx`
- `config.ini`
- `enc_input.npz`, `enc_output.npz`, `erb_dec_input.npz`, `erb_dec_output.npz`, `df_dec_input.npz`, `df_dec_output.npz`

A full tract smoke workflow exercises the encoder, ERB decoder, and DF decoder with and without pulse and compares output bundles. This sub-skill does not bundle that workflow because it depends on export artifacts plus auxiliary NPZ comparison/splitting utilities. Use the model-export-evaluation sub-skill to create or validate export artifacts first.

If the user already has tract CLI and a complete export directory, the command shape is:

```bash
tract -v -O --onnx-ignore-output-shapes /path/to/export/enc.onnx run \
  --io-long --steps \
  --input-from-bundle /path/to/export/enc_input.npz \
  --assert-output-bundle /path/to/export/enc_output.npz
```

Stop if any export artifact is missing, if `tract` is not installed, or if the user is actually asking how to export ONNX models rather than how the Rust runtime consumes them.

## 6. WASM Build Notes

The WASM package build shape is:

```bash
# From the libDF crate directory inside a user-provided source tree.
wasm-pack build --target no-modules --features wasm
```

Preflight:

```bash
command -v wasm-pack
command -v cargo
```

The WASM feature set is source-build and packaging oriented. It is not required for ordinary `deep-filter` binary use, LADSPA/PipeWire setup, Python enhancement, training, or evaluation. Stop if there is no source tree, no `wasm-pack`, or no browser/JS deployment target; do not run the WASM build just to enhance audio locally.

## 7. Source-Build Limitations

- Rust/Cargo builds are optional in this generated skill's verified scope. Do not state that `deep-filter`, LADSPA, demo, tract, or WASM builds have been verified unless you actually run them for the user.
- Building may download crates and compile native dependencies; respect network and time budgets.
- Rust 1.70+ is expected for the package; the demo UI uses nightly in the documented command.
- The Rust binary is CPU/system-runtime oriented. Do not promise CUDA/GPU acceleration through `deep-filter`; route to Python/PyTorch for GPU alternatives.
- If source build fails because Cargo/Rust is absent, diagnose the missing toolchain first and ask whether to install Rust or use a release binary.
