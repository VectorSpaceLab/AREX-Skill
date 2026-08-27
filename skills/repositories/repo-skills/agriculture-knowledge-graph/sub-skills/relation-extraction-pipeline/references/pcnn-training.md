# TensorFlow PCNN training stack

The relation model is an older TensorFlow implementation inspired by OpenNRE. Treat it as a reference/optional training workflow unless a task explicitly asks for TensorFlow 1.x environment preparation and training.

## Architecture summary

The agriculture relation-extraction model uses this flow:

1. Load `train_dataset.json`, `test_dataset.json`, `word2vec.json`, and `rel2id.json` with `json_file_data_loader`.
2. For the agriculture dataset, replace whitespace in each sentence with underscores, add the head/tail entity words to Jieba, segment the sentence, and map words to vector ids.
3. Build position embeddings from the head/tail character offsets, sentence length arrays, and PCNN piecewise masks.
4. Encode word+position embeddings with a 1D convolution and piecewise max pooling.
5. Aggregate instances with the `bag_average` selector.
6. Train a softmax classifier with class weights derived from relation counts.
7. Test by scoring non-NA relations for entity-pair bags and computing precision/recall AUC.

## Files and responsibilities

| Component | Responsibility | Key implementation facts |
| --- | --- | --- |
| `config.py` | Dataset paths and hyperparameters. | `root_path = os.getcwd()`, so run from the algorithm directory. `model.gpu_list = [0]`, `batch_size = 16`, `max_length = 60`, encoder defaults to `pcnn`. |
| `train.py` | Builds data loaders, model class, and training call. | Has a dataset-name trap: it sets `dataset = "nyt"`, stores CLI arg in unused `data_set`, checks the `nyt` directory, but actually loads agriculture train/test paths. |
| `module/data_loader.py` | JSON-to-array preprocessing, Jieba segmentation, bag scopes, batch generation. | Detects dataset behavior from the parent directory basename (`agriculture` or `nyt`). Writes `_processed_data` cache in the current working directory. |
| `module/network/embedding.py` | Word and position embeddings. | Uses `tf.contrib.layers.xavier_initializer`; adds UNK and BLANK rows at graph build time. |
| `module/network/encoder.py` | PCNN convolution and piecewise pooling. | Uses `tf.layers.conv1d`, mask ids 0/1/2/3, and a max-pooling offset trick. |
| `module/network/selector.py` | Bag-level average selector and logits. | Iterates over `scope.shape[0]`; batch dimensions must be statically known. |
| `module/network/classifier.py` | Weighted softmax cross entropy. | Uses relation-count weights and TensorFlow summary scalar. |
| `module/framework.py` | Multi-GPU tower setup, training loop, testing, checkpoint/test-result output. | Requires `batch_size % len(gpu_list) == 0`; sets `allow_soft_placement` and GPU memory growth. |

## Dataset path trap in `train.py`

Do not assume `python train.py agriculture` selects the agriculture dataset. The script contains this typo-like pattern:

```python
dataset = "nyt"
if len(sys.argv) > 1:
    data_set = sys.argv[1]  # not used later

dataset_dir = config.dir.dataset_dir[dataset]['root']
```

Later, the loaders are hard-coded to `config.dir.dataset_dir['agriculture']`. Consequences:

- The script checks for `data/nyt/` even when training agriculture data.
- Checkpoints are named with the `nyt` prefix unless the script is edited.
- Passing `agriculture` on the CLI does not fix the check.

For a real agriculture training run, patch the local training script or run a reviewed wrapper that sets `dataset = "agriculture"` before the directory check and model name construction. Do not create fake `data/nyt` directories as a long-term fix because it hides the configuration bug.

## Working-directory rules

Run training from the algorithm directory so `config.root_path` resolves dataset paths correctly:

```bash
cd relationExtraction/algorithm
python train.py
```

Before running, confirm `data/agriculture/` contains:

- `train_dataset.json`
- `test_dataset.json`
- `rel2id.json`
- `word2vec.json`
- `entity2id.json` (listed in config; not needed by the loader but useful for audits)

If you run from another directory, the code looks for `data/agriculture` under that other current directory.

## TensorFlow version constraints

This code expects TensorFlow 1.x APIs:

- `tf.placeholder`
- `tf.Session`
- `tf.ConfigProto`
- `tf.train.AdamOptimizer`
- `tf.variable_scope(..., reuse=tf.AUTO_REUSE)`
- `tf.contrib.layers.xavier_initializer`
- `tf.layers.conv1d`

TensorFlow 2.x compatibility mode is usually not enough because `tf.contrib` was removed. Use a TensorFlow 1.x-era runtime or adapt the model code to modern TensorFlow/Keras in a separate task.

## GPU and memory constraints

The default config sets `gpu_list = [0]`. Training places model towers under `/gpu:<id>` and uses `allow_soft_placement`; however, a dependable training claim should verify the intended CPU/GPU placement in the target runtime.

Watch for:

- `batch_size` must be divisible by the number of GPUs in `gpu_list`.
- Full Chinese word-vector JSON and resulting NumPy matrix can consume substantial RAM and disk.
- TensorFlow 1.x GPU wheels require old CUDA/cuDNN combinations and may not support newer GPUs without special builds.
- `per_process_gpu_memory_fraction = 1.0` can monopolize a GPU; adjust for shared systems before training.
- Multi-GPU graph/session handling is old and should be smoke-tested with a tiny dataset before long runs.

## Data-loader behavior that affects training

- Agriculture sentence tokenization uses Jieba after adding the head and tail entity words temporarily.
- Entity positions from JSON are character offsets in the raw sentence. If the offset does not land inside the entity span after whitespace handling, the loader raises a position error.
- Sentences longer than `max_length` are truncated; entity positions beyond the limit are clamped to `max_length - 1`, which can reduce signal.
- Unknown relation labels are mapped to `NA`, so schema validation should catch relation typos earlier.
- `_processed_data` is reused across runs unless missing or the cached array width disagrees with `max_length`; delete it after changing data or vectors.

## Minimal safe preflight before training

1. Run the schema checker over training rows and JSON files.
2. Use a tiny word-vector fixture or a limited vocabulary file to force the loader through preprocessing once.
3. Delete `_processed_data` and rerun the tiny loader when changing `max_length`, data splits, or vectors.
4. Patch the dataset-name bug in a local working copy.
5. Confirm TensorFlow 1.x import, GPU visibility if used, and batch divisibility.
6. Only then launch a full training run.

## Expected training outputs

By default, successful training writes:

- `checkpoint/<model_name>` checkpoint shards and checkpoint metadata.
- `summary/` TensorBoard summaries.
- `test_result/<model_name>_x.npy` and `<model_name>_y.npy` precision/recall arrays for the best epoch.

These are generated experiment artifacts. Do not bundle them into the runtime skill.
