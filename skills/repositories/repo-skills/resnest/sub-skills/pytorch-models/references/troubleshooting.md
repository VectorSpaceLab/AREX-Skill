# PyTorch Troubleshooting

Use this table when the PyTorch path fails.

| Symptom | Likely cause | What to do |
|---|---|---|
| `ModuleNotFoundError: fvcore` or `iopath` while importing `resnest.torch` or the training utilities | Package dependencies are missing | Install the package requirements for the PyTorch path before retrying. `fvcore` and `iopath` are required for the registry and utility helpers. |
| `ModuleNotFoundError: torchvision` when using datasets, transforms, or validation helpers | Vision runtime dependency is missing or mismatched | Install a torchvision build compatible with the installed torch version. |
| `KeyError` / registry miss for `resnest50_fast_...` when using `get_model()` | Fast ablation factories are direct exports, not registry names | Call the direct factory from `resnest.torch` instead of `get_model()`. |
| `KeyError` / registry miss for a typoed model name | Name is not registered | Use one of the canonical names from the API reference. |
| `pretrained=True` fails offline or tries to download unexpectedly | Weights are fetched through PyTorch Hub cache behavior | Retry with `pretrained=False`, or pre-populate the PyTorch Hub cache before running the helper. |
| Pretrained load fails with a classifier-head mismatch | The pretrained weights are ImageNet-1000 weights | Keep `classes=1000` when loading pretrained weights, or build the model with `pretrained=False` and fine-tune a custom head. |
| Download completes but the hash check fails | Partial or corrupted weight file | Delete the corrupted cached file and retry, or stay offline with `pretrained=False`. |
| `root='~/.encoding/models'` does not redirect pretrained downloads | The current factory code keeps `root` in the signature but does not pass it to the downloader | Do not rely on `root` for weight placement in this release. Use the PyTorch Hub cache or local cache management instead. |
| `NotImplementedError` when enabling DropBlock | `DropBlock2D` is a placeholder in this build | Keep `dropblock_prob=0.0` unless you provide an alternate implementation. |
| `RuntimeError: expected more than 1 value per channel` during training or tiny-layer smoke | BatchNorm is being executed in an unsuitable training configuration | Use `eval()` for smoke tests, increase the batch size, or freeze batchnorm for the affected check. |
| `CUDA` / `NCCL` failures in the training launcher | The training path assumes a CUDA distributed setup | Use the CPU smoke helper for inspection-only work; treat the training launcher as GPU-oriented. |
| `ImageNet` folder not found | Data is not laid out as raw `train/` and `val/` class folders | Populate the expected raw-image tree before running validation or training. The dataset wrapper does not download the dataset. |
| `prepare_imagenet` style extraction errors | Wrong tar names, bad checksums, or insufficient disk | Verify the official tar names and SHA1 values, and ensure you have enough space before extracting. |
| `rfconv` import errors | Rectified-convolution path was selected | Leave `rectified_conv=False` for the default ResNeSt path, or install the optional dependency if you need that experimental branch. |
| `SplAtConv2d` shape mismatch in custom experiments | `in_channels`, `channels`, `groups`, or `radix` are incompatible | Keep the channel dimensions divisible by `groups * radix` and start from the tiny smoke defaults before scaling up. |

## Quick recovery pattern

When a caller asks for an offline-safe answer, prefer this order:

1. retry with `pretrained=False`;
2. use the bundled tiny inference script;
3. only then investigate cache, data, or launcher issues.

That order avoids most unnecessary downloads and the most common classifier-shape mistakes.
