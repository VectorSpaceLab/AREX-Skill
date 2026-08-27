# Optional dependencies

Use only the packages needed for the selected workflow. The core package needs `torch>=2.2,<3` and `packaging`; everything below is workflow-specific or optional.

## By area

| Area | Packages | Typical use |
| --- | --- | --- |
| Advanced metrics | `scikit-learn` | ROC AUC, ROC curve, precision-recall curve, average precision, classification report, Matthews/Cohen/F-beta style metrics, clustering metrics, and several regression helpers. |
| Scientific metrics | `scipy` | FID, KL/JS divergence, correlation metrics, and other helpers that call `scipy.stats` or `scipy.linalg`. |
| Vision metrics | `torchvision` | Default Inception/FID feature extractors and object-detection mAP helpers. |
| Fairness metrics | `fairlearn` | Accuracy difference and demographic parity metrics. |
| NLP metrics | `nltk`, `filelock` | BLEU comparison fixtures and ROUGE/NLTK-based test helpers. |
| GPU info | `pynvml<12` | `GpuInfo` and GPU memory/utilization reporting. A real NVIDIA GPU is still required for the metric to be meaningful. |
| Progress and tracking | `tqdm`, `tensorboardX`, `tensorboard` | `ProgressBar`, TensorBoard logging, and notebook/example logging recipes. |
| Plotting and summaries | `matplotlib`, `pandas` | Scheduler previews, LR-finder plots, and profiler summaries. |
| Experiment tracking | `clearml`, `mlflow`, `neptune-client`, `polyaxon`, `wandb`, `visdom` | Logger integrations around experiment tracking and remote services. |
| Distributed backends | `horovod`, `torch_xla`, `apex` | Horovod, TPU/XLA, and legacy AMP branches. |
| Example families | `fire`, `gymnasium`, `transformers`, `datasets`, `ray[tune]`, `brevitas` | Example CLIs and the MNIST/CIFAR10/RL/Transformer/QAT recipes. |

## Practical guidance

- A CPU-only environment can cover the core engine, handler, metric, and serial distributed paths.
- Install optional packages only when the chosen route or verification case needs them.
- Do not install the experiment-tracking packages unless you are working on those integrations or a test specifically exercises them.
