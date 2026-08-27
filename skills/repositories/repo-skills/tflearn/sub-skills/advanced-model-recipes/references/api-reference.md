# API Reference for Advanced Recipes

This reference lists the API facts needed by the advanced recipes in this sub-skill. It is intentionally limited to recipe integration surfaces; detailed layer catalogs belong to `layers-and-ops`, and routine persistence/training mechanics belong to `training-and-persistence`.

## Verified Runtime Facts

- TFLearn distribution version used for inspection: `0.5.0`.
- Verified TensorFlow runtime: `1.15.5` CPU.
- Verified NumPy runtime: `1.18.5`.
- TensorFlow `1.15.5` required protobuf `3.20.3` in the verified environment; protobuf `4.x` caused descriptor errors.
- Modern Python/TensorFlow 2.x imports can fail because TFLearn relies on TensorFlow 1.x internals.

## Core Graph and Training Signatures

```python
tflearn.init_graph(seed=None, log_device=False, num_cores=0,
                   gpu_memory_fraction=0, soft_placement=True)

tflearn.input_data(shape=None, placeholder=None, dtype=tf.float32,
                   data_preprocessing=None, data_augmentation=None,
                   name='InputData')

tflearn.fully_connected(incoming, n_units, activation='linear', bias=True,
                        weights_init='truncated_normal', bias_init='zeros',
                        regularizer=None, weight_decay=0.001,
                        trainable=True, restore=True, reuse=False,
                        scope=None, name='FullyConnected')

tflearn.dropout(incoming, keep_prob, noise_shape=None, name='Dropout')

tflearn.regression(incoming, placeholder='default', optimizer='adam',
                   loss='categorical_crossentropy', metric='default',
                   learning_rate=0.001, dtype=tf.float32, batch_size=64,
                   shuffle_batches=True, to_one_hot=False, n_classes=None,
                   trainable_vars=None, restore=True, op_name=None,
                   validation_monitors=None, validation_batch_size=None,
                   name=None)

tflearn.merge(tensors_list, mode, axis=1, name='Merge')
```

## Model, Trainer, and Generator Signatures

```python
tflearn.DNN(network, clip_gradients=5.0, tensorboard_verbose=0,
            tensorboard_dir='/tmp/tflearn_logs/', checkpoint_path=None,
            best_checkpoint_path=None, max_checkpoints=None, session=None,
            best_val_accuracy=0.0)

DNN.fit(X_inputs, Y_targets, n_epoch=10, validation_set=None,
        show_metric=False, batch_size=None, shuffle=None,
        snapshot_epoch=True, snapshot_step=None, excl_trainops=None,
        validation_batch_size=None, run_id=None, callbacks=[])

DNN.predict(X)
DNN.save(model_file)
DNN.load(model_file, weights_only=False, **optargs)

tflearn.TrainOp(loss, optimizer, metric=None, batch_size=64, ema=0.0,
                trainable_vars=None, shuffle=True, step_tensor=None,
                validation_monitors=None, validation_batch_size=None,
                name=None, graph=None)

tflearn.Trainer.fit(feed_dicts, n_epoch=10, val_feed_dicts=None,
                    show_metric=False, snapshot_step=None,
                    snapshot_epoch=True, shuffle_all=None, dprep_dict=None,
                    daug_dict=None, excl_trainops=None, run_id=None,
                    callbacks=[])

tflearn.SequenceGenerator(network, dictionary=None, seq_maxlen=25,
                          clip_gradients=0.0, tensorboard_verbose=0,
                          tensorboard_dir='/tmp/tflearn_logs/',
                          checkpoint_path=None, max_checkpoints=None,
                          session=None)

SequenceGenerator.generate(seq_length, temperature=0.5, seq_seed=None,
                           display=False)
```

## Data Utility Signatures Used by Recipes

