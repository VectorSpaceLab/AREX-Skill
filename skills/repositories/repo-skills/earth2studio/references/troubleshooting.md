# Cross-cutting troubleshooting

Use the first failing boundary to choose the focused sub-skill. Do not repair a
later layer while an earlier one is still unverified.

| Symptom | Likely boundary | Recovery |
|---|---|---|
| `ModuleNotFoundError` for `earth2studio` | package/environment | Use a supported Python, install the package in the active environment, and run a minimal import. Do not add every optional extra. |
| Optional model/data import fails | targeted extra or compiled ABI | Identify the concrete class/provider, install its documented extra, and match Python, PyTorch, CUDA, compiler, and extension ABI. See installation-discovery and models-and-assimilation troubleshooting. |
| CUDA is unavailable or a kernel/undefined-symbol error appears | framework/driver/extension | Check `torch.version.cuda`, `torch.cuda.is_available()`, device capability, driver support, and extension build compatibility. A CPU pass is not a GPU pass when the model requires CUDA. |
| GRIB/ecCodes or cloud-source access fails | data dependency/credential/network | Separate missing local libraries from provider credentials, endpoint availability, permissions, and variable/lexicon mismatch. Validate a local source or lexicon first. |
| `KeyError`, unsupported variable, empty result, or time mismatch | data/schema/coordinate contract | Inspect the selected source lexicon and model `input_coords()`, normalize time/lead-time/tolerance, and request only supported fields. Do not silently rename variables. |
| Output backend rejects a coordinate or cannot reopen a store | IO/layout/permission | Initialize complete ordered coordinates and variable names, check chunk/shard alignment and write mode, use a temporary local store, then retry the remote store. |
| Restart repeats or skips steps | checkpoint catalog/state | Check checkpoint level, write count, lead-time coordinate, and whether model/component state is serializable. A low-level checkpoint may require a clean re-run. |
| Remote client returns 4xx/5xx, `pending_results`, or connection errors | serving/service | Validate workflow schema, request payload, auth, API URL, health, Redis/RQ, output storage, and result lifecycle separately. Never print tokens or assume a service is running. |
| Metric shape/weights are wrong | statistics axes | Align named ensemble/time/spatial axes, truth/prediction coordinates, masks, and latitude weights before scoring. |
| Custom component fails at runtime | protocol/schema | Implement exact call/iterator/coords/schema methods, preserve coordinate ordering and devices, and run the offline contract helper before a real workflow. |

## Stop conditions

Stop and report a precise prerequisite instead of repeated retries when the task
needs credentials, a private dataset, a missing model license, a remote service,
large downloads, unavailable GPU/accelerator hardware, or a dependency variant
that cannot be built safely. Narrow the workflow or obtain the prerequisite;
do not claim verification from source inspection alone.
