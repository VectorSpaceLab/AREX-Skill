# API reference

## Verified upstream interfaces

| Artifact | Verified contract |
| --- | --- |
| `scripts/run_inpainting.py` | CLI is `python scripts/run_inpainting.py --conf_path CONF_PATH [--dry_run]` |
| `conf_mgt.conf_base.Default_Conf.get_dataloader` | `(self, dset='train', dsName=None, batch_size=None, return_dataset=False)` |
| `guided_diffusion.image_datasets.load_data_inpa` | `(*, gt_path=None, mask_path=None, batch_size, image_size, class_cond=False, deterministic=False, random_crop=False, random_flip=True, return_dataloader=False, return_dict=False, max_len=None, drop_last=True, conf=None, offset=0, **kwargs)` |
| `guided_diffusion.script_util.create_model_and_diffusion` | model/diffusion builder that consumes the model-side config keys |
| `guided_diffusion.script_util.create_classifier` | optional classifier builder for ImageNet-style guidance |
| `guided_diffusion.scheduler.get_schedule_jump` | schedule helper used by the resampling path; tuning belongs to schedule-visualization |
| `conf_mgt.conf_base.Default_Conf.eval_imswrite` | writes `srs`, `lrs`, `gts`, and `gt_keep_masks` files to the configured output paths |

## Exact signatures worth keeping in view

```python
# model/diffusion builder used by the sampler
create_model_and_diffusion(
    image_size,
    class_cond,
    learn_sigma,
    num_channels,
    num_res_blocks,
    channel_mult,
    num_heads,
    num_head_channels,
    num_heads_upsample,
    attention_resolutions,
    dropout,
    diffusion_steps,
    noise_schedule,
    timestep_respacing,
    use_kl,
    predict_xstart,
    rescale_timesteps,
    rescale_learned_sigmas,
    use_checkpoint,
    use_scale_shift_norm,
    resblock_updown,
    use_fp16,
    use_new_attention_order,
    conf=None,
)

# optional classifier builder for ImageNet-style runs
create_classifier(
    image_size,
    classifier_use_fp16,
    classifier_width,
    classifier_depth,
    classifier_attention_resolutions,
    classifier_use_scale_shift_norm,
    classifier_resblock_updown,
    classifier_pool,
    image_size_inference=None,
)

# output writer used after sampling
conf_mgt.conf_base.Default_Conf.eval_imswrite(
    self,
    srs=None,
    img_names=None,
    dset=None,
    name=None,
    ext='png',
    lrs=None,
    gts=None,
    gt_keep_masks=None,
    verify_same=True,
)
```

## Bundled helper contract

`scripts/run_inpainting.py`

| Flag | Meaning |
| --- | --- |
| `--conf_path PATH` | Required YAML config path |
| `--dry_run` | Inspect config, checkpoint, pair counts, and mask stats without loading the sampler |
| `--preview_pairs N` | Number of GT/mask pairs to print during dry-run inspection |
| `--device DEVICE` | Optional runtime device override written into the loaded config |
| `--cond_y INT` | Optional fixed ImageNet class label for class-conditioned configs |

## Runtime behavior covered by the helper

- Dry-run validates the checkpoint path, GT/mask directories, output paths, and common layout mistakes.
- The helper prints whether the config uses class conditioning and whether `cond_y` is set.
- Omitting `--dry_run` runs the same inference path as the bundled sampler helper after it adds the optional overrides.
- The helper keeps `gt_keep_mask` in the batch dict so the sampler does not lose the inpainting mask.

## Source mapping

| Source artifact | Bundled artifact |
| --- | --- |
| `test.py` | `scripts/run_inpainting.py` |
| `download.sh` | `references/assets.md` only; not bundled as a runnable helper |
