# Pipeline component catalog

This cheat sheet is for FATE-Client Pipeline workflows backed by a FateFlow service. It summarizes the verified pipeline methods, component call shapes, artifacts, and common uses needed by future agents. Placeholder defaults from the installed-package probe are shown as `<placeholder>` instead of the probe object's memory address; parameter names and order are preserved where signatures were captured.

## Verified `FateFlowPipeline` methods

Use these exact method names:

| Method | Verified signature or call shape | Use |
| --- | --- | --- |
| `FateFlowPipeline` | `FateFlowPipeline(*args)` | Create a service-backed pipeline object. |
| `set_parties` | `set_parties(self, guest=None, host=None, arbiter=None, **kwargs)` | Register guest/host/arbiter or local parties. Examples also use `local="0"` through `**kwargs` for upload. |
| `set_site_role` | `set_site_role(self, role)` | Set local upload site role, e.g. `"local"`. |
| `set_site_party_id` | `set_site_party_id(self, party_id)` | Set local upload site party id, e.g. `"0"`. |
| `transform_local_file_to_dataframe` | Example-backed call uses `file`, `namespace`, `name`, `meta`, `head`, `extend_sid` | Upload/transform local data into a FATE table. Requires FateFlow. |
| `add_tasks` | `add_tasks(self, task_list) -> 'Pipeline'` | Add ordered component objects. |
| `compile` | `compile(self) -> 'Pipeline'` | Compile DAG before run. |
| `fit` | `fit(self) -> 'Pipeline'` | Run training/transform pipeline. |
| `predict` | `predict(self) -> 'Pipeline'` | Run prediction pipeline. |
| `dump_model` | `dump_model(self, file_path)` | Save a trained pipeline. |
| `load_model` | `load_model(file_path)` | Reload a saved pipeline. Called as `FateFlowPipeline.load_model(path)` in examples. |
| `deploy` | `deploy(self, task_list=None)` | Mark trained components for inference-time reuse. |
| `get_deployed_pipeline` | `get_deployed_pipeline(self)` | Get the deployed component bundle to attach to a prediction pipeline. |
| `get_task_info` | `get_task_info(self, task)` | Retrieve output model/data/metric handles after run. |

## Core data and DAG components

| Component | Verified or example-backed constructor shape | Main inputs | Main outputs | Use cases and notes |
| --- | --- | --- | --- | --- |
| `Reader` | `Reader(_name, runtime_parties=None, namespace=<placeholder>, name=<placeholder>)` | Table `namespace`/`name` supplied through role-specific `task_parameters(...)`. | `output_data` | Entry point from uploaded FATE tables. Use `reader.guest.task_parameters(...)`, `reader.hosts[0].task_parameters(...)`, and for multi-host examples `reader.hosts[[0, 1]].task_parameters(...)`. |
| `PSI` | `PSI(_name, runtime_parties=None, input_data=<placeholder>, protocol=<placeholder>, curve_type=<placeholder>)` | `input_data`, usually `reader.outputs["output_data"]`. | `output_data`, `metric` | Private set intersection/sample alignment for hetero tasks. FATE 2.x data should have sample id and match id; use upload `extend_sid=True` when the source has only one id. |
| `DataSplit` | `DataSplit(_name, runtime_parties=None, input_data=<placeholder>, train_size=None, validate_size=None, test_size=None, stratified=False, random_state=None, hetero_sync=True)` | One aligned data table. | `train_output_data`, `validate_output_data`, `test_output_data`, `metric` | Split by ratios or counts. Do not mix int and float split sizes. If all sizes are `None`, docs describe an 80/20 train/validate split with empty test. |
| `Sample` | Example-backed: `Sample("sample_0", frac={0: 0.5}, replace=False, hetero_sync=True, input_data=...)` or `Sample("sample_1", n=100, replace=False, hetero_sync=True, input_data=...)` | One data table. | `output_data` in component docs/examples. | Random or stratified sampling. Docs note `hetero_sync=True` for heterogeneous scenarios and `replace=True` for upsampling. Exact installed signature was not captured in the probe; stay close to example-backed kwargs unless inspecting the package. |
| `Union` | `Union(_name, runtime_parties=None, input_datas=<placeholder>)` | List of data tables. | `output_data` | Concatenate tables along axis 0. Headers, sample id, match id, and label columns must match. |
| `Statistics` | Example-backed: `Statistics("statistics_0", input_data=..., metrics=["min", "max", "25%", "mean", "median"])` | Data table. | `output_model` in examples/docs; metrics/statistics model. | Column statistics for min/max/mean/median/percentiles, missing counts/ratios, skewness/kurtosis, etc.; often feeds `HeteroFeatureSelection`. Exact installed signature was not captured in the probe. |
| `FeatureCorrelation` | Example-backed: `FeatureCorrelation("feature_corr_0", input_data=...)` | Data table. | `output_model` in examples. | Pearson correlation matrix in local or hetero-federated mode. Docs mention `local_only` for mode selection; inspect before using uncommon params. |

## Feature engineering components

