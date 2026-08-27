# CLI reference

This sub-skill covers two source entry points:

- `Pyraformer/long_range_main.py` for the benchmark long-range route.
- `Pyraformer/single_step_main.py` for the electricity, flow, and wind single-step route.

## Long-range entry point

Run the source CLI from a repo checkout:

```bash
python Pyraformer/long_range_main.py [flags]
```

### Important flags

| Flag | Meaning | Notes |
| --- | --- | --- |
| `-eval` | Load a checkpoint and run test-only evaluation | Reads from `models/LongRange/<data>/<predict_step>/best_iter<i>.pth` |
| `-data` | Dataset key | Common values: `ETTh1`, `ETTh2`, `ETTm1`, `ETTm2`, `electricity`, `exchange`, `traffic`, `weather`, `ili` |
| `-root_path` | Directory containing the CSV files | The upstream default assumes the benchmark dataset folder next to the Pyraformer source tree |
| `-data_path` | CSV filename | Must match the dataset key and file layout |
| `-input_size` | History length | Also used by the attention masks and checkpoint path |
| `-predict_step` | Forecast horizon | Also used by the checkpoint path |
| `-model` | Model class name | Default is `Pyraformer` |
| `-decoder` | Decoder family | `FC` or `attention`; the benchmark scripts use `FC` |
| `-epoch` | Training epochs | Default is small for the source script |
| `-batch_size` | Mini-batch size | Tune per dataset and horizon |
| `-pretrain` | Enable pretrain mode | Long-range parser uses `store_true`; default is off |
| `-hard_sample_mining` | Enable hard-sample mining | Long-range parser uses `store_true`; default is off |
| `-dropout` | Dropout rate | Model hyperparameter |
| `-lr` | Learning rate | Source default is `1e-4` |
| `-lr_step` | Scheduler decay | Used by `StepLR` |
| `-d_model` | Hidden size | Model hyperparameter |
| `-d_inner_hid` | Feed-forward hidden size | Model hyperparameter |
| `-d_k` | Attention key width | Model hyperparameter |
| `-d_v` | Attention value width | Model hyperparameter |
| `-d_bottleneck` | Bottleneck width | Used by the pyramid constructor |
| `-n_head` | Attention heads | Model hyperparameter |
| `-n_layer` | Encoder depth | Model hyperparameter |
| `-window_size` | Pyramid branching factors | Pass as a Python list string such as `[4, 4, 4]` |
| `-inner_size` | Intra-scale neighborhood size | Controls local attention width |
| `-CSCM` | Pyramid constructor | `Bottleneck_Construct`, `Conv_Construct`, `MaxPooling_Construct`, or `AvgPooling_Construct` |
| `-truncate` | Drop coarse-scale nodes in the attention decoder | Mainly relevant for `decoder=attention` |
| `-use_tvm` | Enable the optional TVM-backed path | Requires a constant `window_size` list and a compatible CUDA/TVM setup |
| `-iter_num` | Repeat count | Produces `best_iter<i>.pth` files under the long-range checkpoint directory |

### Dataset parameter summary

The script fills several architecture fields from the dataset key before model creation:

| Dataset key | `enc_in` | `covariate_size` | `seq_num` | Embedding |
| --- | --- | --- | --- | --- |
| `ETTh1`, `ETTh2`, `ETTm1`, `ETTm2` | 7 | 4 | 1 | `DataEmbedding` |
| `electricity` | 321 | 4 | 1 | `CustomEmbedding` |
| `exchange` | 8 | 4 | 1 | `CustomEmbedding` |
| `traffic` | 862 | 4 | 1 | `CustomEmbedding` |
| `weather` | 21 | 4 | 1 | `CustomEmbedding` |
| `ili` | 7 | 4 | 1 | `CustomEmbedding` |

## Single-step entry point

Run the source CLI from a repo checkout:

```bash
python Pyraformer/single_step_main.py [flags]
```

### Important flags

| Flag | Meaning | Notes |
| --- | --- | --- |
| `-eval` | Load a checkpoint and run test-only evaluation | Reads from `models/SingleStep/<dataset>/best_model.pth` |
| `-data_path` | Directory containing the preprocessed `.npy` files | Default is `data/elect/` |
| `-dataset` | Dataset key | `elect`, `flow`, or `wind` |
| `-epoch` | Training epochs | Source default is `10` |
| `-inner_batch` | Effective training batch size | The loader uses `batch_size=1` and slices this many sequences per step |
| `-lr` | Learning rate | Source default is `1e-5` |
| `-visualize_fre` | Logging frequency | Controls the training print cadence |
| `-pretrain` | Disable pretraining when passed | This parser uses `store_false`; default is on |
| `-hard_sample_mining` | Disable hard-sample mining when passed | This parser uses `store_false`; default is on |
| `-model` | Model class name | Default is `Pyraformer` |
| `-d_model` | Hidden size | Model hyperparameter |
| `-d_inner_hid` | Feed-forward hidden size | Model hyperparameter |
| `-d_k` | Attention key width | Model hyperparameter |
| `-d_v` | Attention value width | Model hyperparameter |
| `-n_head` | Attention heads | Model hyperparameter |
| `-n_layer` | Encoder depth | Model hyperparameter |
| `-dropout` | Dropout rate | Model hyperparameter |
| `-window_size` | Pyramid branching factors | Pass as a Python list string such as `[4, 4, 4]` or `[2, 2, 2]` |
| `-inner_size` | Intra-scale neighborhood size | Controls local attention width |
| `-use_tvm` | Enable the optional TVM-backed path | Requires a constant `window_size` list and a compatible CUDA/TVM setup |
| `-predict_step` | Forecast horizon | Default is `24` |

### Dataset parameter summary

The single-step loader fixes the model shape from the dataset key:

| Dataset key | `num_seq` | `covariate_size` | `input_size` | `ignore_zero` |
| --- | --- | --- | --- | --- |
| `elect` | 370 | 3 | 169 | `True` |
| `flow` | 1083 | 3 | 192 | `True` |
| `wind` | 29 | 3 | 192 | `False` |

## Common checkpoints and outputs

| Route | Output |
| --- | --- |
| Long-range train | `models/LongRange/<data>/<predict_step>/best_iter<i>.pth` |
| Single-step train | `models/SingleStep/<dataset>/best_model.pth` |
| Elect preprocessing | `data/elect/*.npy` |
| Flow preprocessing | `data/flow/*.npy` |
| Wind preprocessing | `data/wind/*.npy` |
| Synthetic generation | `data/synthetic.npy` |

## Flag gotchas

- `window_size` is evaluated as Python code in the source scripts, so the value must be quoted as a list string.
- `-pretrain` and `-hard_sample_mining` behave differently in the two source entry points.
- `use_tvm` is an advanced route and is not part of the default smoke path.
