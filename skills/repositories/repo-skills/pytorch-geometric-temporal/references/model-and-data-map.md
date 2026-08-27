# Model and Data Map

## Purpose

Use this as the compact routing and ownership map for the generated repo skill. It helps future agents jump to the right sub-skill before reading deeper references.

## Ownership map

| Capability family | Owner | Key public APIs | Typical trigger |
| --- | --- | --- | --- |
| Temporal signal iterators | `sub-skills/temporal-signals/` | `StaticGraphTemporalSignal`, `DynamicGraphTemporalSignal`, `DynamicGraphStaticSignal`, batch variants, `temporal_signal_split` | "build a snapshot iterator", "split a temporal signal", "why did I get Data vs Batch vs HeteroData?" |
| Dataset loaders | `sub-skills/dataset-loaders/` | `*DatasetLoader`, `get_dataset`, constructor cache/download behavior | "which loader should I use?", "how many lags?", "avoid download on constructor" |
| Recurrent layers | `sub-skills/recurrent-layers/` | `GConvGRU`, `GConvLSTM`, `DCRNN`, `TGCN`, `A3TGCN`, `AGCRN`, `MPNNLSTM`, `EvolveGCN*` | "forecast with recurrent ST-GNNs", "shape of H/C/lambda_max" |
| Attention and hetero layers | `sub-skills/attention-and-hetero-layers/` | `STConv`, `ASTGCN`, `MSTGCN`, `GMAN`, `MTGNN`, `AAGCN`, `DNNTSP`, `HeteroGCLSTM` | "attention-based temporal GNN", "heterogeneous graph recurrent model" |
| Index batching | `sub-skills/index-batching/` | `IndexDataset`, `get_index_dataset`, `allGPU`, `world_size`, `ddp_rank`, `dask_batching` | "make PGT use index batching", "PeMS index-only loader", "Dask-DDP" |

## Public signal and model catalog

### Signal classes

- Homogeneous temporal: `StaticGraphTemporalSignal`, `DynamicGraphTemporalSignal`, `DynamicGraphStaticSignal`.
- Homogeneous batch temporal: `StaticGraphTemporalSignalBatch`, `DynamicGraphTemporalSignalBatch`, `DynamicGraphStaticSignalBatch`.
- Heterogeneous temporal: `StaticHeteroGraphTemporalSignal`, `DynamicHeteroGraphTemporalSignal`, `DynamicHeteroGraphStaticSignal`.
- Heterogeneous batch temporal: `StaticHeteroGraphTemporalSignalBatch`, `DynamicHeteroGraphTemporalSignalBatch`, `DynamicHeteroGraphStaticSignalBatch`.

### Dataset-loader families

- Static JSON benchmarks: Chickenpox, PedalMe, WikiMaths, MontevideoBus, MTM.
- Dynamic JSON benchmark: EnglandCovid, TwitterTennis.
- Traffic forecasting: METR-LA, PemsBay.
- Index-only traffic loaders: Pems, PemsAllLA.
- Synthetic PDE loaders: AdvectionDiffusion, SIDiffusion, WaveEquation.
- Windmill loaders: Large is available; Medium and Small are intentionally unavailable in the inspected version.

### Recurrent model families

- Chebyshev/diffusion/temporal recurrent layers: `GConvGRU`, `GConvLSTM`, `GCLSTM`, `DCRNN`, `BatchedDCRNN`, `TGCN`, `TGCN2`, `A3TGCN`, `A3TGCN2`.
- Relational and evolving recurrent layers: `LRGCN`, `DyGrEncoder`, `EvolveGCNH`, `EvolveGCNO`, `MPNNLSTM`, `AGCRN`.

### Attention and heterogeneous model families

- Temporal convolution and graph-convolution blocks: `TemporalConv`, `STConv`, `ChebConvAttention`, `MSTGCN`.
- Traffic-attention and graph-mixing models: `ASTGCN`, `GMAN`, `MTGNN`, `DNNTSP`, `AAGCN`.
- Heterogeneous recurrent layer: `HeteroGCLSTM`.

## Validation map

| Route | Native candidate | Synthetic fallback |
| --- | --- | --- |
| Temporal iterator construction/splitting | `test/dataset_test.py`, `test/batch_test.py` synthetic iterator functions | `sub-skills/temporal-signals/scripts/signal_iterator_smoke.py` |
| Loader selection/signatures | Loader import/signature inspection; most loader construction tests are network-backed | `sub-skills/dataset-loaders/scripts/list_dataset_loaders.py` |
| Recurrent layer shapes/states | `test/recurrent_test.py` selected layer functions | `sub-skills/recurrent-layers/scripts/recurrent_forecasting_smoke.py` |
| Attention/hetero layer shapes | `test/attention_test.py` selected lightweight tests, `test/heterogeneous_test.py` | `sub-skills/attention-and-hetero-layers/scripts/attention_hetero_smoke.py` |
| Index batching and DDP planning | `test/index_test.py` is network-backed; treat as optional | `sub-skills/index-batching/scripts/index_batching_smoke.py` |

## Route-selection hints

- If the task mentions `snapshot`, `Data`, `Batch`, `HeteroData`, or `temporal_signal_split`, start with temporal-signals.
- If the task mentions `raw_data_dir`, `get_dataset`, `index=False`, or constructor downloads, start with dataset-loaders.
- If the task mentions hidden state, `edge_weight`, `lambda_max`, or recurrent forecasting, start with recurrent-layers.
- If the task mentions STConv/ASTGCN/MSTGCN/GMAN/MTGNN/AAGCN/DNNTSP/HeteroGCLSTM, start with attention-and-hetero-layers.
- If the task mentions `IndexDataset`, `index=True`, `allGPU`, `world_size`, `ddp_rank`, or `dask_batching`, start with index-batching.
