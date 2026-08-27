# Multimodal And Physics Workflows

## 1. Build A Catchment Embedding Dataset

1. Prepare one `.npz` file per site.
2. Include `image`, `static`, and `history` arrays.
3. Keep the image dimensions divisible by the chosen patch size.
4. Instantiate `CatchmentEmbeddingDataset`.
5. Use the dataset to inspect a single sample before any training.

## 2. Pretrain The Catchment Encoder

1. Create a `CatchmentEncoder` with matching image, static, and history dimensions.
2. Run `pretrain_catchment_encoder` for a small number of epochs first.
3. Save the checkpoint if the embedding loss decreases.
4. Extract site embeddings with `extract_embeddings`.

### Why this stage matters

The model learns a shared representation across imagery, tabular attributes, and time-series history before those features are handed to a hydrology head or another downstream consumer.

## 3. Use Fusion Helpers

Use `GatedFusion` when you want a compact context-injection block.

Use `MergingModel` when you want to switch between fusion methods while keeping a single outer interface.

## 4. Run A Hybrid GR4 Forecast

1. Feed a catchment embedding into `GR4ParameterHead`.
2. Feed meteorology and context into `EffectiveForcingGenerator`.
3. Integrate the GR4 state with `HybridGR4Model` or a direct `NeuralODE` call.
4. Confirm that the forcing tensor has two channels: precipitation and PET.
5. Confirm that the ODE time grid is strictly increasing.

```python
from flood_forecast.multi_models.catchment_embedding import CatchmentEncoder
from flood_forecast.multi_models.contrastive_pretrain import pretrain_catchment_encoder, extract_embeddings
from flood_forecast.ode.physics.hydrology import HybridGR4Model
```

## 5. Use CrossViViT

CrossViViT is the path to choose when the task is a vision/time-series multimodal forecasting problem rather than a hydrology-only one.

Checklist:

- Set `image_size` and `patch_size` so the images divide evenly into patches.
- Provide a proper time-coordinate encoder.
- Keep the context and time-series channel counts consistent with the constructor.
- Watch the `ctx_masking_ratio` and `ts_masking_ratio` bounds.

## 6. Safe Smoke Strategy

Run `python scripts/synthetic_catchment_smoke.py` to create a synthetic `.npz` dataset and exercise:

- dataset loading,
- catchment encoder forward / contrastive pretraining,
- embedding extraction,
- fusion helper usage,
- hybrid GR4 forward,
- direct NeuralODE integration.

Keep the fixture small so the smoke stays CPU-safe and quick.
