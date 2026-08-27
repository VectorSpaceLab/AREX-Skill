# Release and Packaging

## Versioning

The observed package version for this skill is `0.2.1` at tag `v0.2.1`. Refresh release guidance from the current repository when versioning policy changes.

Before release-like work, check:

```bash
python -c "from importlib.metadata import version; print(version('quip-protocol'))"
quip-miner --help
```

If working from a source checkout, ensure package metadata, docs, Docker configs, and CLI help agree on major runtime behavior.

## PyInstaller Selftest

`quip-miner selftest` verifies packaged binaries can load bundled runtime assets, especially scalecodec type-registry preset data that PyInstaller can miss. Run it on the frozen binary/build artifact, not just the editable source install:

```bash
quip-miner selftest
```

A failure can otherwise show up later as a misleading validator-connect error when `SubstrateInterface` fails to load its type registry.

## Docker Images

Docker assets include CPU and CUDA Dockerfiles, compose validator config, entrypoint, and example TOML files. Release/build validation should confirm:

- CPU image can run with a CPU config and persistent `/data/keystore.json`.
- CUDA image includes CUDA dependencies and is run with appropriate GPU runtime flags.
- `/data/config.toml` is copied/generated once and then treated as the editable source of truth.
- REST telemetry binds to `0.0.0.0` only when intentionally exposed.
- Containers get enough shared memory for multiprocessing/shared-memory rings.

Do not push images or run long live mining from an automated skill verification step unless the user explicitly asks.

## Packaging Data

Package data includes topology JSON/GZip files, embeddings where present, CUDA/Metal kernels, and `genesis_block.json`. Packaging changes should verify these files are included in wheels/frozen bundles when needed.

## Release Checklist

1. Run targeted tests for changed areas.
2. Run no-inline-sampling lint for sampling/runtime changes.
3. Verify CLI help and subcommand help.
4. Verify package metadata version and tag consistency.
5. Run `quip-miner selftest` on packaged/frozen artifacts.
6. Validate Docker configs with `quip-miner resolve-modes --config` or the bundled config lint helper before live container runs.
7. Document optional backend skips and any live QPU/cloud tests that were intentionally not run.
