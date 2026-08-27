# Cross-Cutting Troubleshooting

## Purpose

Read this first when the package fails to install, import, or expose the expected console commands.

## 1) `ModuleNotFoundError` for core dependencies

**Symptoms**

- `import hivemind` fails because `numpy`, `torch`, `scipy`, `uvloop`, `pydantic`, or a similar core dependency is missing.
- `python scripts/check_install.py` reports missing import(s).

**Likely causes**

- the package was installed into a different Python environment
- a local checkout was installed without the build requirements it needs
- the current interpreter is not the one that owns the package

**Recovery**

1. Re-run the bundled helper: `python scripts/check_install.py`.
2. If you are working from a checkout, reinstall with `python -m pip install -e . --no-build-isolation` after making sure `grpcio-tools` is installed.
3. If you are using a published package, install `hivemind` into the same interpreter you intend to use for the skill.

## 2) Console commands are missing

**Symptoms**

- `hivemind-dht` or `hivemind-server` is not found on `PATH`.
- The helper script says a console script is missing.

**Likely causes**

- the package is not installed into the active environment
- the environment was created but never used for the install
- a shell PATH points at the wrong environment

**Recovery**

- verify the environment with `python scripts/check_install.py`
- reinstall the package into the same interpreter you will use to run the command
- avoid relying on a shell activation step when a direct interpreter path is available

## 3) CUDA defaults surprise you

**Symptoms**

- the server or a training peer starts on a GPU when you expected CPU
- the host has CUDA available even though you only wanted a CPU smoke test

**Likely cause**

- the package sees a CUDA-capable host and takes the default GPU path

**Recovery**

- pass `--device cpu` to `hivemind-server` when you want a CPU-only deployment
- use `python scripts/check_install.py --check-cuda` only when you want to confirm the GPU path
- remember that the base package works fine on CPU even when CUDA is present

## 4) Optional compression backends are missing

**Symptoms**

- `BlockwiseQuantization` raises an import error for `bitsandbytes`
- a user tries an optional compression path that is not installed

**Likely cause**

- the optional backend was never installed

**Recovery**

- fall back to `NoCompression`, `Float16Compression`, or the 8-bit quantizers that do not need `bitsandbytes`
- install `bitsandbytes` only when the blockwise path is truly required

## 5) DHT and MoE task failures

If the issue is specifically about bootstrap peers, relay settings, remote experts, or optimizer state-sharing timeouts, move to the owning sub-skill instead of trying to solve it here:

- [`sub-skills/dht/references/troubleshooting.md`](../sub-skills/dht/references/troubleshooting.md)
- [`sub-skills/collaborative-training/references/troubleshooting.md`](../sub-skills/collaborative-training/references/troubleshooting.md)
- [`sub-skills/moe/references/troubleshooting.md`](../sub-skills/moe/references/troubleshooting.md)

## 6) When to stop

Stop local debugging when the failure depends on:

- a missing compiler or toolchain on the host
- network access you cannot allow
- a GPU/accelerator you do not have
- a package version pinned by policy in another environment

In those cases, report the exact missing prerequisite and the command that exposed it instead of guessing.
