# Data troubleshooting

| Symptom | Likely cause | Recovery |
|---|---|---|
| `No valid episodes` or a batch of `None` | Missing one member of a required video/qpos/language/text tuple | Compare basenames and required directories; start with one known-good episode and a small `max_episodes`. |
| Out-of-bounds frame error | Chunk settings exceed video length or a stale video/qpos pair is mismatched | Check video frame count and qpos length; reduce frame count/span or repair the pair. |
| Wrong action shape | `num_video_frames`, frequency ratio, or action dimension differs between config and data | Recompute `action_chunk_size`; compare `[A,D]` with `common.action_dim`; do not pad silently. |
| Language and text mismatch | Random embedding variant was not aligned with the corresponding instruction line | Preserve the selected index and use the same line; regenerate paired resources if needed. |
| VLM processor import/download failure | Transformers processor or checkpoint is missing; network/cache unavailable | Keep `vlm_inputs` disabled only for workflows that do not require VLM features; otherwise install/load the intended processor and checkpoint. |
| Decord cannot open a video | Legacy wheel/platform or damaged/unsupported codec | Install a platform-compatible Decord/FFmpeg stack, test one local MP4, and check RGB decoding. |
| Images are stretched or wrong size | Direct resize bypassed aspect-ratio padding | Use `resize_with_padding` or the bundled camera helper and verify `[H,W]` before writing data. |
| LeRobot worker hangs or raises T5 encoder error | On-the-fly T5 initialization was attempted in a DataLoader worker | Precompute embeddings in the main process, then disable fallback during workers. |
| Conversion writes to the wrong place | Example YAML still contains a placeholder or old absolute path | Replace source/target roots explicitly and check free space and permissions before launch. |
| Camera helper returns no output | Empty/mismatched arrays or unsupported channel count | Use three non-empty HWC arrays with matching channels; run `--help` and the tiny fixture check. |

Missing CUDA is not a data-layout error. Dataset parsing can be checked on CPU,
but final Motus training/inference still requires the CUDA backend and model
assets described by the sibling skills.
