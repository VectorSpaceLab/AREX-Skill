# Troubleshooting

## Import and dependency failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'paddlenlp'` | The package imports `ppcv.ops.models.nlp` during `paddlecv` import. | Install `paddlenlp` in the same environment as `paddlecv`. |
| `ImportError: cannot import name 'download' from 'aistudio_sdk.hub'` | The installed `aistudio-sdk` release does not export the helper expected by `paddlenlp`. | Pin `aistudio-sdk` to a release that still exports `hub.download`.
| `ModuleNotFoundError: No module named 'pkg_resources'` | Newer `setuptools` releases no longer ship the top-level `pkg_resources` module in this environment. | Install a `setuptools` version that still provides `pkg_resources`.
| `ImportError: numpy.core.multiarray failed to import` or `cv2` has no `INTER_LINEAR` | The OpenCV wheel was built against an older NumPy ABI and is incompatible with NumPy 2.x. | Reinstall OpenCV with a NumPy 1.x wheel that matches the compiled bindings. |
| `ModuleNotFoundError: No module named 'paddlespeech'` | The package imports speech operators on module load. | Install `paddlespeech` and its transitive dependencies. |
| `ppdiffusers` / speech import errors around `urllib3` | The speech stack depends on `ppdiffusers`, which is sensitive to `urllib3` version ranges. | Keep `urllib3` within the range accepted by the installed `ppdiffusers` build. |
| `faiss` import or ShiTu-style workflow errors | Retrieval workflows need a Python-compatible `faiss` wheel. | Install a `faiss` build that exists for your Python version and platform. |

## Config and graph failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `AssertionError: device should be CPU, GPU or XPU` | Invalid `device` field in the YAML or CLI override. | Use one of the supported device names exactly. |
| `The last_op ... is not exist` | A config `Inputs` entry points to a missing prior op name. | Check the operator order and the `{last_op}.{output_name}` spelling. |
| `Input: ... could not be found from the last ops` | The config references an output key that no previous op produces. | Compare the requested input against the owner op's `get_output_keys()`. |
| `The module ... is not registered` | A custom op module was not imported before graph construction. | Import the module that defines the `@register` class before building the config. |
| `Module class already registered` | Duplicate class name in the registry. | Rename the custom op class or remove the duplicate registration. |
| `The output key in op ... is inconsistent` | A custom op returned keys different from its declared output names. | Make the returned dict keys match the operator's `get_output_keys()` contract. |

## Download and cache issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `Download from ... failed` | Network or cache access failed while resolving a `paddlecv://` URL. | Re-run with network access, confirm the cache directory is writable, or pre-download the asset. |
| Missing OCR fonts or unreadable table output | Font assets were not downloaded into the cache. | Verify `~/.cache/paddlecv/fonts` and the font-specific config paths. |
| `get_config_file()` or `get_model_file()` returns a path that is not usable | The referenced cache asset was not downloaded completely or was deleted. | Remove the broken cache entry and retry the lookup. |

## Runtime behavior notes
- The config parser merges command-line overrides into the YAML `ENV` and `MODEL` sections; a malformed `-o` override can break the graph before inference starts.
- `list_model(filters)` performs substring matching, so a too-specific filter can return no models.
- The package's public import path is broader than the single-op CV surface because `nlp` and `speech` are imported at module load.

## Recovery checklist
1. Re-run `scripts/smoke_import.py`.
2. Check `PaddleCV.list_all_supported_tasks()` and `list_model([...])`.
3. Verify the cache directories under `~/.cache/paddlecv/`.
4. Reinstall the dependency that matches the failing import path.
5. For custom graphs, inspect the owning operator's `get_output_keys()` and the YAML `Inputs` list.
