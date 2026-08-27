# Cross-cutting Troubleshooting

## Import or install failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| `OSError` says Jina requires a newer Python | Runtime Python is below the supported range for the installed Jina. | Use a supported Python, preferably 3.10 or 3.11 for this baseline unless your deployment pins another version. |
| `docarray dependency is not installed correctly` | DocArray package is missing or inconsistent after upgrade. | Reinstall DocArray and rerun the minimal import check. |
| `ModuleNotFoundError: pkg_resources` during `jina` import | `jina-hubble-sdk` imports `pkg_resources`, which newer setuptools versions may omit. | Install or pin a setuptools release that provides `pkg_resources` until upstream removes the dependency. |
| Pip builds large wheels from source unexpectedly | Old pip or unsupported platform/wheel combination. | Upgrade pip in the target environment and check Python/platform support before installing broad extras. |
| Optional model/framework import fails inside an Executor | The user's Executor imports torch, TensorFlow, diffusers, transformers, or another package that Jina does not install by default. | Add those dependencies to the Executor project requirements or container image, not to every Jina caller environment. |

## Runtime/service failures

- If a Deployment or Flow fails to start because an Executor constructor raises, inspect the Executor `__init__` first and confirm it calls `super().__init__(**kwargs)`.
- If requests time out, increase `timeout_send` on the Flow/Deployment or Gateway when the Executor does slow model inference.
- If a Gateway cannot reach an Executor, check local ports, replicas/shards, service mesh policy, `retries`, and whether the Executor process actually became ready.
- If callbacks do not run, distinguish Executor-level response errors from network/Gateway failures. Network failures raise client exceptions and may bypass callbacks.

## Multiprocessing and platform issues

- On spawn-based platforms, put Flow/Deployment startup under `if __name__ == '__main__':` and keep Executor classes importable at module top level.
- Avoid nested/lambda Executor classes when using spawn because they are not picklable.
- On macOS fork crashes, set `OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES` or use a spawn-compatible structure.
- For CUDA initialization errors in forked subprocesses, set `JINA_MP_START_METHOD=spawn` and ensure model objects are initialized safely for the chosen process model.

## Source-checkout dependency leaks

Generated instructions should never require the original Jina repository checkout. If a future workflow needs a template or diagnostic script, use the bundled scripts in this skill or create a new self-contained helper in the user's project.
