# Cross-Cutting MUNIT Troubleshooting

## Start With The Symptom

| Symptom | Likely owner | First action |
| --- | --- | --- |
| `ImportError` for `torch`, `torchvision`, `yaml`, `tensorboardX`, or `load_lua` | `sub-skills/environment-and-setup/` | Run the environment checker and compare against the legacy runtime reference. |
| CUDA unavailable, CUDA hang, unsupported GPU, or modern driver/runtime mismatch | `sub-skills/environment-and-setup/` | Treat as a runtime/backend block for real training or inference. |
| Missing `trainA`, `trainB`, `testA`, `testB`, zero images, or bad list-file paths | `sub-skills/data-and-configuration/` | Run the dataset inspector and validate config paths. |
| `display_size` index errors before the training loop starts | `sub-skills/data-and-configuration/` then `sub-skills/training/` | Lower `display_size` or add images to every split. |
| `--trainer UNIT` fails with missing loss keys | `sub-skills/training/` and `sub-skills/model-internals/` | Add UNIT KL weights and review UNIT semantics. |
| Resume cannot find checkpoint files | `sub-skills/training/` | Check `<output_path>/outputs/<config-stem>/checkpoints/` for generator, discriminator, and optimizer files. |
| Missing pretrained model or checkpoint shape mismatch during inference | `sub-skills/inference-and-evaluation/` then `sub-skills/model-internals/` | Confirm asset path and architecture/style-dimension compatibility. |
| Wrong translation direction or style image appears mismatched | `sub-skills/inference-and-evaluation/` | Verify `--a2b` and target-domain style image semantics. |
| AdaIN assertion or unsupported norm/activation/padding error | `sub-skills/model-internals/` | Inspect architecture/config compatibility and source assertions. |

## Legacy Runtime Warnings

A modern PyTorch environment can pass generic `import torch` checks while failing MUNIT-specific imports. The original utility imports `torch.utils.serialization.load_lua`; this is absent from modern PyTorch. The original inference code also uses legacy `Variable(..., volatile=True)` and older checkpoint conversion assumptions. Do not claim a modern runtime is supported until the code has been ported and verified.

## Asset Boundaries

This skill does not include or auto-fetch:

- official pretrained generator checkpoints;
- full pix2pix/CycleGAN-style datasets;
- VGG `.t7`/`.weight` files;
- Inception classifier checkpoints for IS/CIS metrics.

Ask the user for local paths or explicit download approval. Keep network, credentials, and large artifacts out of quick checks.

## Safe Helper Pattern

All bundled helper scripts are dry-run or static-inspection helpers. They are designed to catch mistakes before an expensive legacy CUDA job:

```bash
python sub-skills/environment-and-setup/scripts/check_munit_environment.py --repo-root /path/to/user/munit-checkout
python sub-skills/data-and-configuration/scripts/validate_munit_config.py --config /path/to/config.yaml --repo-root /path/to/user/munit-checkout
python sub-skills/data-and-configuration/scripts/inspect_munit_dataset.py --config /path/to/config.yaml --repo-root /path/to/user/munit-checkout
python sub-skills/training/scripts/munit_train_command.py --config configs/demo_edges2handbags_folder.yaml --repo-root /path/to/user/munit-checkout
```

Run the generated `python train.py`, `python test.py`, or `python test_batch.py` commands only after the user approves real execution in a compatible runtime.
