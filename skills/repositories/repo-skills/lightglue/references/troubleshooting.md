# Cross-cutting Troubleshooting

## When to read

Read this when LightGlue cannot be installed, imported, initialized, or run because of dependency, network, backend, or data-shape problems. For workflow-specific fixes, also read the nearest sub-skill troubleshooting reference.

## Install or import fails

| Symptom | Likely cause | Recovery |
|---|---|---|
| `ModuleNotFoundError: No module named 'lightglue'` | Package not installed in the active Python. | Install LightGlue in the Python that will run the task. Then run `python scripts/lightglue_smoke.py --device cpu` from this skill to verify import and synthetic matcher output. |
| `ModuleNotFoundError` for `torch`, `kornia`, `cv2`, or `matplotlib` | Runtime dependencies missing. | Install package runtime dependencies from `pyproject.toml`/`requirements.txt`: `torch`, `torchvision`, `numpy`, `opencv-python`, `matplotlib`, `kornia`. |
| `cv2` imports but `cv2.SIFT_create` is missing | OpenCV build lacks SIFT support. | Use an OpenCV package/version that exposes SIFT, or avoid SIFT-specific extraction and select another extractor. The schema-inspection helper reports this path clearly. |
| `ImportError: Cannot find module pycolmap` | `SIFT(backend='pycolmap*')` selected without optional `pycolmap`. | Use default `backend='opencv'`, install a compatible `pycolmap`, or choose another extractor. Do not require pycolmap for ordinary LightGlue usage. |

## First-use weights or network failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| Construction of `SuperPoint`, `ALIKED`, `DISK`, `DoGHardNet`, or feature-specific `LightGlue` stalls or raises URL/cache errors | Pretrained weights are being downloaded and network/cache access failed. | Check network/proxy access or pre-populate the PyTorch/Kornia model cache. For offline validation, use `python scripts/lightglue_smoke.py --device cpu` or `inspect_feature_schema.py --extractor sift`. |
| SIFT extraction works but `LightGlue(features='sift')` still tries to download | The OpenCV SIFT extractor has no neural weights, but the SIFT LightGlue matcher head is pretrained. | Cache/download the SIFT LightGlue matcher weights, or use `features=None` only for API smoke/custom trained matcher scenarios. |
| Benchmarks include first-run download time | Weights were not cached before measurement. | Run one untimed warm-up after ensuring weight download succeeds, then rerun the benchmark. The bundled benchmark times matcher forward after feature extraction but cannot remove first-use model initialization costs. |

## Backend and device problems

| Symptom | Likely cause | Recovery |
|---|---|---|
| `CUDA was requested but torch.cuda.is_available() is false` | CPU-only torch build, no visible GPU, or container/driver passthrough issue. | Use `--device auto` or `--device cpu`, or install a torch build compatible with the host GPU and driver. Do not treat CPU smoke success as CUDA verification. |
| MPS requested but unavailable | Non-Apple-Silicon host or PyTorch build without MPS. | Use CPU/CUDA, or run on an MPS-capable PyTorch build. |
| FlashAttention warning | `flash=True` requested but no FlashAttention or compatible PyTorch SDPA path is available. | This is usually a performance warning, not a correctness failure. Install a compatible accelerator stack only if speed is the task. |
| `torch.compile` is slow or changes pruning behavior | Compiled path pads to static lengths and partially disables point pruning for small inputs. | Use eager mode for small keypoint counts or when debugging; benchmark both compiled and eager modes before deciding. |

## Data shape and schema problems

| Symptom | Likely cause | Recovery |
|---|---|---|
| `Missing key image0 in data` or `Missing key image1 in data` | Direct matcher input dict is missing required top-level keys. | Pass `{'image0': feats0, 'image1': feats1}`. |
| Assertion failure on descriptor dimension | Matcher preset expects a different descriptor width than the supplied features. | Use the matching preset from `extractors-and-features/references/extractor-reference.md`, or construct `LightGlue(features=None, input_dim=D, ...)` for custom/precomputed descriptors. |
| SIFT/DoGHardNet matcher errors about `scales` or `oris` | SIFT-family matcher adds scale/orientation to keypoints and requires those keys. | Include `scales` and `oris` shaped `[B,N]`, or avoid `features='sift'/'doghardnet'` for feature dicts that lack them. |
| Too few/no matches | Images have low overlap/texture, keypoint threshold too strict, too few requested keypoints, or matcher `filter_threshold` too high. | Increase or remove keypoint limit, lower extractor thresholds where appropriate, try another extractor, lower `filter_threshold` cautiously, and validate keypoint counts before blaming the matcher. |

## Which bundled helper to run

- `scripts/lightglue_smoke.py --device cpu`: package import and synthetic matcher shape check; no pretrained weights.
- `sub-skills/extractors-and-features/scripts/inspect_feature_schema.py --image <image> --extractor sift`: offline feature schema inspection through OpenCV SIFT.
- `sub-skills/image-pair-matching/scripts/match_image_pair.py --image0 <a> --image1 <b> --features sift --device auto --output matches.png`: real matching workflow; can download matcher weights.
- `sub-skills/performance-and-visualization/scripts/benchmark_lightglue.py --image0 <a> --image1 <b> --features superpoint --repeat 10 --no-show`: matcher benchmark; can download extractor and matcher weights.
