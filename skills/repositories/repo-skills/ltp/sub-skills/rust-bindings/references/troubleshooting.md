# Rust and CFFI Troubleshooting

## Toolchain failures

| Symptom | Cause | Recovery |
| --- | --- | --- |
| `cargo` or `rustc` not found | Rust toolchain not installed. | Install Rust intentionally, then rerun the static checker. Do not start source builds without approval. |
| Build fails while fetching crates | Network/index access blocked. | Use approved cargo registry/cache settings or vendor dependencies deliberately. |
| Python `ltp-extension` source build fails | The Python extension uses Rust/maturin, not just pip. | For ordinary Python use, prefer a wheel. For extension development, install Rust and maturin first. |

## Feature and API failures

| Symptom | Cause | Recovery |
| --- | --- | --- |
| `ModelSerde` missing | `serialization` feature not enabled. | Add `features = ["serialization"]` to the Cargo dependency. |
| Parallel prediction unavailable or slow | `parallel` feature omitted or batch too small. | Enable `parallel` and benchmark with realistic batches. |
| Type aliases such as `CWSModel` unavailable | Serialization-gated aliases are not compiled. | Enable `serialization`. |

## Model file failures

- Rust examples require local legacy model binaries.
- Check paths for `cws_model.bin`, `pos_model.bin`, and `ner_model.bin` before running examples.
- Keep model files and source revision aligned; mismatched model formats can fail at deserialization.

## C linking failures

| Symptom | Cause | Recovery |
| --- | --- | --- |
| `cannot find -lltp` | Library path not supplied or crate not built. | Build `ltp-cffi`, then pass the target library directory to the linker. |
| Runtime shared-library load error | Dynamic library path not configured. | Set the platform library path or link statically. |
| Symbol mismatch | C header/bindings and library came from different revisions. | Regenerate/rebuild from the same source revision. |

## Stop conditions

Ask before installing system toolchains, starting long release builds, changing linker/global library paths, or downloading model binaries.
