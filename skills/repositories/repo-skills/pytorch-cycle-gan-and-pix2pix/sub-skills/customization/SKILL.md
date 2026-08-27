---
name: customization
description: "Add custom models and datasets that match the repo registry,
  templates, and option-injection contracts."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Customization

Use this sub-skill when the task is to add or debug a custom model class, custom dataset class, registry naming, parser defaults, or model/dataset data-key coupling for this repository.

Route elsewhere when the request is really about:

- running a completed custom training, testing, inference, pretrained, CPU/GPU, or DDP command: [`translation-workflows`](../translation-workflows/SKILL.md)
- formatting raw data roots, pairing A/B folders, validating standard layouts, downloading assets, or Cityscapes/HED data preparation: [`data-preparation`](../data-preparation/SKILL.md)
- full new architecture research beyond the registry/template contract: treat as a long-tail gap unless the bundled references below already cover the decision.

## References and helper

- [`references/model-extension.md`](references/model-extension.md): model filename/class contract, `BaseModel` obligations, required lists/methods, checkpoints, and network factory choices.
- [`references/dataset-extension.md`](references/dataset-extension.md): dataset filename/class contract, `BaseDataset` obligations, transforms, data dictionaries, and keys expected by existing models.
- [`references/option-registry.md`](references/option-registry.md): dynamic parser injection order, verified default couplings, and CLI implications.
- [`references/troubleshooting.md`](references/troubleshooting.md): import/class-name, default, device, checkpoint, and data-key failure recovery.
- [`scripts/check_extension_names.py`](scripts/check_extension_names.py): safe import-free name checker for `--kind model|dataset --name <mode>` with optional `--repo-root` file/class text checks.

## Operating order

1. Choose the registry value first: `--model <model>` or `--dataset_mode <mode>`.
2. Use the registry naming contract before writing code: model files are `models/<model>_model.py` with a `<Model>Model` subclass; dataset files are `data/<mode>_dataset.py` with a `<Mode>Dataset` subclass.
3. Put model defaults and model-specific flags in the model class `modify_commandline_options`; put data-layout/channel defaults and dataset-specific flags in the dataset class `modify_commandline_options`.
4. Make the dataset dictionary returned by `__getitem__` match the model's `set_input` keys and tensor channel counts.
5. Validate names with the bundled checker before testing command-line imports. If names pass but training/test commands are needed, route to `translation-workflows`.
