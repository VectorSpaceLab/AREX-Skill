# Model and Trainer API reference

## Trainer

Verified live constructor:

```text
Trainer(model: torch.nn.Module, checkpoint_path: Optional[str] = None,
        metrics: Optional[List[str]] = None, device: Optional[str] = None,
        enable_logging: bool = True, output_path: Optional[str] = None,
        exp_name: Optional[str] = None)
```

`device=None` selects CUDA when available, else CPU; pass an explicit device for
reproducibility. `train(train_dataloader, val_dataloader=None,
test_dataloader=None, epochs=5, optimizer_class=torch.optim.Adam,
optimizer_params=None, steps_per_epoch=None, evaluation_steps=1,
weight_decay=0.0, max_grad_norm=None, monitor=None, monitor_criterion="max",
load_best_model_at_last=True, patience=None)` expects model batches whose
forward result contains `loss`. `evaluate(dataloader)` uses `model.mode` to
select binary/multiclass/multilabel/regression metrics and returns a score
mapping plus loss. `inference(dataloader, additional_outputs=None,
return_patient_ids=False)` returns true labels, probabilities, mean loss, and
optional outputs/IDs. `save_ckpt` stores `state_dict`; `load_ckpt` loads it
with the trainer device.

## Model contract

Most supervised models expose a mode and return a dictionary containing at least
`loss`, `y_true`, and `y_prob` during evaluation. Inputs are keyword-expanded
from a collated task sample, so names and nested shapes must match the model.
Token processors generally provide a vocabulary size and discrete indices;
continuous processors provide numeric tensors. Inspect one batch and the
selected constructor before training.

## Monitoring

Use a metric that exists for the model mode, such as `pr_auc`/`roc_auc` for
binary outputs or an appropriate multilabel score. `monitor_criterion="max"`
keeps larger scores; use `"min"` only for a loss-like measure. If no validation
loader is supplied, do not claim a best checkpoint based on validation.
