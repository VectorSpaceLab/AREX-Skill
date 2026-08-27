# COVID 2D API reference

This branch exposes a small set of public entry points that are useful for routing and smoke checks.

| Symbol | Role | Inputs | Outputs | Notes |
| --- | --- | --- | --- | --- |
| `lib.medloaders.COVIDxdataset.COVIDxDataset(mode, n_classes=3, dataset_path='./datasets', dim=(224, 224))` | 3-class chest X-ray dataset | `mode` is `train` or `val`; manifests are fixed in source | `(image_tensor, label_tensor)` | Labels map `pneumonia`, `normal`, `COVID-19` to `0/1/2`; source has a `__getitem__` / `load_image` keyword mismatch |
| `lib.medloaders.covid_ct_dataset.CovidCTDataset(mode, root_dir, txt_COVID, txt_NonCOVID, transform=None)` | 2-class chest CT dataset | root directory plus class-specific text files | `(image_tensor, label_tensor)` | `transform` argument is currently ignored; class order defines labels `0/1` |
| `lib.medzoo.create_model(args)` | Model factory | `args.model`, `args.classes`, `args.inChannels`, `args.lr`, `args.opt`, `args.dim` | `(model, optimizer)` | `COVIDNET1`, `COVIDNET2`, and `CNN` are the COVID routes |
| `lib.medzoo.COVIDNet(model='small', n_classes=3)` | COVIDNet branch | `model` is `small` or `large` | `nn.Module` | Constructor currently references `pepx` instead of `PEPX`; classifier head assumes 224x224-style inputs |
| `lib.medzoo.CNN(classes, model='resnet18')` | torchvision wrapper | `classes` integer, backbone name | `nn.Module` | Uses `pretrained=True`; do not rely on network downloads in smoke runs |
| `lib.train.train_covid.train(args, model, trainloader, optimizer, epoch, writer)` | Training loop | batched tensors from a `DataLoader` | `MetricTracker` | Uses `CrossEntropyLoss`; updates writer and terminal summaries |
| `lib.train.train_covid.validation(args, model, testloader, epoch, writer)` | Validation loop | batched tensors from a `DataLoader` | `(MetricTracker, confusion_matrix)` | Builds `classes x classes` confusion matrix |
| `lib.utils.covid_utils.accuracy(output, target)` | Accuracy helper | logits `[N, C]`, integer targets `[N]` | `(correct, total, acc)` | Expects aligned batch sizes |
| `lib.utils.covid_utils.MetricTracker(*keys, writer=None, mode='/')` | Metric accumulator | metric names plus optional writer | tracker object | Averages by iteration count, not by sample count |
| `lib.utils.covid_utils.read_txt(txt_path)` | Text-file reader | plain text path | list of stripped lines | Used by `CovidCTDataset` |

## Safe usage notes

- Keep 2D image tensors at 3 channels.
- Keep class counts aligned with the chosen branch.
- Prefer the bundled smoke script before any real dataset run.
- Treat the known source caveats as blockers until they are fixed or wrapped.
