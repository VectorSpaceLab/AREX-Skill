# Repository Provenance

This file records the source state used to construct the Kubeflow Pipelines repo skill.

| Field | Value |
| --- | --- |
| Repository | `kubeflow/pipelines` |
| Source commit | `1630f8063b3434217f54da67aea221b910ea238b` |
| Branch | `master` |
| Exact tag at HEAD | `none` |
| Working tree state | dirty: yes; untracked `skills/` tree present during generation |
| Repo version file | `2.17.0` in `VERSION` |
| SDK package version | `2.15.2` in `sdk/python/kfp/version.py` |
| Kubernetes addon version | `2.15.2` in `kubernetes_platform/python/kfp/kubernetes/__init__.py` |
| Pipeline-spec version | `2.15.2` in `api/v2alpha1/python/setup.py` |
| Remote URL | `omitted-private-or-unknown` |

## Evidence paths

All evidence paths below are relative to the repository root.

- `README.md`
- `sdk/python/README.md`
- `sdk/python/kfp/`
- `sdk/python/kfp/version.py`
- `api/v2alpha1/python/`
- `kubernetes_platform/python/`
- `docs/sdk/source/`
- `samples/`
- `backend/README.md`
- `frontend/README.md`
- `docs/agents/`
- `developer_guide.md`
- `CONTRIBUTING.md`
- `manifests/kustomize/README.md`
- `test/README.md`
- `components/google-cloud/README.md`

## Why this matters

Future agents can compare this provenance snapshot with the current checkout or installed package set to decide whether the generated skill is still aligned with the repo or should be refreshed.