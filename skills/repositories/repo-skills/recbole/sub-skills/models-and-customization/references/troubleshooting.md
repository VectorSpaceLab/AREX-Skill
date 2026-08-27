# Model And Customization Troubleshooting

Start from the symptom, then decide whether the fix belongs to model selection,
custom code, data/config, optional dependencies, or training execution.

| Symptom | Likely cause | Recovery |
|---|---|---|
| `ValueError: model_name ... is not the name of an existing model` | Wrong model spelling, model not installed in this RecBole version, or a custom local model passed as a string | Try public class spelling (`BPR`, `SASRec`, `FM`, `KGAT`, `XGBoost`, `LightGBM`). Run `scripts/inspect_model_registry.py <name> --details`. For local custom classes, import the class and pass the class object instead of a string. |
| Module imports but `getattr`/class lookup fails | Case mismatch between module filename and class name | Use the exact class name. External-library docs may show lower-case names, but registry resolution commonly needs `XGBoost` or `LightGBM`. |
| `ModuleNotFoundError: xgboost` or `ModuleNotFoundError: lightgbm` | Optional external-library model dependency is missing | Install the matching optional package in the active environment or switch to a non-external context-aware model. Do not diagnose this as a RecBole registry bug until dependency import succeeds. |
| Knowledge-aware model import/runtime complains about graph packages | Optional graph dependency or sparse operation support is missing | Confirm the model's optional packages and backend. If the task does not require KG propagation, switch families; otherwise include the dependency/backend in the run plan. |
| Constructor `KeyError` for `embedding_size`, `hidden_size`, `layers`, `loss_type`, etc. | Model-property YAML was not loaded, custom defaults are absent, or config overrides omitted required hyperparameters | Check the known property YAML filename with the helper. Provide the missing keys through config or package a matching model-property YAML for custom models. |
| Config error says the model must have `input_type` or `loss_type` | Custom model lacks an explicit input contract | Set `input_type = InputType.POINTWISE` or `InputType.PAIRWISE`, or intentionally implement a supported `loss_type` path. For ordinary custom models, prefer explicit `input_type`. |
| `NotImplementedError` from `calculate_loss`, `predict`, or `full_sort_predict` | Custom model inherited abstract methods but did not implement required methods; full-sort evaluation may call the optional method | Implement `calculate_loss` and `predict`. Implement `full_sort_predict` for efficient full-ranking evaluation or change evaluation mode in the training/config route. |
| `KeyError` for `neg_item_id`, `neg_<item field>`, or similar | Pairwise model/input type but negative sampling did not create negative item fields | Align `input_type`, `loss_type`, and `train_neg_sample_args`. Pairwise losses need negative sampling; CE/pointwise losses usually do not. Route config details to `configuration-and-data`. |
| `KeyError` for `label` or poor CTR behavior with all-positive labels | Context-aware/CTR model lacks a label field or threshold-derived labels | Set `LABEL_FIELD` or threshold/label config and ensure the label column is loaded from `.inter`. This is a data/config issue, not a model-family issue. |
| User asks for CTR with side features but proposed `BPR` or `LightGCN` ignores features | Wrong family selection | Route to context-aware models (`FM`, `DeepFM`, `DCN`, `AutoInt`, etc.) and verify `.inter` labels plus `.user`/`.item` feature loading. |
| Knowledge-aware model says `.kg` or `.link` is missing | Data family prerequisites are incomplete | Provide `.inter`, `.kg`, and `.link`, and configure entity/relation/head/tail fields. If no KG is available, switch to general or context-aware models. |
| Sequential model reports missing item-list or sequence length fields | Dataset was not prepared as sequential, or ordering fields/config are missing | Verify sequential config fields and ordering in `.inter`. Route atomic and config validation to `configuration-and-data`. |
| Custom context model cannot see a side feature | Feature not loaded, wrong feature type, or `.user`/`.item` file absent | Check `load_col`, atomic field type suffixes, and the presence of side-feature files. Use `ContextRecommender` field groups rather than hard-coded assumptions. |
| `get_trainer` returns the default trainer but the model needs special optimization | Trainer class name is not discoverable or no custom trainer exists | Name the trainer `<ModelName>Trainer` where RecBole imports trainers, or instantiate it explicitly. Route actual training behavior checks to `training-evaluation-and-tuning`. |
| Custom metric name is not recognized | Metric class is not registered/imported when RecBole builds metric dictionaries | Ensure the metric class is imported into the metric module/entry point used by the run. Metric keys should be lower-case in outputs. |
| NaN/overflow with mixed precision | Model/loss is numerically unstable under AMP; sparse ops may not support mixed precision | Disable AMP/scaler or customize the trainer carefully. Sparse-heavy models such as `NGCF`, `DMF`, `GCMC`, `LightGCN`, `NCL`, `SGL`, `SpectralCF`, and `KGAT` need extra caution. |
| CUDA out-of-memory or very slow full-sort evaluation | Large item/entity set, full-sort scoring, KG graph memory, or large sequential model | Lower batch size, use negative-sample evaluation when acceptable, reduce embedding/hidden sizes, or use CPU/optional backend only after stating the trade-off. |

## Debugging A Custom Model That `get_model` Cannot Resolve

1. Check whether the user passed a local class name string. If yes, import the
   class and pass the class object to RecBole config instead.
2. If string resolution is required, ensure the installed module path is under a
   RecBole-searched model family, the module filename is lower-case, and the
   class name exactly matches the model string.
3. Run the bundled helper against the installed package:

   ```bash
   scripts/inspect_model_registry.py NewModel --details
   ```

4. If resolution succeeds but construction fails, inspect `input_type`, required
   config keys, and implemented methods.

## Debugging Missing `input_type` Or Methods

A valid ordinary custom model should have all of the following before any
training run:

```python
input_type = InputType.POINTWISE  # or InputType.PAIRWISE

def __init__(self, config, dataset): ...
def calculate_loss(self, interaction): ...
def predict(self, interaction): ...
# optional but recommended for full ranking:
def full_sort_predict(self, interaction): ...
```

If any are missing, fix the custom model first. If the fields read inside those
methods are missing from `interaction`, fix data/config or dataloader alignment
next.
