# Model Family Selection

DeepChem exposes both base wrappers and optional-backend neural model families. In minimal environments, only the scikit-learn path is safe to assume.

## Minimal-install choices

| Goal | Preferred model | Backend requirements | Notes |
| --- | --- | --- | --- |
| Fast regression/classification baseline | `dc.models.SklearnModel` wrapping a scikit-learn estimator | scikit-learn | Best first step for fingerprints, descriptors, and small tabular datasets. |
| Gradient boosting with early stopping | `dc.models.GBDTModel` wrapping XGBoost/LightGBM sklearn-style estimators | xgboost and lightgbm | Single-output only; not safe in base environments unless both packages are installed. |
| Hyperparameter search | `dc.hyper.GridHyperparamOpt` or `RandomHyperparamOpt` | same as candidate model | Serial search, so keep candidate count small. |

## General purpose neural families

These require optional backends and compatible featurized inputs.

| Model family | Typical use | Backend gate | Fit note |
| --- | --- | --- | --- |
| `MultitaskClassifier`, `MultitaskRegressor`, `MultitaskFitTransformRegressor` | Descriptor/fingerprint multitask prediction | PyTorch for current multitask entries | Use `fit()` with classification/regression metrics. |
| `ProgressiveMultitaskClassifier`, `ProgressiveMultitaskRegressor`, `RobustMultitaskClassifier`, `RobustMultitaskRegressor` | Transfer/multitask baselines | Keras/TensorFlow for listed implementations | Use only when TensorFlow/Keras stack is available. |
| `CNN`, `UNet`, `PINNModel`, `FNOModel` | Images, fields, or physics-inspired data | Keras or PyTorch depending on class | Confirm expected tensor shapes before training. |
| `SeqToSeq` | Sequence-to-sequence generation | PyTorch | Uses `fit_sequences()` instead of ordinary `fit()`. |
| `WGAN` and GAN variants | Generative/adversarial workflows | Keras or PyTorch depending on class | Uses `fit_gan()` and custom generators. |

## Molecular neural families

Route featurizer selection to the featurization sub-skill, then pick a model whose expected feature objects match the dataset.

| Model family | Common featurizer | Backend gate | Notes |
| --- | --- | --- | --- |
| `GraphConvModel`, `DAGModel`, `WeaveModel`, `AtomicConvModel`, `ScScoreModel` | `ConvMolFeaturizer`, `WeaveFeaturizer`, complex/atomic/image featurizers | Keras/TensorFlow | Older Keras-backed molecular models; avoid if TensorFlow is unavailable. |
| `GCNModel`, `GATModel`, `MPNNModel`, `PagtnModel` | `MolGraphConvFeaturizer` or model-specific graph featurizer | DGL plus PyTorch | Check DGL installation before import. |
| `AttentiveFPModel`, `DMPNNModel`, `MATModel`, `DTNNModel`, `ProgressiveMultitaskModel` | model-specific graph/3D/descriptor featurizers | PyTorch, sometimes PyTorch Geometric | Good candidates when graph extras are installed. |
| `ChemCeption` | `SmilesToImage` | Keras or PyTorch | Image-like molecule representation. |
| `TextCNNModel`, `Smiles2Vec`, `Chemberta`, `MoLFormer` | sequence/tokenizer/dummy featurizers | Keras or PyTorch | Choose for SMILES/text representation tasks. |
| `BasicMolGANModel` | `MolGanFeaturizer` | Keras | Uses adversarial training, not standard scalar metrics. |

## Backend decision rules

- If the environment reports missing TensorFlow, PyTorch, JAX, DGL, or PyTorch Geometric, do not select models that require them unless the user approves installing extras.
- If the user asks for “a DeepChem model” without specifying a neural architecture, start with `SklearnModel` or a backend-safe estimator baseline.
- If the user asks for graph neural networks, first verify graph featurizers and DGL/PyTorch availability.
- If the user asks for Keras/TensorFlow models in an environment that only imports base DeepChem, present the missing dependency gate and a fallback baseline.
- JAX-backed classes live under JAX model surfaces and require JAX; treat them as optional even if `deepchem` imports successfully.

## Model and metric compatibility quick checks

- Regression models should evaluate with regression metrics and predictions shaped like `(N,)` or `(N, n_tasks)`.
- Classification models should output probabilities for ROC-AUC/PRC-AUC; if they output labels, use thresholded metrics or adapt predictions.
- `GBDTModel` rejects multi-output labels; use one model per task or a different wrapper for multitask data.
- Generative models, sequence models, and GANs may not support ordinary `evaluate()` with scalar metrics; use their custom fit/predict methods and task-specific validation.