```python
tflearn.data_utils.load_csv(filepath, target_column=-1, columns_to_ignore=None,
                            has_header=True, categorical_labels=False,
                            n_classes=None)

tflearn.data_utils.to_categorical(y, nb_classes=None)

tflearn.data_utils.pad_sequences(sequences, maxlen=None, dtype='int32',
                                  padding='post', truncating='post', value=0.0)

tflearn.data_utils.string_to_semi_redundant_sequences(string, seq_maxlen=25,
                                                       redun_step=3,
                                                       char_idx=None)
```

## Advanced Helpers

- `tflearn.get_layer_variables_by_scope(scope_name)` returns model variables whose names include `scope_name + '/'`. Use it to isolate generator/discriminator or branch-specific variables.
- `tflearn.get_layer_variables_by_name(name)` returns variables collected under a TFLearn layer name.
- `tflearn.multi_target_data(name_list, shape, dtype=tf.float32)` creates multiple target placeholders, adds them to `tf.GraphKeys.TARGETS`, and concatenates them along axis `0`. This is useful for discriminator fake/real targets.
- `tflearn.variable(name, shape=None, dtype=tf.float32, initializer=None, regularizer=None, trainable=True, ..., restore=True)` creates TensorFlow variables with TFLearn initialization/regularization conventions.
- `tflearn.add_weights_regularizer(var, 'L2', weight_decay=...)` adds regularization losses for custom TensorFlow variables.

## Estimator Constructors and Caveats

The estimator classes are TF1/contrib-dependent and are not the same as TensorFlow Estimator APIs.

```python
from tflearn.estimators import KMeans, MiniBatchKMeans
from tflearn.estimators import RandomForestClassifier, RandomForestRegressor

KMeans(n_clusters, max_iter=300, init=RANDOM_INIT,
       distance=SQUARED_EUCLIDEAN_DISTANCE, metric=None,
       num_features=None, log_dir='/tmp/tflearn_logs/',
       global_step=None, session=None, graph=None, name=None)

MiniBatchKMeans(n_clusters, max_iter=300, init=RANDOM_INIT,
                distance=SQUARED_EUCLIDEAN_DISTANCE, metric=None,
                num_features=None, log_dir='/tmp/tflearn_logs/',
                global_step=None, session=None, graph=None, name=None)

RandomForestClassifier(n_estimators=10, max_nodes=100,
                       split_after_samples=25, n_classes=None,
                       n_features=None, metric=None,
                       log_dir='/tmp/tflearn_logs/', global_step=None,
                       session=None, graph=None, name=None)

RandomForestRegressor(n_estimators=10, max_nodes=100,
                      split_after_samples=25, n_features=None,
                      num_output=None, metric=None,
                      log_dir='/tmp/tflearn_logs/', global_step=None,
                      session=None, graph=None, name=None)
```

Estimator usage notes:

- `KMeans.fit(X, shuffle=True, display_step=500, n_jobs=1, max_steps=None)` accepts a 2-D array. Set `max_steps` in smokes.
- `MiniBatchKMeans.fit(X, batch_size=1024, shuffle=True, display_step=500, n_jobs=1, max_steps=None)` uses mini-batches. Use a batch size no larger than the tiny fixture.
- `RandomForestClassifier.predict(X)` returns class ids via `argmax` over forest scores; `predict_proba(X)` returns score/probability arrays.
- Random forest code is marked work-in-progress in the implementation and uses TensorFlow tensor_forest contrib internals.

## Shape and Feed Notes

- `input_data` prepends a batch dimension when a multi-dimensional shape does not start with `None`.
- `DNN.fit` and `SequenceGenerator.fit` can receive arrays, lists, or dictionaries. Dictionaries keyed by input/target names are safest for multi-input recipes.
- `validation_set` can be a tuple `(X_val, Y_val)` or a float less than `1.0` to split training data.
- `SequenceGenerator.generate(seq_length, ...)` returns the original seed plus generated content. For a string seed of length `seq_maxlen`, the returned string length is `seq_maxlen + seq_length`.
- `SequenceGenerator` requires `dictionary` entries for every token in `seq_seed`; missing tokens raise lookup errors during generation.
