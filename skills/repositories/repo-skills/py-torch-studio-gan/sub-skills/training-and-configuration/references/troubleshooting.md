# Training and configuration troubleshooting

Use this reference when a StudioGAN `src/main.py` training/configuration command fails before expensive training, HDF5 preparation, metric evaluation, or checkpoint resume. Prefer rerunning the safe helpers first:

```bash
python sub-skills/training-and-configuration/scripts/validate_studiogan_config.py \
  --repo-root /path/to/PyTorch-StudioGAN \
  --cfg /path/to/config.yaml \
  --data-dir /path/to/data --save-dir /path/to/save --train --gpus 1
```

```bash
python sub-skills/training-and-configuration/scripts/check_studiogan_dataset.py \
  --data-dir /path/to/data --require-valid --min-classes 2 --min-images-per-class 1
```

## Fast failure matrix

| Symptom or error fragment | Likely cause | Recovery |
| --- | --- | --- |
| `There does not exist 'SECTION.attr' attribute in the config.py.` | The YAML contains a misspelled or unsupported config key. | Start from a known StudioGAN YAML family and edit only recognized `DATA`, `MODEL`, `LOSS`, `OPTIMIZATION`, `PRE`, `AUG`, `RUN`, or `STYLEGAN` fields. |
| `-metrics option can only contain is, fid, prdc or none` | Unsupported metric token or `none` mixed with real metrics. | Use `-metrics is fid prdc`, a subset, or `-metrics none` alone. |
| `Please specify data_dir...` | Native compatibility requires `-data` unless the command only saves fake images. | Add `-data /path/to/data`. For CIFAR10/100 this is a writable cache root; for custom datasets it is the root containing `train/<class>/...`. |
| ImageFolder reports no classes or no images | Custom data was pointed at images directly or lacks split/class directories. | Restructure as `/path/to/data/train/<class>/image.*`; add `valid/<class>/...` when using `-ref valid`. |
| `There is no data for validation.` | CIFAR10/100 config used `-ref valid`. | Use `-ref train` or `-ref test` for CIFAR10/100. |
| `DATA.num_classes` mismatch symptoms or conditional labels look wrong | YAML class count does not match ImageFolder class directories. | Run the dataset checker, then update `DATA.num_classes` and preserve class directory names. |
| `load_data_in_memory option is appliable with the load_train_hdf5 (-hdf5) option` | Native `-l` was supplied without `-hdf5`. | Add `-hdf5` or remove `-l`. |
| HDF5 creation is slow or storage explodes | High-resolution or large ImageFolder data was cached into train HDF5. | Start without `-hdf5`, or explicitly provision storage/RAM before using HDF5 and `-l`. |
| `Batch_size should be divided by the number of gpus.` | `OPTIMIZATION.batch_size` is not divisible by the visible GPU count times total nodes. | Edit the YAML batch size or change visible GPUs/nodes. Revalidate with the intended `--gpus` and `--total-nodes`. |
| `Cannot perform distributed training with a single gpu.` | `-DDP` was selected with only one visible GPU. | Remove `-DDP` or expose multiple GPUs and set DDP rendezvous variables. |
| DDP hangs at startup | Missing or conflicting `MASTER_ADDR`/`MASTER_PORT`, wrong node rank, or backend mismatch. | Set rendezvous variables, use unique ports, check `-tn/-cn`, and prefer `--backend nccl` for CUDA training. |
| DDP assertion mentions visualization, KNN, interpolation, frequency, t-SNE, DDLS, SeFa, or CAS | Analysis flags were mixed into a DDP training command. | Train with DDP first using ordinary training flags, then run checkpoint analysis later without `-DDP`; route to the sampling sub-skill. |
| `RUN.save_freq should be divided by RUN.print_freq` | Logging/save interval mismatch. | Choose a `--save_freq` multiple of `--print_freq`. |
| `Freezing discriminator needs a pre-trained model` | `--freezeD` was supplied without `-ckpt`. | Add `-ckpt /path/to/source_checkpoint` or remove `--freezeD`. |
| Checkpoint load reports missing/unexpected keys or shape mismatch | Resume/freezeD checkpoint does not match the target config family. | Use the YAML family, resolution, backbone, and conditioning method that produced the checkpoint, or treat it as incompatible transfer. |
| `deep_conv ... spatial resolution is not 32` | `MODEL.backbone: deep_conv` was used with non-32px data. | Use 32x32 data or choose a ResNet/BigGAN/StyleGAN-family config. |
| BigGAN-deep spectral-normalization assertion | BigGAN-deep config is missing required SN-compatible settings. | Copy the generator/discriminator SN fields from a known BigGAN-deep StudioGAN config. |
| Multi-Hinge assertion | `MODEL.d_cond_mtd` and `LOSS.adv_loss` are not both `MH`, or TopK was enabled. | Set both to `MH` and disable TopK, or choose another loss/conditioning family. |
| ADA/APA assertion | ADA and APA schedules are both enabled but their initial probability, target, kimg, or interval differ. | Align ADA and APA schedule fields exactly, or enable only one adaptive augmentation path. |
| Invalid `--pre_resizer` or `--post_resizer` | Resize token is not one of StudioGAN's accepted values. | Use `--pre_resizer` in `wo_resize`, `nearest`, `bilinear`, `bicubic`, `lanczos`; use `--post_resizer` in `legacy`, `clean`, `friendly`. |
| `eval_backbone should be in ...` | Unsupported metric backbone token. | Use `InceptionV3_tf`, `InceptionV3_torch`, `ResNet50_torch`, `SwAV_torch`, `DINO_torch`, or `Swin-T_torch`. |
| Metric run tries to download weights or fails offline | Selected training-time metrics/backbones require pretrained weights or caches. | For infrastructure training smoke tests use `-metrics none`; run full metrics only when cache/network/GPU budget is approved. |
| W&B login, project, service, or network prompt | The training path imports W&B and may try to log online. | Configure W&B according to the runtime policy before launching, use offline/disabled mode if approved, or stop at dry-run helpers. |

