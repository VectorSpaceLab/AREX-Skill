# Kubeflow Pipelines Troubleshooting

Use this reference for cross-cutting KFP install/import/version issues that span multiple sub-skills.

## Symptoms and likely causes

| Symptom | Likely cause | Check | Recovery |
| --- | --- | --- | --- |
| `ImportError` for `kfp`, `kfp.dsl`, `kfp.compiler`, or `kfp.local` | The SDK package is missing or the wrong environment is active. | `python -c "import kfp; print(kfp.__version__)"` | Install the SDK in the active environment and retry. |
| `ImportError` for `kfp.kubernetes` or missing Kubernetes helper names | `kfp-kubernetes` is missing or does not match the SDK version. | `python -c "from kfp import kubernetes; print(kubernetes.__all__)"` | Install `kfp[kubernetes]` or `kfp-kubernetes` and keep versions aligned. |
| `kfp pipeline --help` or similar help output fails with localhost connection refused | A client-backed CLI group instantiated `Client` before help finished, and no live endpoint or kubeconfig was available. | Check `--endpoint`, `--namespace`, `KFP_ENDPOINT`, and kubeconfig/auth settings. | Use the correct API endpoint or switch to a no-client command such as `kfp dsl compile --help`. |
| A local execution helper fails because Docker is unavailable | `DockerRunner` requires Docker and related package support. | Check the runner class and whether Docker is installed and running. | Use `SubprocessRunner` for lightweight Python components or install Docker before retrying. |
| A compile succeeds but no cluster resource appears at runtime | Compile-only verification was mistaken for runtime validation. | Inspect whether the workflow only produced YAML/platform markers. | Use the appropriate cluster-backed or service-backed workflow if you need runtime proof. |
| Kubernetes helper calls appear to do nothing at runtime | A helper was attached to the wrong object or runtime prerequisites are missing. | Confirm the helper was called on a `PipelineTask`, not a component function or pipeline object. | Rewire the helper call and recompile. |
| Compile output ignores naming flags | `--kubernetes-manifest-format` was omitted, or the flags were applied to the wrong mode. | Check the compile command and output document kinds. | Add the manifest-format flag before expecting Kubernetes `Pipeline` / `PipelineVersion` output. |
| CLI compile cannot choose the right entry point | Multiple pipelines/components exist in the file. | Confirm the compile command includes `--function`. | Pass the exact function name or refactor to a single entry point. |
| JSON pipeline parameters fail to parse | The parameter string is not valid JSON. | Validate the payload with a JSON parser first. | Fix quoting, object syntax, and input names before recompiling. |
| Backend or frontend repo commands fail immediately | Required maintainer tooling is missing. | Check Go, Node, npm, Docker, Kind, kubectl, Ginkgo, and the pinned package versions. | Install the missing toolchain or narrow the task to a CPU-only package workflow. |
| `_KFP_RUNTIME=true` hides imports inside a runtime image | Runtime containers intentionally suppress most SDK imports. | Check the environment variable and the base image dependencies. | Move SDK-only imports out of runtime code or install the needed packages in the runtime image. |

## Common recovery patterns

- Start from the narrowest valid sub-skill and read its bundled reference before making assumptions.
- Prefer package/version checks over guesswork when a helper import is missing.
- Separate compile-time, client/service-bound, and cluster-bound failures; they have different prerequisites and different fixes.
- Do not recommend source-checkout paths or local environment details in user-facing answers. Use bundled scripts and references instead.

## When to escalate

Escalate to the repo-maintenance sub-skill when the issue is actually about generated files, CI, manifests, backend/frontend code, lockfiles, or repository setup rather than package usage.