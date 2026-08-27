# pytorch-semseg troubleshooting

Read this for cross-cutting install/import/runtime issues before drilling into a workflow-specific sub-skill.

## First checks

Run the bundled environment probe from an environment where `ptsemseg` is importable:

```bash
python scripts/check_environment.py
python scripts/check_environment.py --smoke
```

The smoke path uses FRRN rather than FCN/SegNet so it does not download VGG weights.

## Import and dependency failures

| Symptom | Likely cause | What to do next |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'ptsemseg'` | The repository has no packaging metadata in this snapshot, so an editable install may not exist. | Run from a source tree that contains `ptsemseg`, add the source tree to `PYTHONPATH`, or install a release that provides the same import package. Then rerun `scripts/check_environment.py`. |
| `Descriptors cannot be created directly` during `ptsemseg.models` import | Incompatible modern protobuf with generated `caffe_pb2.py`. | Use `protobuf<3.21`, regenerate protobuf files, or use the slower pure-Python protobuf implementation workaround. |
| `ModuleNotFoundError: No module named 'tensorboardX'` | Training script imports TensorBoardX at module import time. | Install `tensorboardX` before using training helpers or the original training entry point. |
| `Failed to import pydensecrf` | Optional DenseCRF dependency is missing. | Ignore it for normal inference with `--no-dcrf`; install/verify `pydensecrf` only when CRF post-processing is explicitly required. |
| `AttributeError` on `scipy.misc.imread`, `imresize`, `imsave`, or `toimage` | Modern SciPy removed image helpers used by the original single-image script and Pascal SBD preprocessing. | Use a legacy-compatible environment or adapt those calls to Pillow/imageio in the workflow-specific script before a real run. |

## Data and config failures

Use `sub-skills/data-and-configs/scripts/validate_config.py` before any dataset-bound run.

Common issues:

- Example configs may contain machine-specific absolute dataset paths. Replace them before running.
- Pascal augmented training uses SBD/pre-encoded behavior; make `sbd_path` explicit and review whether the stock entry point forwards it for the workflow you are adapting.
- `img_rows: same` and `img_cols: same` are not universally safe. Let the config sub-skill decide whether the selected loader supports that path.
- The original scripts use legacy `yaml.load(fp)`; adapted scripts should use `yaml.safe_load(fp)`.

## Model and checkpoint failures

Use `sub-skills/model-zoo-and-apis/references/troubleshooting.md` for detailed API issues.

Fast triage:

- Unknown model ids are often capitalization or registry spelling errors. Valid ids include `fcn32s`, `fcn16s`, `fcn8s`, `unet`, `segnet`, `pspnet`, `icnet`, `icnetBN`, `linknet`, `frrnA`, and `frrnB`.
- For `frrnA`, include `model_type: "A"`; for `frrnB`, include `model_type: "B"`. The shared constructor defaults to B.
- For FCN/SegNet, expect possible VGG weight-cache/network behavior during `get_model`.
- If a checkpoint was saved under `torch.nn.DataParallel`, strip `module.` prefixes with `ptsemseg.utils.convert_state_dict` before loading into a non-parallel model.

## Expensive or side-effecting workflows

Training, validation, and real single-image inference can read datasets/checkpoints, allocate GPU memory, write output masks/logs/checkpoints, and run for a long time. Use the dry-run command builders first:

```bash
python sub-skills/training-and-evaluation/scripts/build_train_command.py --config CONFIG.yml
python sub-skills/training-and-evaluation/scripts/build_validate_command.py --config CONFIG.yml --model-path MODEL.pkl
python sub-skills/single-image-inference/scripts/build_inference_command.py --model-path MODEL.pkl --dataset pascal --img-path image.jpg --out-path mask.png
```

Run the printed command only after the user has approved compute, data access, and writes for the actual target environment.
