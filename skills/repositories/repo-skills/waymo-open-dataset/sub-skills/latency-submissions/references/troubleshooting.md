# Latency Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: wod_latency_submission` | Module not on `PYTHONPATH` or not installed in the image | Package the module or set `PYTHONPATH`; test with the bundled validator. |
| Missing `.npy` input | `DATA_FIELDS` asks for a field not extracted for that frame | Reduce `DATA_FIELDS` or ensure preprocessing creates the requested field, including `_1`/`_2` suffixes. |
| Mismatched output lengths | `boxes`, `scores`, and `classes` have different first dimensions | Return all three arrays with the same `N`; use `validate_latency_submission.py`. |
| 2D conversion fails on camera input | More than one input field or field does not end in `_IMAGE` | For 2D latency conversion, use exactly one camera RGB input field. |
| Objects are skipped | Score below threshold or box length/width/height too small | Check result arrays before conversion; low-confidence or degenerate boxes are filtered. |
| GPU timing differs locally | Official timing runs inside challenge infrastructure and container constraints | Validate the module contract locally, then use the official Docker submission path for timing. |
