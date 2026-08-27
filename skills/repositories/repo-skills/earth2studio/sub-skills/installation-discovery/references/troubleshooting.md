# Installation and discovery troubleshooting

This guide owns predictable environment, optional-extra, access, and discovery
failures. It does not diagnose model numerical output, data quality, serving,
or inference performance. First capture the exact command, Python version,
`earth2studio.__version__`, PyTorch version, `torch.version.cuda`, and
`torch.cuda.is_available()` from the environment that failed.

| Signal | Likely cause | Recovery |
| --- | --- | --- |
| `Requires-Python` or resolver rejects the interpreter | Python is outside `>=3.11,<3.15`, or a selected extra has a narrower range. | Create/use Python 3.13; for GraphCast/GenCast use >=3.12; retry only the targeted command. Do not override the package's Python constraint. |
| Core `import earth2studio` fails | Partial install, wrong interpreter, or a broken base dependency. | Compare `command -v python`/`python --version` with the package manager environment; run the checker; reinstall the base package in a clean user-managed environment if needed. |
| Core import passes but a model class raises `ImportError` | Its optional extra is absent or a transitive dependency is not importable. | Identify the class's documented extra, install that targeted extra, then retry a targeted import. Do not install every extra as the first response. |
| `uv` reports an AIFS or ACE2 conflict | uv conflict declarations are working as designed. | Put the competing model families/experiments in separate environments. Avoid bypassing the resolver. |
| Resolver succeeds but a compiled extension will not import | Extension was built against a different PyTorch/CUDA or stale build cache. | Check torch/CUDA first; rebuild the selected extension in the same environment, clearing only user-approved package caches. For undefined `torch-harmonics` symbols, a clean rebuild may be necessary. |
| `Python.h: No such file or directory` | Python development headers are missing for a source build. | Ask the user to install the OS-equivalent Python development package, then rerun the selected install. |
| `Cannot find CMake executable` | CMake is absent from `PATH` for a build such as `dm-tree` or `natten`. | Install/configure CMake through the user's system policy, verify `cmake --version`, and rerun only the targeted extra. |
| AIFS install spends a long time building `flash-attn` | Flash Attention is a known build-sensitive dependency. | Allow a bounded user-approved build, use a compatible prebuilt wheel or suitable PyTorch container, or choose a different model/environment. Do not claim that a generic wheel is compatible. |
| FCN3/SFNO build is slow or fails in CUDA extension compilation | `torch-harmonics` needs a matching build toolchain and CUDA architecture. | Confirm PyTorch/CUDA/GPU, Python headers, CMake/Ninja, and the model's build guidance. If the user chooses it, constrain `TORCH_CUDA_ARCH_LIST` to the actual GPU and use `FORCE_CUDA_EXTENSION=1` only as documented. |
| `torch.cuda.is_available()` is false or no device is visible | CPU-only PyTorch, missing/incompatible driver, container GPU not passed through, or CUDA mismatch. | Verify `nvidia-smi`/driver policy and the PyTorch install; compare `torch.version.cuda` to the intended runtime. Do not promise GPU extras from a CPU check. |
| ONNX Runtime cannot bind GPU input or cannot load `libonnxruntime_providers_cuda.so` | ONNX Runtime GPU provider and CUDA libraries do not match. | Follow the selected ONNX Runtime GPU installation guidance for the CUDA line, then rerun the targeted import/provider check. FengWu, FuXi, and Pangu require more than the core package. |
| Data source construction reports `cdsapi`/ecCodes missing | The `data` extra or GRIB system library is absent. | Install the targeted `data` extra; if GRIB support still reports a native library error, ask the user to install ecCodes using the OS/Conda policy and recheck. Credentials are a separate step. |
| `ImportError` appears only when creating a data source | Many data connectors defer optional imports until construction. | Treat this as useful dependency evidence; map the error to the named extra, install it, and perform a constructor/import check without requesting remote data. |
| NGC public model access reports invalid org/team | Stale NGC config or API-key environment variables can interfere with guest/public resolution. | Ask the user to inspect or temporarily remove the conflicting local configuration under their credential policy, or set provider-documented guest organization/team values. Never request or print a key. |
| Checkpoint URI resolves but access is denied | Provider permissions, terms, region, network, or URI are wrong. | Verify the URI/provider and user authorization outside this sub-skill; record the candidate as unverified. Changing cache variables cannot grant access. |
| Model or data feature appears in docs but not in the installed package | Documentation may track a different release/branch than the installed package. | Inspect `earth2studio.__version__`, then use the matching version's catalog/API metadata or install an approved source/release intentionally. |
| A source lexicon contains a variable but a model still cannot use it | Lexicon coverage is only the name layer; grid, levels, units, cadence, domain, or coordinate order differ. | Compare `input_coords()` and source output coordinates, then check source-specific availability and transforms. Do not rename or interpolate blindly. |
| `fetch_data`/`fetch_dataframe` would require CuPy/cuDF | A later data movement request targets CUDA, but the relevant DA/data dependency is absent. | Keep this sub-skill at discovery; report the required CUDA dataframe/array dependency and hand off to the data/inference workflow. |
| Cache fills a shared filesystem or times out | Model/data caches are large or remote package timeout is too low. | Set `EARTH2STUDIO_MODEL_CACHE` and/or `EARTH2STUDIO_DATA_CACHE` to approved locations, check quotas, and adjust `EARTH2STUDIO_PACKAGE_TIMEOUT` deliberately. Do not delete cache content automatically. |

## Unsupported Python/CUDA synthetic case

If a user requests `Python 3.10 + CUDA 12` for an extra whose dependency line
expects Python >=3.11 and the current TOML target is CUDA 13, respond in this
order:

1. State that Python 3.10 is outside the package range and that CUDA 12 is not
   automatically compatible with a CUDA-13 PyTorch/extra resolution.
2. Do not recommend a resolver override or a broad `all` install.
3. Offer Python 3.13 and a PyTorch build selected for the actual driver, then a
   fresh targeted extra environment. If CUDA 12 is mandatory, mark the selected
   model extra as unverified until its dependencies explicitly support that
   runtime.
4. Ask the user to run the checker and provide `torch.version.cuda`,
   `torch.cuda.is_available()`, device name, and the targeted import result.

## Conflicting-extra synthetic case

If a user asks for `AIFS + AIFS2 + ACE2 + FCN3` in one environment:

1. Point out the declared AIFS-family conflict and the ACE2 conflict with
   FCN3; do not silently choose one.
2. Separate the AIFS variants and separate ACE2 from FCN3. A valid two-environment
   partition can be `aifs + ace2` and `aifs2 + fcn3` if no other selected extras
   conflict; otherwise use more environments.
3. Keep shared source/data inspection in a base/data environment only when its
   dependencies do not pull the conflicting model extras into the same lockfile.
4. Record the chosen model class, extra, PyTorch/CUDA build, checkpoint/cache,
   and license evidence for each environment.

## Verification levels

Use precise language in the handoff:

- **Observed:** the package version, Python range, extra declaration, class
  export, or lexicon key was read from the selected source/install.
- **Import-checked:** a targeted module imported in the user's environment.
- **Hardware-checked:** PyTorch reported the expected CUDA availability/device.
- **Name-compatible:** model required variables were covered by source lexicon
  keys; grid/time/access may still be open.
- **Access-verified:** the user separately confirmed a provider/checkpoint/data
  access path. This sub-skill does not perform that access.

Do not upgrade any lower level to a stronger claim in the final handoff.
