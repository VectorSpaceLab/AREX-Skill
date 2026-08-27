# Pretrained Model Registry

TIAToolbox ships a `pretrained_model.yaml` registry with 64 keys. Each registry entry maps a key to a Hugging Face repository id, architecture class plus keyword arguments, IO config class plus keyword arguments, and often a dataset label. Reading the registry is safe; constructing a model with a registry key can download weights when local weights are not supplied.

## Safe Inspection

Use the bundled script when an agent needs to validate keys or summarize model families without importing TIAToolbox or downloading weights:

```bash
python scripts/model_registry_probe.py --summary
python scripts/model_registry_probe.py --list-prefix hovernet
python scripts/model_registry_probe.py --list-prefix resnet34 --show-ioconfig
```

The script reads a local YAML file, prints counts and selected keys, and never calls `get_pretrained_model()`, `fetch_pretrained_weights()`, or Hugging Face APIs.

## Family Summary

- Patch classification backbones appear for Kather100K and PCam datasets, including AlexNet, ResNet, ResNeXt, Wide ResNet, DenseNet, MobileNet, and GoogLeNet variants.
- Semantic segmentation entries include FCN/UNet tissue or BCSS-style models and related IO configs.
- Nucleus detection entries include `mapde-*` and `sccnn-*` families.
- Nucleus instance/multitask entries include `hovernet*`, `hovernetplus-*`, `micronet-*`, and NuClick-style families.
- Image quality or tissue detection entries include KongNet, GrandQC, and EfficientUNet tissue-mask models.
- Many entries share `TIACentre/TIAToolbox_pretrained_weights`; KongNet and GrandQC families use dedicated Hugging Face repositories.

## Registry Entry Shape

A typical entry contains:

```yaml
model-key:
  hf_repo_id: TIACentre/TIAToolbox_pretrained_weights
  architecture:
    class: vanilla.CNNModel
    kwargs:
      backbone: resnet18
      num_classes: 9
  ioconfig:
    class: io_config.IOPatchPredictorConfig
    kwargs:
      patch_input_shape: [224, 224]
      stride_shape: [224, 224]
      input_resolutions: [{"resolution": 0.5, "units": "mpp"}]
  dataset: kather100k
```

Do not copy the whole registry into task plans. Quote only the selected key, family, architecture class, IO config class, and the small IO fields needed to justify a plan.

## Model Selection Heuristics

- Patch classification: choose a `*-kather100k` or `*-pcam` classifier key when the task is patch-level class prediction.
- Feature extraction: choose a backbone accepted by `DeepFeatureExtractor` and output `zarr` for large batches.
- Tissue or semantic segmentation: choose a segmentation key such as `fcn-tissue_mask` when the desired output is dense class labels.
- Nucleus detection: choose a detection key such as `mapde-*` or `sccnn-*` and plan detector thresholds explicitly.
- Nucleus instance segmentation: prefer `MultiTaskSegmentor` with a HoVerNet, HoVerNetPlus, MicroNet, or related multitask key.
- No-download or restricted network: use a custom model object or provide `weights` as a local compatible file; do not rely on a registry key with `weights=None`.

## Case and Typo Handling

Registry keys are exact strings. Some documentation says pretrained arguments are case-insensitive, but the safest plan is to normalize only by checking the registry and then pass the exact key printed by the probe. If no exact key matches:

1. Run `--list-prefix` with the suspected family prefix.
2. Compare hyphen, underscore, and dataset suffix spelling.
3. Avoid silently substituting a different dataset or task family.
4. Ask the user before replacing a missing custom model key.

## License and Network Notes

Pretrained weights can come from external Hugging Face repositories and may have their own licenses or access constraints. When a task requires offline, private, or reproducible execution, document whether the plan uses local weights, a pre-populated model cache, or an allowed network download. The bundled probe does not verify license terms and does not prove weights are cached.
