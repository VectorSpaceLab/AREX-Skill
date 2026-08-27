# Data troubleshooting

| Symptom | Likely cause | Action |
|---|---|---|
| `KeyError` for a dataset name | Registration module was not imported, or prefix/name differs | Import the module before dataset construction; print `CONVERSATION_DATA.keys()` and compare exact names. |
| No samples / empty index | `annotations` points at a parent without JSONL, or a remote path is inaccessible | Check the resolved path and count JSONL files. Remove stale `index_cache.json` only after preserving it for diagnosis, then let DexDataset rebuild. |
| Random fallback samples or repeated loader errors | A frame has missing media, invalid transforms, or too-short action horizon | Run the validator, inspect the first failing episode, and fail fast during a preflight loader rather than relying on `__getitem__` fallback. |
| Images are swapped | `images_keys`, camera order, and registration/conversion order disagree | Define one camera-order table and use it in data config, policy config, and deployment. |
| Video decode failure | Codec/container or relative path is invalid | Test a single video with the chosen decoder, mount the data root consistently, and avoid assuming source checkout paths. |
| State/action shape mismatch | Different robot embodiments were mixed or padding was omitted | Partition by action space or explicitly pad with a model-approved transform; update masks and norm stats together. |
| Bad wraparound motion | Rotation dimensions were treated as ordinary deltas | Set `periodic_mask`/`periodic_range` correctly and verify the action transform on a boundary-crossing pair. |
| NaNs or exploding normalized actions | Invalid raw values or near-zero standard deviation | Reject non-finite records, inspect dimension ranges, and use a bounded/epsilon-aware normalization policy. |
| Custom conversation is ignored | `conversations` has wrong keys or is not a list | Use `{from, value}` turns and include the image marker expected by the tokenizer. |
| RLDS converter cannot import | External `dlimp`/TensorFlow/TFDS stack is absent | Keep RLDS optional; install it in an isolated variant and verify `--help`/tiny conversion separately. |
