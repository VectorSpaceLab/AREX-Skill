# Data and Demo Troubleshooting

## Dataset download scripts fail

**Symptoms**
- `download_modelnet40.sh` or a demo that fetches data cannot proceed.

**Likely cause**
- Network access is unavailable or the dataset host is blocked.

**Fix**
- Treat the example as reference-only until the data is already present.
- Do not make the default runtime helper download anything.

## Open3D or visualization dependencies are missing

**Symptoms**
- Indoor, reconstruction, or completion demos fail on import.

**Likely cause**
- Optional visualization or point-cloud dependencies were not installed.

**Fix**
- Install the missing optional dependency only when you actually need that demo.
- Keep the sparse-tensor and layer workflows separate from visualization setup.

## ModelNet40 demo uses too much memory

**Symptoms**
- Classification examples become very memory-hungry.

**Likely cause**
- The example caches large amounts of data in memory.

**Fix**
- Use the example as a recipe, not as a drop-in smoke test.
- Prefer the synthetic training batch checker before touching the real dataset.

## Segmentation or reconstruction output looks misaligned

**Symptoms**
- Predictions do not line up with the input point cloud.

**Likely cause**
- Quantization size, slicing, or coordinate handling is inconsistent.

**Fix**
- Revisit the sparse-tensor data sub-skill for coordinate and slicing semantics.
- Confirm that the network returns the expected sparse output before visualization.

## Multi-worker dataloaders fail in training

**Symptoms**
- Training crashes when using more than one worker.

**Likely cause**
- SparseTensor construction or coordinate-manager state is happening in worker processes instead of the main process.

**Fix**
- Follow the training recipe: collate in workers, construct the sparse tensor in the main process.

## GPU OOM during training

**Symptoms**
- CUDA memory grows or fluctuates across batches.

**Likely cause**
- Sparse batches vary in active coordinate count.

**Fix**
- Clear cache periodically in the training loop.
- Reduce batch size or use a smaller voxel size if the data is too dense.
