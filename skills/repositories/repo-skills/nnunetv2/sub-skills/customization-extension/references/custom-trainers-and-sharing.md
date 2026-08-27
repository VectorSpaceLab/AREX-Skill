# Custom Trainers and Sharing

Custom trainers are the most common nnU-Net v2 extension point. They are also the easiest way to make a checkpoint non-portable if the trainer class is not available where inference or continued training runs.

## When to write a trainer

Write a subclass of `nnUNetTrainer` when changing:

- Loss functions or class/region weighting.
- Patch sampling or oversampling logic.
- Data augmentation transforms.
- Optimizer, learning-rate schedule, or training length.
- Validation/export behavior.
- Network construction for a quick custom architecture experiment.

Do not write a trainer just to choose folds, resume training, run validation, or select built-in variants; route those tasks to `training-configuration`.

## Minimal implementation pattern

Start from a built-in variant closest to the change. Keep the subclass small and preserve nnU-Net contracts.

Common override targets:

- `configure_optimizers()` for optimizer and scheduler changes.
- Data augmentation setup methods for transform changes.
- Loss construction methods for training objective changes.
- `build_network_architecture(...)` for quick architecture changes.
- Epoch/iteration class attributes for training length variants.

Trainer class rules:

- The class name is the public identifier. Use a stable, unique name.
- The class must inherit from `nnUNetTrainer` directly or indirectly.
- Keep imports available in every environment that will load the checkpoint.
- If overriding `build_network_architecture`, match the current base-class signature and return a network without output softmax/sigmoid.
- If the network cannot support deep supervision, derive from or mirror `nnUNetTrainerNoDeepSupervision` behavior.

## Selecting a custom trainer

Training selects the class by name in the trainer position of the training command, for example:

```bash
nnUNetv2_train DATASET001_Example 3d_fullres 0 -tr MyCustomTrainer
```

Keep all other routine training choices in `training-configuration`. This sub-skill only covers making `MyCustomTrainer` exist and remain discoverable.

## How checkpoint loading finds trainers

Checkpoints store `trainer_name`. When inference or continued training loads a checkpoint, nnU-Net resolves that name as follows:

1. Search built-in/importable trainer classes below `nnunetv2.training.nnUNetTrainer`.
2. If not found and `nnUNet_extTrainer` is set, split it on the OS path separator and recursively search each external directory.
3. Assert the found class inherits from `nnUNetTrainer`.
4. Fail if no class is found or if the module import fails because a dependency is missing.

`nnUNet_extTrainer` should point to the parent directory that makes your package importable. Example layout:

```text
custom_trainers_root/
└── my_trainers/
    ├── __init__.py
    └── trainer.py  # defines class MyCustomTrainer(nnUNetTrainer)
```

Linux/macOS:

```bash
export nnUNet_extTrainer="/path/to/custom_trainers_root"
```

Windows PowerShell:

```powershell
$Env:nnUNet_extTrainer = "C:/path/to/custom_trainers_root"
```

Multiple directories are allowed:

```bash
export nnUNet_extTrainer="/path/to/custom_trainers_root:/path/to/other_trainers"
```

On Windows use `;` instead of `:`.

## Sharing strategy choices

Choose one distribution strategy before publishing a custom-trainer checkpoint.

### Rename checkpoint trainer to a built-in trainer

Use when the custom trainer did not change network topology or inference-relevant behavior, and you have verified predictions after renaming.

Advantages:

- Lowest-friction inference for users with stock nnU-Net.
- Useful when trainer implementation cannot be shared.

Risks:

- Reproducibility is reduced because the checkpoint no longer points to the true trainer.
- Unsafe if `build_network_architecture` or other inference-relevant behavior changed.

### Ship trainer source and use `nnUNet_extTrainer`

Use when distributing a checkpoint whose trainer must remain transparent and importable, especially when architecture or procedure changed.

Advantages:

- No fork required.
- Checkpoint metadata remains honest.
- Users can run inference or continue training if dependencies are satisfied.

Requirements:

- Provide trainer files and dependency instructions.
- Tell users which directory to put in `nnUNet_extTrainer`.
- Verify the class can be found with the bundled helper before running inference.

### Editable install plus source-tree placement

Use only for development setups where users intentionally modify nnU-Net source code.

Risks:

- Brittle across reinstallations and nnU-Net versions.
- Users must copy files into the right source-tree location.
- Harder to support than `nnUNet_extTrainer` for ordinary inference distribution.

### Maintain a fork

Use when users need a complete stable development environment, a challenge submission requires source release, or many coordinated source changes must travel together.

Advantages:

- Pins exact code behavior if users install the forked version.
- Good for training new models with the same custom stack.

Risks:

- The fork can drift from upstream.
- Users must install a different nnU-Net distribution.

## Shipping without forking

For a practical no-fork package:

1. Put custom trainer classes in a small importable Python package or directory tree.
2. Keep class names stable and unique.
3. Avoid relative imports that only work from your development checkout.
4. Include any custom architecture/loss/helper code imported by the trainer.
5. Document the required nnU-Net version and dependency versions.
6. Instruct users to set `nnUNet_extTrainer` to the parent directory of the package.
7. Ask users to run:
   ```bash
   python sub-skills/customization-extension/scripts/list_available_nnunet_classes.py --kind trainer --external-trainer-dir /path/to/custom_trainers_root
   ```
8. Then route inference command details to `inference-evaluation`.

## Compatibility checklist

Before sharing a checkpoint, verify:

- The checkpoint's `trainer_name` matches the class name you ship.
- The trainer inherits from `nnUNetTrainer`.
- All imports succeed in a clean environment.
- If the trainer builds a custom network, the target environment has the same architecture code.
- The current `build_network_architecture` signature is supported.
- The plans identifier and configuration used for training are available with the checkpoint.
- Any custom image reader/writer, normalization, label manager, or preprocessor used during planning/inference is also available.

## Hand-off boundaries

- After the class is importable and selected, routine training launch details belong to `training-configuration`.
- After a checkpoint exists, prediction/evaluation/model installation details belong to `inference-evaluation`.
- Dataset label/region/ignore-label metadata belongs to `data-preparation` unless custom trainer code must preserve the behavior.
