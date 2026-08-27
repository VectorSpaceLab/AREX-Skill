# Model Recipes

Use this reference to select and safely adapt a higher-level TFLearn recipe. The original examples are evidence for architecture patterns, not runtime commands. For validation, build a tiny in-memory fixture with matching shape and dtype, run at most a few epochs, and keep network access disabled unless the user explicitly requests real dataset acquisition.

## Compatibility and Safety Gates

- Use a TensorFlow 1.x-compatible stack. The verified stack for these recipes was TFLearn `0.5.0` with TensorFlow `1.15.5`, NumPy `1.18.5`, and protobuf `3.20.3`.
- CPU execution is sufficient for API and graph behavior. CUDA only changes performance/device placement and is not required for the safe recipe smokes in this skill.
- Replace every dataset loader with in-memory fixtures unless the user explicitly asks for the full dataset and accepts download/time costs.
- Do not open interactive plots, notebooks, Gym render windows, or long-running training loops during smoke validation.

## Recipe Selection Matrix

| Need | Choose this family | Core TFLearn pattern | Data/download prerequisites | Safe adaptation |
|---|---|---|---|---|
| Fast tabular or flattened-image classifier | MLP / highway MLP | `input_data([None, n_features]) -> fully_connected/dropout/highway -> fully_connected(n_classes, 'softmax') -> regression(...) -> DNN` | MNIST loaders in examples download/cache real data. | Generate `float32` arrays such as shape `(8, 784)` or `(8, 2)` and one-hot labels. Use 4-16 units, `n_epoch=1-2`, `snapshot_epoch=False`. |
| Small vision classifier | CNN | `input_data([None, H, W, C]) -> conv_2d/max_pool_2d/local_response_normalization -> fully_connected/dropout -> regression` | MNIST/CIFAR/Oxford Flowers loaders can download data; preprocessing/augmentation may compute dataset statistics. | Use random or patterned arrays with shape `(4, 28, 28, 1)` or `(4, 32, 32, 3)`. Keep one or two convolution layers and a tiny dense head. Disable augmentation unless that is the workflow under test. |
| Large vision architecture study | AlexNet, VGG, GoogLeNet/Inception, Inception-ResNet, ResNet, ResNeXt, DenseNet, Network-in-Network | Repeated convolution blocks, branch merges, residual/dense blocks, global pooling, optimizer schedules, large checkpoints. | Usually downloads Oxford Flowers/CIFAR; often hundreds or thousands of epochs. | Treat as architecture templates only. Shrink image size/classes/filters/blocks, verify graph build and one batch. For residual/dense families, preserve the block ordering and downsample/merge pattern while reducing depth. |
| Image reconstruction or latent generation | Autoencoder / VAE | Encoder dense stack, decoder dense stack, custom VAE loss or reconstruction loss, optional generator model reusing the training session. | MNIST download; VAE uses SciPy for plotting grid values; examples use matplotlib. | Use 4-8 synthetic vectors with `original_dim` small, one hidden layer, no plotting. For VAE, verify the custom loss tensor and one `DNN.fit` call, then create a generator `DNN(decoder, session=training_model.session)` only if generation is needed. |
| Adversarial image generation | GAN / DCGAN | Separate generator and discriminator scopes, `get_layer_variables_by_scope`, custom losses, multiple train ops, sometimes `multi_target_data`. | MNIST download, matplotlib, long and unstable training. | Use tiny noise/image arrays, one or two dense/convolution layers, `placeholder=None` for loss-only train ops when appropriate, and `trainable_vars` to isolate generator/discriminator updates. Validate shapes, not sample quality. |
| Text classification | LSTM, bidirectional LSTM, dynamic LSTM, CNN sentence classifier | Token integer input, `embedding`, `lstm`/`bidirectional_rnn`/`conv_1d` branches, `pad_sequences`, `to_categorical`, `regression`. | IMDB loader downloads data. Dynamic LSTM assumes zero padding for length inference. | Use tiny integer token arrays with vocabulary size 5-20. Pad to short lengths such as 6 or 10. For dynamic LSTM, ensure padding value `0` and nonzero tokens for actual content. |
| Character or word generation | `SequenceGenerator` | One-hot sequence windows, LSTM stack, softmax vocabulary head, `SequenceGenerator(network, dictionary, seq_maxlen)`, then `.fit()` and `.generate()`. | City/Shakespeare examples download text; large LSTM sizes and many epochs. | Use inline strings such as repeated digits or a two-word fixture. Build a 2-32 unit LSTM. Ensure `dictionary` maps every seed token to a contiguous integer id and `seq_seed` length equals `seq_maxlen`. |
| Synthetic seq2seq | Legacy seq2seq | TensorFlow contrib legacy seq2seq ops, input/decoder slicing, custom sequence loss and metric, `DNN`. | Requires TensorFlow 1.x `tensorflow.contrib`; not portable to TF2. | Keep as TF1-only. Generate small integer sequences locally, reduce cell size and number of points, and avoid using it as a smoke for modern runtimes. |
| Wide/deep recommender or ranking prototype | Wide & deep recommender | Continuous `wide_X`, categorical `*_in` placeholders, embeddings for categorical columns, separate trainable vars for wide/deep heads, custom validation monitors. | Example downloads UCI Adult data and requires pandas. | Build a tiny local pandas DataFrame or direct dict arrays. Preserve input dict keys (`wide_X`, categorical `*_in`, target `Y`) and use a few categories. Prefer one epoch and no automatic downloads. |
| Reinforcement-learning Q-network architecture | Atari one-step Q-learning | Custom TensorFlow placeholders, TFLearn conv/fully-connected Q-network, target network variable assignment, RMSProp loss. | Requires Gym, Atari ROM/environment support, scikit-image preprocessing, rendering, threads, and very long training. | Do not run as a smoke. If needed, build the Q-network with a fake frame stack and tiny `num_actions`, then test `session.run` on dummy arrays. Use a real Gym environment only after explicit user approval. |
| Classical estimator-like workflows | KMeans, MiniBatchKMeans, RandomForestClassifier/Regressor | `tflearn.estimators` wrappers around TensorFlow contrib factorization/tensor_forest; scikit-learn-like `fit`, `predict`, `transform`, `evaluate`. | TensorFlow contrib is required; TF2 removes it. Queue runners and log directories are used internally. Forest code is marked WIP. | Use tiny 2-D `float32` arrays, set `n_clusters`, `n_features`, `n_classes`, `max_steps`, and small forest sizes explicitly. Prefer KMeans over forest when a minimal estimator check is needed. |
| Custom TensorFlow graph training | `TrainOp` / `Trainer` | Build placeholders, variables, loss, metric, and `tf.train.Optimizer` yourself; wrap with `tflearn.TrainOp`; train with `tflearn.Trainer.fit`. | No dataset downloads needed. | Use [`../scripts/custom_trainer_smoke.py`](../scripts/custom_trainer_smoke.py) as the safe pattern. |

