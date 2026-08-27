# Visualization and benchmarking troubleshooting

Use this as a fail-closed checklist. Each recovery keeps the original
condition visible; none authorizes fabricated images, metrics, or benchmark
comparisons.

| Symptom | Likely cause | Recovery | Stop condition |
|---|---|---|---|
| Config import fails before the dataset is built | Legacy `mmcv`/`mmdet`/`mmdet3d` versions, plugin path, or custom op is unavailable | Verify the documented dependency versions, `PYTHONPATH`, plugin setting, and custom-operation build in the intended environment; do not change model config in this skill | Import still fails or matching extension is unproven |
| Checkpoint load reports missing/unexpected keys or incompatible shapes | Checkpoint and config are from different model variants or branches | Identify both artifacts and select a matching pair; preserve the failed pair in the report | No verified compatible pair |
| Dataset construction fails or images are missing | Annotation pickle/map JSON, camera files, CAN-bus data, or data root is incomplete | Route layout/conversion to data-preparation and verify one complete sample before retrying | Required annotations or camera files remain absent |
| Visualization output directory exists but has no sample children | Test set was empty, all GT labels were empty, or inference exited early | Inspect native stdout/log, verify split and annotations, and count usable samples | No usable dataset sample or no completed model forward |
| `--score-thresh` appears ineffective | Threshold is higher/lower than expected, or the docs (0.3) and parser default (0.4) were conflated | Pass an explicit float and record it; compare artifacts from real runs only | No completed run or threshold value is unknown |
| `--gt-format se_pts` or `bbox` produces no named GT image | Current source draws these formats but does not save a dedicated file | Use `fixed_num_pts` or `polyline_pts` for native saved artifacts, or route a code change for persistent formats | A report claims an absent image was produced |
| Native video assembly crashes in `hconcat`, `vconcat`, or image operations | A camera/map file is missing, undecodable, or has incompatible dimensions | Use the bundled helper; inspect its skipped-sample report and replace/regenerate invalid artifacts | No complete decodable sample remains |
| The visualization directory has mixed names and no `SAMPLE_VIS.jpg` | Non-frame files are present and the native directory order is unspecified; sample image has not yet been generated | Run `scripts/make_video.py`; it ignores non-directories, sorts frame names, creates `SAMPLE_VIS.jpg`, and requires the six cameras plus both map images | All frame directories are incomplete or unreadable |
| MP4 is zero bytes or cannot be opened | `mp4v` codec unavailable, output directory is unwritable, or a writer was not opened | Check the helper's writer error, try a supported local codec/container, and verify with a media reader available to the user | No writer can open or no decoder can read the resulting file |
| Video plays but frames look stretched or order is unexpected | Native helper assumes its layout; arbitrary image dimensions or unsorted source entries were used | Confirm the helper's fixed 1680x450 output and lexicographic frame order; use consistent camera dimensions for better display | Order or geometry is not recorded |
| `benchmark.py --samples 100` does not stop or `--log-interval 10` errors | Source parser omits `type=int` for these flags | Treat native explicit numeric flags as unsafe; use defaults only if they satisfy the request, or use a reviewed corrected wrapper | No tested numeric handling under the requested protocol |
| FPS is reported for unlike GPUs or batch sizes | Comparison changes hardware or throughput semantics | Build a manifest and rerun both conditions with identical protocol, or mark the comparison blocked | GPU, batch, view count, precision, or extension status is missing |
| Overall FPS is surprising near the sample limit | Native script's final elapsed value is added twice in the overall path | Report native output with this caveat or use a reviewed corrected timing implementation | Timing implementation is unknown |
| Benchmark never prints overall FPS | Requested count exceeds the usable dataset or fewer than five samples remain after warm-up | Compare requested count with dataset length and record actual processed samples | No post-warm-up sample exists |
| `analyze_logs.py` rejects a file or raises `KeyError` | File is not line-delimited JSON, lacks epoch records, has a missing metric, or uses incompatible eval cadence | Validate each line, requested `--keys`, `--mode`, and `--interval`; use `--out` for headless plotting | Logs or metric provenance remain incomplete |
| Time analysis changes substantially with `--include-outliers` | First iteration of each epoch includes startup/data-loader overhead | Report both policies only when both are actually run; do not silently mix them | Timing policy is not recorded |

## Minimal recovery records

For a visualization failure, retain:

```text
config: ...
checkpoint: ...
threshold: ...
gt-format: ...
show-dir: ...
dataset split/sample count: ...
first failing sample: ...
missing or undecodable files: ...
legacy runtime/extension status: ...
```

For a benchmark or log failure, retain:

```text
status: observed | deferred | blocked
config/checkpoint: ...
GPU/batch/views/precision: ...
sample and warm-up policy: ...
log files and requested keys: ...
stdout or exception: ...
recovery owner: ...
```

Do not continue to a qualitative or quantitative conclusion when a strict
input, artifact, decoder, metric, or comparison-condition gate is unresolved.