## StyleGAN-specific failures

| Symptom or condition | Recovery |
| --- | --- |
| StyleGAN2/3 with non-`Auto` activations | Set `MODEL.g_act_fn: Auto` and `MODEL.d_act_fn: Auto`. |
| StyleGAN2/3 with spectral normalization | Disable `MODEL.apply_g_sn` and `MODEL.apply_d_sn`. |
| StyleGAN3 missing `STYLEGAN.stylegan3_cfg` | Choose `stylegan3-t` or `stylegan3-r`; for `stylegan3-r`, set `STYLEGAN.blur_init_sigma`. |
| StyleGAN EMA assertion | Use `STYLEGAN.g_ema_kimg` and `STYLEGAN.g_ema_rampup`; leave non-StyleGAN `MODEL.g_ema_decay` and `MODEL.g_ema_start` as `N/A`. |
| `d_epilogue_mbstd_group_size` too large | Ensure `STYLEGAN.d_epilogue_mbstd_group_size <= OPTIMIZATION.batch_size / world_size`. |
| StyleGAN rejects interpolation, SeFa, synchronized BN, batch/standing stats, FreezeD, or Langevin/DDLS combinations | Remove those flags. Use StyleGAN-compatible training, then route qualitative checkpoint use to the sampling sub-skill. |

## Difficult usability cases

### Custom data adapted from a CIFAR config

If a user starts from a CIFAR YAML for a private/custom dataset, do not only change `-data`. Update `DATA.name` to a non-CIFAR name, set `DATA.img_size`, set `DATA.num_classes`, check conditioning methods, run the dataset checker, and validate the config with the intended GPU count. Otherwise StudioGAN may follow CIFAR download/cache behavior or train with incorrect class semantics.

### Infrastructure smoke run without metric/cache readiness

If CUDA and the config need a quick sanity check but metric weights, reference data, or W&B credentials are not ready, build a command with `-metrics none`, minimal `--save_freq`, and the planned GPU topology. Report that this proves command/config wiring only, not model quality or published metric values.
