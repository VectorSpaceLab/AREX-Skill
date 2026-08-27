# Data and Checkpoints

## Purpose

Read this when a DARTS workflow needs CIFAR-10, ImageNet, Penn Treebank, WikiText-2, or a pretrained model file. The generated skill does not bundle datasets or pretrained weights.

## Dataset expectations

| Workflow | Default native `--data` | Expected layout | Acquisition note |
| --- | --- | --- | --- |
| CNN CIFAR-10 search/train/test | `../data` from inside `cnn/` | torchvision-managed CIFAR-10 files under the root | The native scripts pass `download=True`, so torchvision can download CIFAR-10 in a compatible runtime. |
| CNN ImageNet train/test | `../data/imagenet/` from inside `cnn/` | `train/<class>/image...` and `val/<class>/image...` ImageFolder directories | README says ImageNet must be manually downloaded, preferably to SSD. |
| RNN PTB search/train/test | `../data/penn/` from inside `rnn/` | `train.txt`, `valid.txt`, `test.txt` | README points to the AWD-LSTM language-model repo for acquisition instructions. |
| RNN WikiText-2 training | `../data/wikitext-2` from inside `rnn/` | `train.txt`, `valid.txt`, `test.txt` | README uses this folder for the WT2 recipe. |

The checked-out repository only contains empty `.keep` placeholders in the dataset directories. Missing files are expected until the user supplies data or lets the native scripts download CIFAR-10.

## RNN corpus format

The RNN corpus loader reads plain text files. For each line, it splits on whitespace and appends an `<eos>` token. It builds one shared dictionary while tokenizing train, valid, and test in order. A missing split file raises an assertion before training begins.

Minimum PTB/WT2 validation checklist:

```text
<data-root>/train.txt
<data-root>/valid.txt
<data-root>/test.txt
```

Each file should be non-empty UTF-8 text. Do not supply JSONL, CSV, token-id tensors, or nested directories unless you also port `rnn/data.py`.

## Pretrained model files

The README documents three external pretrained artifacts, but they are not part of this skill:

| Model | Native command shape | File expectation | README metric |
| --- | --- | --- | --- |
| CIFAR-10 CNN | `cd cnn && python test.py --auxiliary --model_path cifar10_model.pt` | Raw PyTorch state dict matching `NetworkCIFAR(init_channels=36, layers=20, auxiliary=True, arch=DARTS)` | `2.63%` test error, `3.3M` params. |
| PTB RNN | `cd rnn && python test.py --model_path ptb_model.pt` | Serialized `RNNModel` object loaded with `torch.load` | `55.68` test perplexity, `23M` params. |
| ImageNet CNN | `cd cnn && python test_imagenet.py --auxiliary --model_path imagenet_model.pt` | Checkpoint dictionary with key `state_dict`, matching `NetworkImageNet(init_channels=48, layers=14, auxiliary=True, arch=DARTS)` | `26.7%` top-1 error and `8.7%` top-5 error, `4.7M` params. |

Do not invent results when a checkpoint is absent. Report the planned command, the expected file kind, and the missing artifact.

## Checkpoint behavior by native script

- CNN CIFAR training writes `weights.pt` as a raw model state dict every epoch.
- CNN CIFAR test loads a raw state dict via the repository utility loader.
- ImageNet training writes `checkpoint.pth.tar` and copies `model_best.pth.tar` when top-1 validation improves.
- ImageNet test expects a checkpoint dictionary and reads the `state_dict` key.
- RNN train/search write `model.pt`, `optimizer.pt`, and `misc.pt` under the experiment directory.
- RNN test loads a serialized model object directly from `--model_path`.

Keep these checkpoint formats separate. A raw CNN state dict is not accepted by ImageNet test without wrapping, and an RNN serialized model object is not interchangeable with CNN state dict checkpoints.

## Safe helper use

- Use [scripts/darts_command_builder.py](../scripts/darts_command_builder.py) to print commands and prerequisite notes without running training or downloading data.
- Use [scripts/darts_static_inspector.py](../scripts/darts_static_inspector.py) with `--repo-root` to check whether a local source tree has the expected files and dataset placeholders before a native run.