## Adaptation Rules for Tiny Fixtures

1. **Preserve interface shapes.** A vision classifier that expects `[None, 32, 32, 3]` should receive a tiny `float32` array with the same rank. A text classifier that expects token ids should receive integer ids before embedding or one-hot windows before `SequenceGenerator`.
2. **Preserve target semantics.** Use one-hot labels for softmax/categorical cross-entropy. Use matching reconstruction targets for autoencoders. Use dict targets when named TFLearn target placeholders are present.
3. **Shrink before training.** Reduce filters, hidden units, recurrent units, sequence length, vocabulary size, blocks, epochs, and batch size. Smoke tests should prove API wiring, not quality.
4. **Disable costly side effects.** Prefer `tensorboard_verbose=0`, `snapshot_epoch=False`, small `snapshot_step` only when checkpointing is the behavior under test, and temporary output directories.
5. **Use named feeds for multi-input models.** GAN, DCGAN, wide/deep, and named vision examples are safer with dictionaries keyed by TFLearn input/target layer names than by creation order.
6. **Avoid plotting in validation.** Replace `matplotlib` display calls with assertions on tensor shapes, finite losses, or prediction array shapes.
7. **Treat estimator and contrib examples as TF1-only.** If the environment is TensorFlow 2.x, do not attempt to patch them in place; report the compatibility block from [Troubleshooting](troubleshooting.md).

## Optional Dependency Matrix

| Dependency | Used by recipe families | Install only when | Safe substitute |
|---|---|---|---|
| SciPy | VAE plotting/grid helpers | The task explicitly needs the VAE plotting distribution helpers. | Skip plotting and sample deterministic small latent arrays. |
| h5py | Large-data HDF5 examples | The task is about HDF5-backed data rather than model recipes. | Use in-memory NumPy arrays for recipe smokes. |
| Dask | Large array examples | The task is about Dask data streaming. | Use NumPy arrays. |
| pandas | Wide/deep recommender | The task needs tabular categorical preprocessing. | Build direct input dictionaries or a tiny DataFrame. |
| Gym/Atari and scikit-image | RL Atari example | The user explicitly requests real environment interaction and accepts install/render/runtime costs. | Build the Q-network with dummy frame tensors only. |
| matplotlib / notebook stack | Autoencoder, GAN, VAE, spiral notebook visuals | The deliverable includes plots. | Assert numeric outputs and shapes; use noninteractive backends if plots are unavoidable. |
| CUDA / tensorflow-gpu | Large training acceleration | The task requires performance benchmarking or GPU placement. | CPU is enough for graph/API smokes. |

## Validation Patterns

- **Custom TensorFlow graph integration:** run `python ../scripts/custom_trainer_smoke.py --epochs 2` from this `references/` directory, or `python scripts/custom_trainer_smoke.py --epochs 2` from the sub-skill root.
- **Sequence generation:** create an inline string or word list, use `string_to_semi_redundant_sequences` or a small manual one-hot fixture, train a tiny LSTM for a bounded number of epochs, call `generate(seq_length, temperature=0.5, seq_seed=seed)`, and assert the returned sequence contains the seed plus generated tokens.
- **Vision/NLP classifier:** build a tiny graph, run one `DNN.fit`, then assert `np.asarray(model.predict(X[:1])).shape` matches `[1, n_classes]`.
- **Estimator:** if TensorFlow contrib is available, fit on a tiny 2-D array with `max_steps` set; otherwise report a TF contrib compatibility block.
