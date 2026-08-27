# Realtime Audio Reference

This reference covers the DeepFilterNet LADSPA plugin, PipeWire virtual microphone/source and stereo sink setup, realtime latency/attenuation behavior, and the Linux demo/UI path. It is intentionally self-contained; use the bundled templates and checker rather than reopening source configs.

## 1. LADSPA Plugin Build Or Install

The LADSPA plugin provides realtime DeepFilterNet noise suppression for LADSPA hosts such as PipeWire filter-chain. It uses a model variant without lookahead; the documented minimum latency is 20 ms for STFT processing plus additional host/PipeWire latency.

Preferred operational order:

1. Use a release-built LADSPA plugin when available. Look for a shared library named like `libdeep_filter_ladspa.so` on Linux.
2. If the user explicitly wants a source build, verify Rust first and build in their DeepFilterNet source tree:

```bash
command -v cargo
command -v rustc
cargo build --release -p deep-filter-ladspa
ls target/release/libdeep_filter_ladspa*
```

The plugin initializes a compiled/default DeepFilter runtime. PipeWire configs do not take a model archive path; they point only to the LADSPA shared library and plugin label.

Stop if Cargo/Rust is absent, the user has no source tree/release source archive, or the user only needs Python/GPU enhancement.

## 2. Bundled PipeWire Templates

This sub-skill bundles adapted, self-contained templates:

- `../scripts/deepfilter-mono-source.conf`: virtual mono microphone/source for VoIP capture.
- `../scripts/deepfilter-stereo-sink.conf`: virtual stereo sink for application playback denoising.
- `../scripts/check_pipewire_config.py`: read-only validator for edited templates.

Each template uses a realistic default plugin path, but users must edit the `plugin = ...` line to the actual absolute path of their `libdeep_filter_ladspa.so` when the plugin is installed elsewhere. Do not use `~`, `$HOME`, relative paths, or private checkout paths in PipeWire configs.

Important fields:

| Field | Mono source | Stereo sink | Required meaning |
|---|---|---|---|
| `plugin` | Absolute path to LADSPA `.so` | Absolute path to LADSPA `.so` | Must be absolute; existence can be checked with the bundled validator. |
| `label` | `deep_filter_mono` | `deep_filter_stereo` | Must match the LADSPA plugin descriptor. |
| `"Attenuation Limit (dB)"` | `0` to `100`, default `100` | `0` to `100`, default `100` | `0` means no noise reduction; `100` means no attenuation limit/full reduction. |
| `audio.rate` | `48000` | `48000` | DeepFilterNet realtime path is designed around 48 kHz processing. |
| `audio.position` | `[MONO]` | `[FL FR]` | Mono virtual mic vs stereo application sink. |
| `media.class` | `Audio/Source` in playback props | `Audio/Sink` in capture props | Determines whether apps see a virtual microphone or sink. |

The plugin also exposes additional controls if a user extends a template: `Post Filter Beta` range `0..0.05`, `Min processing threshold (dB)` range `-15..35`, `Max ERB processing threshold (dB)` range `-15..35`, `Max DF processing threshold (dB)` range `-15..35`, and `Min Processing Buffer (frames)` range `0..10`.

## 3. Validate A PipeWire Config Without Launching PipeWire

Use the checker before any service restart or one-off PipeWire launch:

```bash
# From this sub-skill directory, validate the bundled mono template.
python scripts/check_pipewire_config.py scripts/deepfilter-mono-source.conf \
  --expected-label deep_filter_mono

# Validate an edited user config and require that the LADSPA file exists.
python scripts/check_pipewire_config.py /path/to/deepfilter-mono-source.conf \
  --expected-label deep_filter_mono \
  --expected-plugin-path /opt/deepfilter/libdeep_filter_ladspa.so \
  --require-plugin-exists

# Validate the stereo sink template.
python scripts/check_pipewire_config.py scripts/deepfilter-stereo-sink.conf \
  --expected-label deep_filter_stereo
```

The checker verifies:

- Config file is readable.
- Every `plugin = ...` value is absolute and does not use shell expansion.
- Optional exact plugin path and file existence when requested.
- LADSPA label is `deep_filter_mono` or `deep_filter_stereo`, and optionally the expected one.
- `Attenuation Limit (dB)` is numeric and within `0..100`.
- `audio.rate` is `48000` unless the rate check is explicitly skipped.

The checker does not start PipeWire, load a plugin, change services, or touch system directories.

## 4. User-Level PipeWire Setup Pattern

