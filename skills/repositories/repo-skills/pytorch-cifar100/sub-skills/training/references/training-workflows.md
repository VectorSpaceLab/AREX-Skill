# Training Workflows

## Purpose

Use this reference when you need to construct, explain, or resume the CIFAR-100 training workflow behind `train.py`.
It was distilled from the repository training entry point, helper utilities, global settings, README usage notes, and the learning-rate finder.

## Quick command

```bash
python train.py -net <name> [-gpu] [-b B] [-warm WARM] [-lr LR] [-resume]
```

## CLI flags and defaults

| Flag | Default | Meaning |
| --- | --- | --- |
| `-net` | required | Selects the model family key passed to the network factory. |
| `-gpu` | off | Moves the model, images, and labels to CUDA. |
| `-b` | `128` | Batch size for both training and test loaders. |
| `-warm` | `1` | Number of warmup epochs. Warmup runs per batch. |
| `-lr` | `0.1` | Initial SGD learning rate. |
| `-resume` | off | Resume from the most recent non-empty checkpoint folder for that net. |

## Runtime flow

1. Parse the CLI.
2. Resolve the network with `get_network(args)`.
3. Build training and test loaders from torchvision CIFAR-100.
4. Create the loss, SGD optimizer, MultiStepLR scheduler, and `WarmUpLR` helper.
5. Choose a checkpoint folder:
   - fresh run: `checkpoint/<net>/<TIME_NOW>/`
   - resume: most recent non-empty `checkpoint/<net>/<timestamp>/` folder
6. Create a TensorBoard writer under `runs/<net>/<TIME_NOW>/`.
7. Add a graph using a dummy `(1, 3, 32, 32)` tensor.
8. Train for `EPOCH = 200` epochs.
9. Save regular checkpoints every `SAVE_EPOCH = 10` epochs.
10. Save best checkpoints only after the second milestone once accuracy improves.

## Training details that matter

- Optimizer: `SGD(net.parameters(), lr=args.lr, momentum=0.9, weight_decay=5e-4)`.
- Scheduler: `MultiStepLR(milestones=[60, 120, 160], gamma=0.2)`.
- Warmup: `WarmUpLR(optimizer, iter_per_epoch * args.warm)`.
- Warmup steps happen during each training batch while `epoch <= args.warm`.
- Scheduler steps at the start of epochs only when `epoch > args.warm`.
- The best checkpoint name is `checkpoint/<net>/<timestamp>/<net>-<epoch>-best.pth`.
- The regular checkpoint name is `checkpoint/<net>/<timestamp>/<net>-<epoch>-regular.pth`.
- Resume first loads the best checkpoint, if present, only to recover the current best accuracy baseline.
  It then loads the most recent weight file to continue training from the latest epoch.
- If the resume folder has no usable weights, the code raises instead of guessing.
- TensorBoard logging always uses a fresh `runs/<net>/<TIME_NOW>/` folder, even when resuming.

## TensorBoard

Launch TensorBoard against the shared log root:

```bash
tensorboard --logdir runs --host localhost --port 6006
```

Each run gets its own timestamped subfolder, so compare the folders if you are tracking a resume sequence.

## Data side effects

- Both loaders use torchvision CIFAR-100 with `download=True` and `root='./data'`.
- The first run can create or update the local `./data` tree.
- Training uses random crop, horizontal flip, and 15-degree rotation.
- Both splits normalize with the training mean and std from `conf/global_settings.py`.
- The test loader is also shuffled in the current code.

## Safe planning

Use the bundled command builder before launching a long run:

```bash
python scripts/build_train_command.py --net vgg16 --gpu --batch-size 128 --warm 1 --lr 0.1 --explain
```

For a quick parser inspection, use `python train.py -h`. Do not use a full training run as a quick sanity check.

## Reproducibility notes

- No seed is fixed in the training entry point.
- Random crop, flip, rotation, and shuffled loading make runs stochastic.
- The timestamped log and checkpoint folders depend on the wall clock at launch.
- If you want a clean fresh run, remove or rename older checkpoint folders for that net before starting.

## Supported model keys

The training command accepts any key implemented by the network factory in `utils.py`.
If the README and code disagree, trust the factory list and the bundled command builder rather than the older README table.
For example, `densenet169` is accepted by the code even though the older README table does not list it.
