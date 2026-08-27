# Model-family overview

PyHealth exports a large catalog under `pyhealth.models`, including:

- **Classical/tabular:** `LogisticRegression`, `CaliForest`.
- **Sequence/recurrent:** `RNN`, `RETAIN`, `Deepr`, `TCN`, `AdaCare`, `ConCare`,
  `StageNet`, `GRASP`, `SparcNet`, and related layers.
- **Attention/transformer:** `Transformer`, `TransformersModel`, `BIOT`,
  `EHRMamba`, `JambaEHR`, `ContraWR`.
- **Graph/clinical graph:** `GAT`, `GCN`, `GraphCare`, `GAMENet`, `SafeDrug`,
  `MoleRec`, `MedLink`; graph paths may need `[graph]`.
- **Multimodal/embeddings:** `EmbeddingModel`, `TextEmbedding`,
  `VisionEmbeddingModel`, `UnifiedMultimodalEmbeddingModel`, `MedFuse`.
- **Generative:** `GAN`, `VAE`, `HALO`, `GPT2`, `PromptEHR`, `MedGAN`, `CorGAN`.

This is a routing catalog, not a promise that every class fits every dataset.
Use the model's constructor and source/API page to confirm expected feature
keys, token processors, dimensions, task mode, and optional resources.

A good baseline comparison keeps dataset/task/split/label semantics fixed and
changes one model family at a time. Record random seed, package version,
processor configuration, device, optimizer, epochs/steps, metric monitor, and
checkpoint path.
