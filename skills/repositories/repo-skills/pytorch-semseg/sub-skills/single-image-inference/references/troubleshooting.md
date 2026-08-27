# Single-Image Inference Troubleshooting

Use this matrix when `test.py` command construction or one-image inference fails. Prefer fixing the smallest local issue first; route training/config/model-registry questions to the owning sub-skills.

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `AttributeError: module 'scipy.misc' has no attribute 'imread'`, `imresize`, or `imsave` | Modern SciPy removed the image helpers used by the original script. | Run in a legacy image-helper environment or patch `test.py` to use Pillow/imageio/skimage. Preserve RGB `uint8` reads, bicubic/bilinear image resize, nearest-neighbor class-map resize, and `[0, 1]` color output conversion to `uint8` before saving. |
| Parser/help prints `Failed to import pydensecrf, CRF post-processing will not work` | `pydensecrf` is optional and was not installed or could not be imported. | Use `--no-dcrf` for normal inference. Install/debug `pydensecrf` only when DenseCRF is explicitly required. |
| `--dcrf` run fails with a `NameError` or similar around `dcrf.DenseCRF2D` | The source script catches the import failure but still later references `dcrf` when `--dcrf` is selected. | Disable DenseCRF or install a compatible `pydensecrf`; if adapting, guard the DenseCRF block with an explicit availability check. |
| DenseCRF output is poor, all one class, or emits NaN/inf warnings | The script builds unary energies as `-np.log(outputs)` and assumes positive probability-like model outputs. Raw logits or zero/negative values break that assumption. | If adapting DenseCRF, apply softmax over classes, clamp probabilities to a small positive minimum, then compute `-log(probability)`. Keep shapes contiguous as expected by `DenseCRF2D`. |
| Checkpoint filename has no `_` and the builder warns architecture parsing will fail | The source script computes `model_file_name[:model_file_name.find("_")]`; with no underscore, `find` returns `-1` and the parsed id is the basename without its final character. | Rename or symlink the checkpoint to `<arch>_<description>.pkl`, for example `fcn8s_pascal_best_model.pkl` or `icnetBN_cityscapes_best_model.pkl`. |
| Unknown model id parsed from checkpoint basename | The filename prefix before `_` is not a registered architecture id, or case/spelling differs. | Use one of `fcn32s`, `fcn16s`, `fcn8s`, `unet`, `segnet`, `pspnet`, `icnet`, `icnetBN`, `linknet`, `frrnA`, or `frrnB`. Route model registry questions to `model-zoo-and-apis`. |
| `torch.load(...)["model_state"]` fails with `KeyError` | The file is not a pytorch-semseg training checkpoint or stores a raw state dict under different keys. | Inspect the checkpoint metadata out of band. Adapt the load line to the actual key only if you know the checkpoint format. Checkpoint production belongs to `training-and-evaluation`. |
| `model.load_state_dict` reports missing/unexpected keys | Architecture id, dataset class count, or checkpoint wrapper prefixes do not match. | Confirm the filename architecture, dataset key, and number of classes match training. The source already applies `convert_state_dict` for common `DataParallel` prefixes. |
| Input image path is missing or unreadable | `--img_path` points to a non-file or a path relative to the wrong working directory. | Run the command builder from the intended directory, pass a correct image path, and verify the file exists before real inference. |
| Checkpoint path is missing or unreadable | `--model_path` points to a non-file or a path relative to the wrong working directory. | Fix the path before running real inference. The builder only checks metadata; it does not load the checkpoint. |
| Output does not save or parent path fails | The output parent directory does not exist, `--out_path` is a directory, or permissions are insufficient. | Create the output parent before running. Prefer a `.png` filename because DenseCRF path derivation slices the last four characters of `--out_path`. |
| DenseCRF extra output path looks odd | The source script derives `dcrf_path = args.out_path[:-4] + "_drf.png"`. | Use a `.png` output path and expect the DenseCRF file suffix `_drf.png`. Adapt the path logic if you need a different convention. |
| Output colors look wrong even though inference runs | Dataset key does not match the checkpoint training dataset, so `decode_segmap` used a wrong palette and possibly wrong class count. | Re-run with the dataset key used for training. If you need raw class ids, save `pred` before `decode_segmap` instead of relying on the color output. |
| `mit_sceneparsing_benchmark` fails at output decoding | The registry key exists, but the inspected loader does not expose a compatible `decode_segmap` method. | Do not use unmodified `test.py` for this key. Add a dataset-specific decode function or route dataset adaptation to `data-and-configs`. |
| `cityscapes`, `nyuv2`, `sunrgbd`, or `vistas` fails while constructing the loader with `root=None` | Some loaders are more dataset-bound than the generic `test_mode=True` call and may still touch dataset directories/config files. | Patch loader test mode for palette-only inference, or construct only the palette/class-count data needed by `test.py`. Keep dataset layout work in `data-and-configs`. |
| CPU run is too slow or the process is killed | Large image/model combinations can consume substantial RAM/compute, especially PSPNet/ICNet-style models. | Use a smaller input image, run on a compatible GPU environment, or choose a lighter architecture/checkpoint. |
| CUDA out of memory | `test.py` automatically uses CUDA when available; the selected image/model is too large. | Reduce image size before inference, free GPU memory, use CPU by masking CUDA in the environment, or use a smaller model. |
| PSPNet/ICNet prediction shape surprises you | For `pspnet`, `icnet`, and `icnetBN`, the source resizes inputs to odd dimensions and resizes predictions back to original size. | Treat this as expected behavior. For exact-size experiments, document the odd-size step and use nearest-neighbor interpolation for class maps when adapting. |
| Results change when toggling `--img_norm` | The flag changes preprocessing after mean subtraction by dividing by `255.0` or not. | Match the preprocessing used during training. If unknown, try the setting recorded in the training config or checkpoint notes; config provenance belongs to `data-and-configs`/`training-and-evaluation`. |
| Running `test.py --help` fails before showing help because of protobuf/caffe imports | Importing model modules can load generated protobuf code incompatible with newer protobuf packages. | Use a compatible protobuf version or the pure-Python protobuf implementation workaround before relying on CLI help or inference. Cross-cutting environment setup belongs to the root skill/environment reference. |

## Fast checks with the bundled builder

```bash
python scripts/build_inference_command.py --help
```

For a known ICNet-BN naming pattern:

```bash
python scripts/build_inference_command.py \
  --model_path checkpoints/icnetBN_cityscapes_best_model.pkl \
  --dataset cityscapes \
  --img_path examples/city.jpg \
  --out_path outputs/city_mask.png \
  --img_norm \
  --no-dcrf
```

For a deliberate bad filename check:

```bash
python scripts/build_inference_command.py \
  --model_path checkpoints/icnetBNcityscapes.pkl \
  --dataset cityscapes \
  --img_path examples/city.jpg \
  --out_path outputs/city_mask.png
```

The second command should warn that source architecture parsing will not recover `icnetBN` because there is no underscore.
