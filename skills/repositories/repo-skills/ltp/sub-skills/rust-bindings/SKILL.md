---
name: rust-bindings
description: "Guides Rust ltp crate and ltp-cffi workflows for legacy
  CWS/POS/NER model loading, features, builds, and diagnostics."
disable-model-invocation: true
metadata:
  disco-role: operating
license: CC BY-NC 4.0
---

# Rust Bindings

Use this sub-skill for native Rust or C workflows around LTP's legacy CWS/POS/NER implementation.

## Choose this route when

- The user asks for the Rust crate `ltp`, `CWSModel`, `POSModel`, `NERModel`, `ModelSerde`, Cargo features, or Rust examples.
- The task involves `ltp-cffi`, static/dynamic C library builds, C headers/symbols, or linking a C program to LTP.
- The user needs to diagnose missing Rust toolchains, feature flags, or legacy model binary paths.

For Python `ltp_extension` wrappers, use [../legacy-extension/SKILL.md](../legacy-extension/SKILL.md). For neural Python inference/training, use the Python sub-skills.

## Safe workflow

1. Run the static checker against a checkout or staged source tree:

   ```bash
   python scripts/check_rust_layout.py --repo-root /path/to/ltp-checkout
   ```

   It checks manifests, toolchain presence, feature hints, and optional legacy model files. It does not build by default.

2. For Rust model loading, enable required features:

   ```toml
   [dependencies]
   ltp = { version = "0.1", features = ["serialization", "parallel"] }
   itertools = "0.14"
   apache-avro = "0.18"
   ```

3. Use model files explicitly:

   ```rust
   use std::fs::File;
   use ltp::{CWSModel, POSModel, NERModel, ModelSerde, Format, Codec};

   let cws: CWSModel = ModelSerde::load(File::open("cws_model.bin")?, Format::AVRO(Codec::Deflate))?;
   ```

4. Build `ltp-cffi` only after Rust and a C toolchain are intentionally available.

## Read these references

- [references/rust-api.md](references/rust-api.md) for crate features, model loading, prediction sequence, and utility APIs.
- [references/cffi-reference.md](references/cffi-reference.md) for the C binding build/linking surface.
- [references/troubleshooting.md](references/troubleshooting.md) for missing toolchain, features, model files, and linker issues.

## Boundaries

- This skill does not ship legacy model binaries or build artifacts.
- Rust/C examples require `cargo`/`rustc` and model files; the production environment that created this skill did not verify local Rust builds.
- Do not route Python wheel install problems here unless they involve the source Rust extension boundary; use root packaging and legacy-extension guidance first.
