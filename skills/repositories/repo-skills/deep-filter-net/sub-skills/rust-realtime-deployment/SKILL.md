---
name: rust-realtime-deployment
description: "Plan and troubleshoot DeepFilterNet Rust binaries, LADSPA/PipeWire
  realtime audio, model archives, and demo deployment."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Rust Realtime Deployment

Use this sub-skill when a DeepFilterNet task involves native Rust deployment rather than the Python package: the `deep-filter` WAV enhancement binary, Rust/Cargo build planning, model archives for the Rust/tract runtime, LADSPA plugin deployment, PipeWire virtual microphone/sink setup, or the Linux realtime demo.

## Route First

- Python enhancement CLI/API, PyTorch devices, CUDA/GPU alternatives, audio file loading through `df.enhance`, or Python model directories: use [python-enhancement](../python-enhancement/SKILL.md).
- HDF5 dataset preparation, training, checkpoint/base-dir behavior, or batch-size config edits: use [training-data](../training-data/SKILL.md).
- ONNX export, objective evaluation, DNSMOS, metric scripts, or completed export-directory validation: use [model-export-evaluation](../model-export-evaluation/SKILL.md).
- Stay here for native Rust `deep-filter`, `libDF`/Cargo feature planning, LADSPA/PipeWire realtime audio, tract/WASM runtime notes, and demo/UI prerequisites.

## Operating Map

1. For offline WAV enhancement with the Rust binary, read [references/rust-runtime.md](references/rust-runtime.md). Confirm the user has a compatible `deep-filter` binary or explicitly wants a source build; do not imply that Cargo builds have already been verified.
2. For model archive selection, use the archive expectations in [references/rust-runtime.md](references/rust-runtime.md). Do not copy model binaries into this skill tree.
3. For LADSPA and PipeWire virtual source/sink work, read [references/realtime-audio.md](references/realtime-audio.md), then adapt one of the bundled templates:
   - [scripts/deepfilter-mono-source.conf](scripts/deepfilter-mono-source.conf)
   - [scripts/deepfilter-stereo-sink.conf](scripts/deepfilter-stereo-sink.conf)
4. Before launching or restarting PipeWire, validate the edited config with [scripts/check_pipewire_config.py](scripts/check_pipewire_config.py). The checker is read-only and never launches PipeWire.
5. For failure diagnosis, read [references/troubleshooting.md](references/troubleshooting.md) before changing system services, installing host packages, or retrying builds.

## Required Inputs To Collect

- User goal: binary enhancement, Rust source build, LADSPA plugin build, PipeWire mono source, PipeWire stereo sink, demo/UI, tract/WASM, or troubleshooting.
- Platform and audio stack: OS, PipeWire/WirePlumber status, live audio device availability, and whether service restarts are allowed.
- Toolchain state: `cargo --version`, `rustc --version`, whether nightly is needed for the demo, and whether installing Rust/system packages is allowed.
- Artifact paths supplied by the user: `deep-filter` binary, model `.tar.gz`, LADSPA `.so`, and target PipeWire config file. Never invent private machine paths.
- Stop conditions: missing toolchain, missing plugin `.so`, non-absolute plugin path, absent model archive, live audio service risk, or user not authorizing host-level changes.

## Safety Notes

- This sub-skill contains self-contained distilled guidance and bundled templates only. It does not require opening the source repository to operate.
- Treat all Cargo commands as build recipes to run in a user-provided DeepFilterNet source tree or release source archive, not as verified outcomes.
- Do not launch PipeWire, restart user services, install packages, or mutate `/etc` without explicit user approval.
- Keep runtime troubleshooting local to this sub-skill unless the task is clearly Python, training, export, or evaluation; then route to the sibling sub-skill listed above.