For a virtual microphone/source:

```bash
mkdir -p ~/.config/pipewire/filter-chain.conf.d
cp scripts/deepfilter-mono-source.conf ~/.config/pipewire/filter-chain.conf.d/deepfilter-mono-source.conf
# Edit the copied file: set plugin = /absolute/path/to/libdeep_filter_ladspa.so
python scripts/check_pipewire_config.py ~/.config/pipewire/filter-chain.conf.d/deepfilter-mono-source.conf \
  --expected-label deep_filter_mono --require-plugin-exists
```

For a virtual stereo sink:

```bash
mkdir -p ~/.config/pipewire/filter-chain.conf.d
cp scripts/deepfilter-stereo-sink.conf ~/.config/pipewire/filter-chain.conf.d/deepfilter-stereo-sink.conf
# Edit the copied file: set plugin = /absolute/path/to/libdeep_filter_ladspa.so
python scripts/check_pipewire_config.py ~/.config/pipewire/filter-chain.conf.d/deepfilter-stereo-sink.conf \
  --expected-label deep_filter_stereo --require-plugin-exists
```

After validation, the user can load the config through their PipeWire setup. Depending on distro/session manager, this may require a user-service restart such as:

```bash
systemctl --user restart pipewire pipewire-pulse wireplumber
```

or a one-off filter-chain launch in an interactive audio session:

```bash
pipewire -c /path/to/filter-chain.conf
```

Do not run service restarts or one-off launches without explicit permission. A failed or stale config can break the user's live audio session.

## 5. Mono Source Behavior

The mono-source template creates a virtual microphone named `DeepFilter Noise Canceling Source`. It is meant for applications that select an input device, such as conferencing or VoIP tools.

Checklist:

1. LADSPA plugin exists at the absolute `plugin` path.
2. Config label is `deep_filter_mono`.
3. `audio.rate = 48000` and `audio.position = [MONO]`.
4. `capture.props.node.passive = true` and `playback.props.media.class = Audio/Source` remain present.
5. After loading PipeWire, select the DeepFilter source in the application.

## 6. Stereo Sink Behavior

The stereo-sink template creates a virtual output named `DeepFilter Noise Canceling Sink`. Applications send audio to this sink; the denoised output is played back to the default output device.

Checklist:

1. LADSPA plugin exists at the absolute `plugin` path.
2. Config label is `deep_filter_stereo`.
3. `audio.channels = 2` and `audio.position = [FL FR]`.
4. `capture.props.media.class = Audio/Sink` remains present.
5. After loading PipeWire, select the DeepFilter sink for the target application in the desktop audio mixer.

## 7. Attenuation And Latency Expectations

- `Attenuation Limit (dB)` range is `0..100`.
- `0` means no noise reduction; it is a useful diagnostic value when comparing dry vs processed audio.
- `6..12` gives little noise reduction, `18..24` gives medium reduction, and `100` means no attenuation cap/full reduction.
- Minimum plugin latency is documented as 20 ms STFT processing plus additional PipeWire/LADSPA host latency.
- If logs mention underruns or processing RTF >= 1, the plugin may increase processing latency. Reduce CPU load, try less aggressive processing thresholds if exposed, or increase buffer tolerance before blaming the model.

## 8. Demo/UI Prerequisites

The realtime demo is Linux-oriented and uses Rust, CPAL audio, and an optional Iced UI. The documented Ubuntu prerequisite packages are:

```bash
sudo apt -y install build-essential cmake libfontconfig1-dev libasound2-dev
```

Rust setup is through rustup, and the documented UI command uses nightly:

```bash
cargo +nightly run -p df-demo --features ui --bin df-demo --release
```

To pass a model archive to the UI binary when running through Cargo, put binary arguments after `--`:

```bash
cargo +nightly run -p df-demo --features ui --bin df-demo --release -- \
  --model /path/to/DeepFilterNet3_ll_onnx.tar.gz -v
```

The demo source also reads `DF_MODEL` for the model path and defines a command-line capture binary without UI controls:

```bash
DF_MODEL=/path/to/DeepFilterNet3_ll_onnx.tar.gz \
  cargo +nightly run -p df-demo --bin df-demo-c --release
```

Stop and diagnose instead of retrying when:

- No default input/output device exists.
- The session has no working PipeWire/ALSA/desktop audio stack.
- A GUI session or font/audio development libraries are missing.
- `cargo +nightly` reports that nightly is not installed.
- The user has not approved installing system packages or changing audio services.