| Component | Verified constructor shape | Main inputs | Main outputs | Use cases and notes |
| --- | --- | --- | --- | --- |
| `FeatureScale` | `FeatureScale(_name, runtime_parties=None, method=<placeholder>, feature_range=None, scale_col=None, scale_idx=None, strict_range=True, use_anonymous=False, train_data=<placeholder>, test_data=<placeholder>, input_model=<placeholder>)` | `train_data`, `test_data`, optional `input_model`. | `train_output_data`, `test_output_data`, `output_model`, `metric` in docs/examples. | Min-max or standard scaling. Use a training instance to create the model and a second instance with `test_data` + `input_model` to apply it. |
| `HeteroFeatureBinning` | `HeteroFeatureBinning(_name, runtime_parties=None, method=<placeholder>, n_bins=None, split_pt_dict=None, bin_col=None, bin_idx=None, category_col=None, category_idx=None, use_anonymous=False, transform_method=None, skip_metrics=False, local_only=False, relative_error=1e-06, adjustment_factor=0.5, he_param=<placeholder>, train_data=<placeholder>, test_data=<placeholder>, input_model=<placeholder>)` | `train_data`, `test_data`, optional `input_model`. | `train_output_data`, `test_output_data`, `output_model`, `metric`. | Quantile, bucket, or manual binning; computes IV/WOE and can transform data. Supports multi-host and asymmetric binning. |
| `HeteroFeatureSelection` | `HeteroFeatureSelection(_name, runtime_parties=None, method=<placeholder>, select_col=None, iv_param=None, statistic_param=None, manual_param=None, keep_one=True, use_anonymous=False, train_data=<placeholder>, test_data=<placeholder>, input_model=<placeholder>, input_models=<placeholder>)` | `train_data`, `test_data`, plus `input_model`/`input_models` from binning/statistics. | `train_output_data`, `test_output_data`, `output_model` / example uses `train_output_model`. | Cascade feature filters: IV, statistics, and manual keep/drop. Keep method order explicit. Use federated IV params carefully in multi-host tasks. |

## Model and evaluation components

