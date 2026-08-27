# C FFI Reference

## Purpose

`ltp-cffi` builds C-compatible static and dynamic libraries over the Rust legacy implementation. Use it when a C/C++ application needs LTP legacy CWS/POS/NER without going through Python.

## Build shape

The C FFI crate is configured as:

```text
crate-type = ["cdylib", "staticlib"]
lib name = "ltp"
```

It depends on the Rust `ltp` crate with `serialization` and `parallel` features. Optional features include allocator choices such as `malloc` and `secure`.

## Typical steps

1. Ensure `cargo`, `rustc`, and a C compiler/linker are installed.
2. Build the C FFI crate with the feature set your deployment needs.
3. Locate the produced dynamic or static library.
4. Compile your C program with include/library paths pointing at the generated artifacts.
5. Provide legacy model binary paths at runtime.

## What to validate before building

Run the static checker:

```bash
python scripts/check_rust_layout.py --repo-root /path/to/ltp-checkout --require-models
```

The checker reports missing manifests, missing toolchains, and missing model binaries. It does not run `cargo build`.

## Linker troubleshooting hints

- If the compiler cannot find headers or declarations, verify the generated header/bindings process used by your build.
- If the linker cannot find `ltp`, add the generated target directory to the library search path.
- If runtime loading fails, set the appropriate dynamic-library path for your platform or link statically.
- If symbols mismatch, rebuild CFFI and the Rust crate from the same source revision.
