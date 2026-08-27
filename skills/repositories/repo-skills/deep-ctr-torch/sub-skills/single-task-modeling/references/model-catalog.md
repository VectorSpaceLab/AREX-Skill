# Single-task model catalog

This catalog covers the 16 DeepCTR-Torch **single-output** model classes owned by this sub-skill. The installed package exposes 22 model classes total; `DIN` and `DIEN` are routed to [`../../sequence-and-interest-models/SKILL.md`](../../sequence-and-interest-models/SKILL.md), and `SharedBottom`, `ESMM`, `MMOE`, and `PLE` are routed to [`../../multitask-modeling/SKILL.md`](../../multitask-modeling/SKILL.md).

All models here accept `task='binary'` or `task='regression'` unless noted. `task='binary'` applies a sigmoid prediction layer; `task='regression'` returns the scalar logit without sigmoid.

## Constructor families

| Family | Constructor shape | Use when | Watch-outs |
|---|---|---|---|
| `WDL` | `WDL(linear_feature_columns, dnn_feature_columns, ...)` | Wide & Deep baseline: linear memorization plus DNN generalization. | Needs both lists supplied, even if one is intentionally empty. |
| `DeepFM` | `DeepFM(linear_feature_columns, dnn_feature_columns, use_fm=True, ...)` | Strong default for CTR-style tabular binary classification; also works for scalar regression. | `use_fm=False` disables the FM interaction part. Empty `linear_feature_columns` is supported for no-wide/no-linear experiments. |
| `xDeepFM` | `xDeepFM(linear_feature_columns, dnn_feature_columns, cin_layer_size=(256, 128), ...)` | Combine DNN with CIN explicit feature interactions. | Tune `cin_layer_size`; large defaults can be excessive for tiny data. |
| `AFM` | `AFM(linear_feature_columns, dnn_feature_columns, use_attention=True, attention_factor=8, ...)` | FM-style interaction model with attention over pairwise interactions. | Use sparse embeddings; attention settings matter more when there are multiple sparse fields. |
| `AFN` | `AFN(linear_feature_columns, dnn_feature_columns, ltl_hidden_size=256, afn_dnn_hidden_units=(256, 128), ...)` | Adaptive-order feature interactions. | DNN hidden argument name is `afn_dnn_hidden_units`, not `dnn_hidden_units`. |
| `AutoInt` | `AutoInt(linear_feature_columns, dnn_feature_columns, att_layer_num=3, att_head_num=2, att_res=True, dnn_hidden_units=(256, 128, 64), ...)` | Multi-head self-attention over feature embeddings, optionally combined with DNN. | Default DNN has three layers `(256, 128, 64)`. Attention output size is controlled by `att_embedding_size`. |
| `DCN` | `DCN(linear_feature_columns, dnn_feature_columns, cross_num=2, cross_parameterization='vector', dnn_hidden_units=(128, 128), ...)` | Explicit cross features with optional DNN. | `cross_parameterization` is `'vector'` or `'matrix'`. Empty DNN and zero cross layers together are not useful. |
| `DCNMix` | `DCNMix(linear_feature_columns, dnn_feature_columns, cross_num=2, low_rank=32, num_experts=4, ...)` | DCN-Mix mixture-of-experts cross network plus optional DNN. | More parameters than `DCN`; lower `low_rank`, `num_experts`, or DNN sizes for smoke tests. |
| `FiBiNET` | `FiBiNET(linear_feature_columns, dnn_feature_columns, bilinear_type='interaction', reduction_ratio=3, ...)` | SENET feature reweighting plus bilinear feature interactions. | `bilinear_type` changes interaction parameterization; keep default unless reproducing a known setting. |
| `IFM` | `IFM(linear_feature_columns, dnn_feature_columns, dnn_hidden_units=(256, 128), ...)` | Input-aware factorization machine with instance-specific feature weights. | Has an additional factor-estimating network; DNN sizes affect both capacity and speed. |
| `DIFM` | `DIFM(linear_feature_columns, dnn_feature_columns, att_head_num=8, dnn_hidden_units=(256, 128, 64), ...)` | Dual input-aware FM with vector-wise and bit-wise feature reweighting. | Default DNN has three layers; attention dimensions follow `att_embedding_size`. |
| `MLR` | `MLR(region_feature_columns, base_feature_columns=None, bias_feature_columns=None, region_num=4, ...)` | Piece-wise linear / mixed logistic regression model. | Special feature-column groups; not `linear_feature_columns, dnn_feature_columns`. Input must include the union of region/base/bias feature names. `region_num` must be greater than 1. |
| `NFM` | `NFM(linear_feature_columns, dnn_feature_columns, dnn_hidden_units=(128, 128), bi_dropout=0, ...)` | Neural FM using bi-interaction pooling plus DNN. | Embedding dimensions across sparse/varlen features must match. |
| `ONN` | `ONN(linear_feature_columns, dnn_feature_columns, dnn_hidden_units=(128, 128), ...)` | Operation-aware neural network preserving field-pair interaction information. | More expensive with many sparse fields because it models second-order pairs. |
| `PNN` | `PNN(dnn_feature_columns, use_inner=True, use_outter=False, kernel_type='mat', ...)` | Product-based neural network with inner and/or outer products. | Constructor has **no** linear column list. `kernel_type` must be `mat`, `vec`, or `num`. |
| `CCPM` | `CCPM(linear_feature_columns, dnn_feature_columns, conv_kernel_width=(6, 5), conv_filters=(4, 4), dnn_hidden_units=(256,), ...)` | Convolutional click prediction over feature embeddings. | Keep convolution widths compatible with the number of sparse fields; tests use smaller kernels for tiny field counts. |

## Fast selection rules

- Start with `DeepFM` for a robust single-output CTR/recommender baseline.
- Use `WDL` when you want a simpler wide + DNN baseline without FM interaction.
- Use `xDeepFM`, `DCN`, `DCNMix`, `AutoInt`, `FiBiNET`, `IFM`, `DIFM`, `AFN`, `NFM`, `ONN`, `PNN`, or `CCPM` when the user explicitly asks for a named interaction family or a benchmark comparison.
- Use `MLR` only when the user needs piece-wise linear modeling and can provide region/base/bias feature groups.
- Do not route DIN/DIEN here even though they are single-target; they require behavior-history sequence contracts.
- Do not route SharedBottom/ESMM/MMOE/PLE here; they require multi-output task-name/task-type contracts.

## Binary versus regression

| Objective | Model `task` | Loss | Typical metrics | Output interpretation |
|---|---|---|---|---|
| Binary CTR/click prediction | `task='binary'` | `binary_crossentropy` | `binary_crossentropy`, `logloss`, `auc`, `accuracy`, `acc` | Probability-like value in `[0, 1]` from sigmoid. |
| Scalar rating/value regression | `task='regression'` | `mse` or `mae` | `mse` | Unbounded scalar prediction; do not use AUC or accuracy. |

For a worked binary-to-regression conversion, see [training and prediction workflows](training-and-prediction.md#convert-binary-deepfm-to-regression-ratings).