| Component | Verified constructor shape | Main inputs | Main outputs | Use cases and notes |
| --- | --- | --- | --- | --- |
| `HeteroSecureBoost` | `HeteroSecureBoost(_name, runtime_parties=None, train_data=<placeholder>, validate_data=<placeholder>, num_trees=20, learning_rate=0.3, max_depth=3, max_bin=32, objective='binary:bce', num_class=2, goss=False, goss_start_iter=0, top_rate=0.2, other_rate=0.1, l1=0, l2=0.1, min_impurity_split=0.01, min_sample_split=2, min_leaf_node=1, min_child_weight=1, gh_pack=True, split_info_pack=True, hist_sub=True, he_param=<placeholder>, cv_param=<placeholder>, train_output_data=<placeholder>, output_model=<placeholder>, warm_start_model=<placeholder>, test_data=<placeholder>, input_model=<placeholder>, cv_data=<placeholder>)` | Aligned hetero data, often `psi.outputs["output_data"]`; optional validation/test/cv/warm-start/model. | `train_output_data`, `test_output_data`, `cv_output_datas`, `output_model`, `metric`. | Hetero GBDT for binary, multi-class, or regression. Examples use `objective='multi:ce'` with `num_class` and `objective='regression:l2'` for variants. |
| `SSHELR` | `SSHELR(_name, runtime_parties=None, epochs=20, early_stop='diff', tol=0.0001, batch_size=None, learning_rate=<placeholder>, init_param=<placeholder>, threshold=0.5, train_data=<placeholder>, cv_data=<placeholder>, cv_param=<placeholder>, reveal_every_epoch=False, reveal_loss_freq=1, output_cv_data=True, validate_data=<placeholder>, test_data=<placeholder>, input_model=<placeholder>, warm_start_model=<placeholder>)` | Hetero aligned train/validate/test/cv data. | `train_output_data`, `test_output_data`, `cv_output_datas`, `output_model`. | Arbiter-less secure hetero logistic regression. Docs mark multi-host unsupported for SSHE LR; use coordinated LR for multi-host. |
| `SSHELinR` | `SSHELinR(_name, runtime_parties=None, epochs=20, early_stop='diff', tol=0.0001, batch_size=None, learning_rate=<placeholder>, init_param=<placeholder>, threshold=0.5, train_data=<placeholder>, cv_data=<placeholder>, cv_param=<placeholder>, reveal_every_epoch=False, reveal_loss_freq=1, output_cv_data=True, validate_data=<placeholder>, test_data=<placeholder>, input_model=<placeholder>, warm_start_model=<placeholder>)` | Hetero aligned regression data. | `train_output_data`, `test_output_data`, `cv_output_datas`, `output_model`. | Secure hetero linear regression. Docs mark multi-host unsupported; coordinated LinR supports multi-host. |
| `CoordinatedLR` | `CoordinatedLR(_name, runtime_parties=None, epochs=20, early_stop='diff', tol=0.0001, batch_size=None, optimizer=<placeholder>, learning_rate_scheduler=<placeholder>, init_param=<placeholder>, threshold=0.5, train_data=<placeholder>, cv_data=<placeholder>, cv_param=<placeholder>, floating_point_precision=23, he_param=<placeholder>, output_cv_data=True, validate_data=<placeholder>, test_data=<placeholder>, input_model=<placeholder>, warm_start_model=<placeholder>)` | Hetero aligned train/validate/test/cv data; often with arbiter. | `train_output_data`, `test_output_data`, `cv_output_datas`, `output_model`. | Hetero logistic regression with coordinator/arbiter, including multi-host, CV, warm-start, and multi-class examples. |
| `CoordinatedLinR` | `CoordinatedLinR(_name, runtime_parties=None, epochs=20, early_stop='diff', tol=0.0001, batch_size=None, optimizer=<placeholder>, learning_rate_scheduler=<placeholder>, init_param=<placeholder>, train_data=<placeholder>, cv_data=<placeholder>, output_cv_data=True, cv_param=<placeholder>, floating_point_precision=23, he_param=<placeholder>, validate_data=<placeholder>, test_data=<placeholder>, input_model=<placeholder>, warm_start_model=<placeholder>)` | Hetero aligned regression data; often with arbiter. | `train_output_data`, `test_output_data`, `cv_output_datas`, `output_model`. | Hetero linear regression with coordinator/arbiter, multi-host, CV, and warm-start examples. |
| `HomoLR` | `HomoLR(_name, runtime_parties=None, epochs=20, early_stop='diff', tol=0.0001, batch_size=-1, optimizer=<placeholder>, learning_rate_scheduler=<placeholder>, init_param=<placeholder>, threshold=0.5, ovr=False, label_num=None, train_data=<placeholder>, validate_data=<placeholder>, test_data=<placeholder>, warm_start_model=<placeholder>, input_model=<placeholder>)` | Horizontally partitioned tables with same features. | `train_output_data`, `test_output_data`, `output_model`. | Homogeneous logistic regression; examples set guest, host, and arbiter parties. |
| `HomoNN` | `HomoNN(_name, runtime_parties=None, runner_module=<placeholder>, runner_class=<placeholder>, runner_conf=<placeholder>, source=<placeholder>, train_data=<placeholder>, validate_data=<placeholder>, test_data=<placeholder>, warm_start_model=<placeholder>, input_model=<placeholder>)` | Homo training/validation/test data and NN runner config. | `train_output_data`, `test_output_data`, `output_model`. | Federated PyTorch/transformers NN through FATE Pipeline. CPU torch was verified; GPU/DeepSpeed optional/unverified. |
| `HeteroNN` | `HeteroNN(_name, runtime_parties=None, runner_module=<placeholder>, runner_class=<placeholder>, runner_conf=<placeholder>, source=<placeholder>, train_data=<placeholder>, validate_data=<placeholder>, test_data=<placeholder>, warm_start_model=<placeholder>, input_model=<placeholder>)` | Hetero train/validation/test data and NN runner config. | `train_output_data`, `test_output_data`, `output_model`. | Hetero neural network with SSHE or FedPass strategies. Pipeline execution still requires FateFlow service. |
| `Evaluation` | `Evaluation(_name, runtime_parties=None, default_eval_setting=<placeholder>, metrics=None, predict_column_name=None, label_column_name=None, input_datas=<placeholder>)` | List of model output data tables. | `metric`. | Binary/multi/regression metrics. Use `runtime_parties` to limit where metrics are emitted, commonly `dict(guest=guest)` for hetero models. |

## NN helper signature

`get_config_of_default_runner(algo='fedavg', model=None, optimizer=None, loss=None, training_args=None, fed_args=None, dataset=None, data_collator=None, tokenizer=None, task_type='binary')`

The full probe includes type annotations for PyTorch modules, optimizer/loss loaders, `TrainingArguments`, and `FedArguments`. In practice, examples pass `algo='fedavg'`, a `Sequential` model, `nn.BCELoss()`, `optim.Adam(lr=...)`, `TrainingArguments(...)`, `FedAVGArguments()`, and `task_type='binary'`.

## Component selection guide

- **Need uploaded table entry point**: `Reader`.
- **Need vertical-party sample alignment**: `PSI` before feature/model components.
- **Need train/validate/test split**: `DataSplit`.
- **Need sampling/rebalancing**: `Sample` with example-backed `frac` or `n`.
- **Need scaling**: `FeatureScale`; fit one scaler on train data and reuse its `output_model` for test data.
- **Need IV/WOE or bins**: `HeteroFeatureBinning`.
- **Need feature filters**: `HeteroFeatureSelection`, optionally with binning/statistics models.
- **Need correlations**: `FeatureCorrelation`.
- **Need simple table concatenation**: `Union`, with matching headers/ids.
- **Need hetero GBDT**: `HeteroSecureBoost`.
- **Need secure hetero LR/LinR without multi-host**: `SSHELR` or `SSHELinR`.
- **Need hetero LR/LinR with arbiter or multi-host**: `CoordinatedLR` or `CoordinatedLinR`.
- **Need homo LR/NN**: `HomoLR` or `HomoNN` with guest/host/arbiter party setup.
- **Need metrics**: `Evaluation` after the model/test component.
