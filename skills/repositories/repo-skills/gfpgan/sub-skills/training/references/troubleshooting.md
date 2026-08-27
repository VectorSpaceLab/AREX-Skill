# GFPGAN Training Troubleshooting

## LMDB Path Error

**Symptom**

`ValueError: 'dataroot_gt' should end with '.lmdb'`

**Cause**

The config sets `io_backend.type: lmdb`, but `dataroot_gt` does not end in `.lmdb`.

**Recovery**

Use a real LMDB directory with `meta_info.txt`, or change `io_backend.type` to `disk` for an image folder.

## Missing Component Landmark File

**Symptoms**

- `torch.load(component_path)` fails.
- Dataset cannot return `loc_left_eye`, `loc_right_eye`, or `loc_mouth`.

**Cause**

`crop_components: true` requires a landmark `.pth` file.

**Recovery**

Generate the file with `scripts/parse_ffhq_landmarks.py` or disable `crop_components` and use the simple config.

## Missing Pretrained Checkpoints

**Symptoms**

- `load_network` failures.
- Missing StyleGAN2 decoder or ArcFace identity paths.

**Cause**

The config points to absent or incompatible checkpoints.

**Recovery**

Check:

- `network_g.decoder_load_path`
- `path.pretrain_network_identity`
- `path.pretrain_network_g`
- discriminator/component pretrained paths when present

Do not launch full training until every required path exists.

## OpenCV / BasicSR Degradation Error

**Symptoms**

- JPEG compression degradation raises an OpenCV argument/type error.
- Dataset smoke fails before model code runs.

**Cause**

OpenCV, NumPy, and BasicSR dependency versions can interact poorly in the JPEG degradation helper.

**Recovery**

Pin a version set known to work for GFPGAN/BasicSR, then re-run a single-item dataset smoke. Do not debug this through full training.

## CUDA or Extension Issues

**Symptoms**

- CUDA unavailable for GPU-only component tests.
- BasicSR fused/custom op import or JIT failures.
- Original model path fails while clean model path works.

**Cause**

The original/paper model and some BasicSR/StyleGAN2 paths can require extension/JIT support. Clean models avoid much of this surface.

**Recovery**

- Use clean architecture for modern inference/fine-tuning unless the user needs the original paper model.
- For original model work, follow the BasicSR JIT or extension compilation path and verify PyTorch/CUDA/compiler compatibility.
- Treat CPU-only checks as insufficient for required GPU training claims.

## OOM or Training Too Slow

**Symptoms**

- CUDA out-of-memory.
- Training stalls on CPU.
- Distributed launch fails from resource limits.

**Recovery**

- Reduce batch size per GPU and workers.
- Use fewer validation images or disable image saving for smoke tests.
- Confirm GPU memory and distributed backend before launch.
- Do not run full training as an unattended verification step.

## Checkpoint Conversion Fails

**Symptoms**

- Missing `params_ema` key.
- Unexpected key names in `stylegan_decoder` or `conv_body` mappings.

**Cause**

The source checkpoint is not the bilinear/original GFPGAN checkpoint shape expected by the converter.

**Recovery**

- Inspect top-level checkpoint keys.
- Try `--param-key params` if the checkpoint stores normal weights instead of EMA weights.
- Verify `--narrow` and `--channel-multiplier` match the source model.
- Do not use conversion errors as evidence that the clean model cannot be fine-tuned; first confirm checkpoint lineage.

## Config Builds But Validation Fails

**Cause**

Validation data paths or metrics may not match train data assumptions. `nondist_validation` expects dataloader fields and may save images under visualization paths.

**Recovery**

- Validate a tiny paired dataset first.
- Check `val.metrics`, `val.suffix`, `path.visualization`, and normalization fields.
