# Multimodal And Physics API Reference

## Catchment Embedding Dataset

### `CatchmentEmbeddingDataset`

`CatchmentEmbeddingDataset(data_dir, history_window_days=365, image_scale=3000.0, min_window_observed=0.5, seed=None)`

### Returns

Each item is a dictionary with:

- `image`: `(channels, height, width)` tensor.
- `static`: `(static_features,)` tensor.
- `history`: `(history_window_days, 2)` tensor containing standardized log-flow and an observed mask.
- `site_index`: long tensor with the site index.

## Catchment Encoder And Contrastive Pretraining

### `CatchmentEncoder`

`CatchmentEncoder(image_size, image_channels, static_features, history_features, history_len, patch_size=16, dim=128, embedding_dim=256, depth=4, heads=4, dim_head=32, dropout=0.0, fusion="concat", contrastive_dim=128)`

### Output

- Embedding tensor of shape `(batch_size, embedding_dim)`.
- When `return_modalities=True`, also returns a dictionary with contrastive projections for `vision`, `tabular`, and `history`.

### `pretrain_catchment_encoder`

`pretrain_catchment_encoder(encoder, dataset, epochs=30, batch_size=32, lr=3e-4, temperature=0.07, device="cpu", checkpoint_path=None)`

Runs InfoNCE pretraining over the paired modality projections.

### `extract_embeddings`

`extract_embeddings(encoder, dataset, batch_size=64, device="cpu", n_history_samples=1)`

Returns a tuple of `(site_ids, embedding_matrix)`.

## Fusion Helpers

### `MergingModel`

A generic wrapper for combining temporal and meta-data tensors with a selected method.

### `GatedFusion`

`GatedFusion(hidden_dim, context_dim)`

Applies a learned gate to inject static context into a temporal sequence.

## CrossViViT

### `RoCrossViViT`

A multimodal video / time-series transformer requiring image size, patch size, and a time-coordinate encoder.

Important constructor groups:

- vision: `image_size`, `patch_size`, `ctx_channels`, `dim`, `depth`, `heads`, `dim_head`.
- time series: `num_time_series`, `forecast_history`, `out_dim`.
- decoder: `decoder_dim`, `decoder_depth`, `decoder_heads`, `decoder_dim_head`.
- masking / positional encoding: `ctx_masking_ratio`, `ts_masking_ratio`, `pe_type`, `freq_type`.

## Neural ODE And ODE Forecasting

### `NeuralODE`

`NeuralODE(dynamics, method="dopri5", rtol=1e-4, atol=1e-5, adjoint=False, solver_options=None)`

Integrates a dynamics module over a 1D time grid.

### `ODEForecast`

`ODEForecast(n_time_series, n_target, forecast_length, dynamics_params, solver_params=None, encoder_hidden_dim=32, encoder_layers=1, time_step=1.0)`

Encodes the history with a GRU, integrates the hidden state with `NeuralODE`, and decodes the forecast trajectory.

## GR4 Hydrology

### `GR4Dynamics`

`GR4Dynamics(x1_init=300.0, x2_init=0.0, x3_init=100.0, x4_init=24.0, n_routing_reservoirs=3, learnable=True, interpolation="previous")`

Important methods:

- `set_parameters(params)`
- `gr4_parameters()`
- `streamflow(state)`
- `actual_et(t, state)`

### `GR4ParameterHead`

`GR4ParameterHead(embedding_dim=256, hidden_dim=64, x1_range=(10.0, 2000.0), x2_range=(-10.0, 10.0), x3_range=(5.0, 500.0), x4_range=(0.5, 120.0))`

Maps catchment embeddings into bounded GR4 parameters.

### `EffectiveForcingGenerator`

`EffectiveForcingGenerator(n_met_features, seq_len, context_dim=256, dim=64, depth=2, heads=4, dim_head=32, dropout=0.0, encoder_type="crossformer", seg_len=3)`

Builds non-negative effective forcing from raw meteorology plus context.

### `HybridGR4Model`

`HybridGR4Model(n_met_features, seq_len, context_dim=256, dim=64, depth=2, heads=4, n_routing_reservoirs=3, solver_params=None, parameter_head_params=None, encoder_type="crossformer")`

Returns a dictionary with:

- `flow`: simulated streamflow.
- `forcing`: effective forcing tensor.
- `parameters`: bounded GR4 parameters.
- `states`: integrated ODE states.

## Losses

### `InfoNCELoss`

`InfoNCELoss(temperature=0.07, symmetric=True)`

Used for contrastive alignment of the catchment modality embeddings.

### `NSELoss`

`NSELoss(eps=1e-6)`

Hydrology loss that minimizes 1 - NSE.

### `MaskedMSELoss`

A masked regression loss for sparse supervision such as intermittent satellite observations.
