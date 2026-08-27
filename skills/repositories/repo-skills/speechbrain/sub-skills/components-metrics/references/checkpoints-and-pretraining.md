# Checkpoints and pretrained parameter loading

SpeechBrain distinguishes local experiment checkpointing from pretrained model file collection/loading.

## Verified signatures

```python
speechbrain.utils.checkpoints.Checkpointer(checkpoints_dir, recoverables=None, custom_load_hooks=None, custom_save_hooks=None, allow_partial_load=False)
Checkpointer.recover_if_possible(importance_key=None, max_key=None, min_key=None, ckpt_predicate=None)
Checkpointer.save_and_keep_only(meta={}, end_of_epoch=True, name=None, num_to_keep=1, keep_recent=True, importance_keys=[], max_keys=[], min_keys=[], ckpt_predicate=None, verbosity=20)

speechbrain.utils.parameter_transfer.Pretrainer(collect_in=None, loadables=None, paths=None, custom_hooks=None, conditions=None)
Pretrainer.collect_files(default_source=None, local_strategy=LocalStrategy.SYMLINK, fetch_config=FetchConfig(...))
Pretrainer.load_collected()
```

## `Checkpointer`: experiment state

Use `Checkpointer` for training state owned by an experiment output folder:

```python
from speechbrain.utils.checkpoints import Checkpointer

checkpointer = Checkpointer(
    checkpoints_dir="results/exp/save",
    recoverables={"model": model, "optimizer": optimizer},
)
checkpointer.recover_if_possible()
# training loop
checkpointer.save_and_keep_only(meta={"valid_loss": loss}, min_keys=["valid_loss"])
```

`recoverables` maps names to modules/optimizers/objects with registered hooks. Checkpoints are directories containing parameter files and metadata.

## `Pretrainer`: pretrained file collection/loading

Use `Pretrainer` for loading known pretrained files into modules:

```python
from speechbrain.utils.parameter_transfer import Pretrainer

pretrainer = Pretrainer(
    collect_in="pretrained_models/my-model",
    loadables={"model": model},
    paths={"model": "model.ckpt"},
)
pretrainer.collect_files(default_source="local-or-hf-source")
pretrainer.load_collected()
```

Pretrained inference classes use this pattern internally from hparams.

## Compatibility and renamed keys

SpeechBrain checkpoint code includes compatibility handling for selected renamed state-dict keys. If recovery fails:

- Read the exact missing/unexpected keys.
- Decide whether `allow_partial_load=True` is acceptable for the task.
- Confirm model architecture and hparams match the checkpoint.
- Do not suppress strict-load errors unless the user accepts the resulting partially loaded model.

## Checkpoint troubleshooting checklist

- Are paths relative to the active working directory or output folder as intended?
- Do checkpoint names in hparams match `recoverables` / `loadables` keys?
- Is the checkpoint from a compatible SpeechBrain version/model architecture?
- Is the target device CPU/GPU compatible with the saved tensors?
- Are DDP ranks writing one checkpoint or multiple competing checkpoints?
