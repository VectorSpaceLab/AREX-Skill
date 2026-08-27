# Network and Layer Recipes

## Auto network

Use `network='auto'` or `network=dict(type='auto', size=64, depth=2)` when the user does not need a custom architecture. This is the safest quickstart path for PPO/DQN-style examples.

## Layered network

A list is shorthand for a layered/sequential network:

```python
network = [
    dict(type='dense', size=64, activation='tanh'),
    dict(type='dense', size=64, activation='tanh'),
]
```

The action/value output layer is implicit. Do not add an output layer just to match the action dimension unless Tensorforce documentation for the selected policy says to do so.

## Multi-input DAG with register/retrieve

For nested states, use `retrieve` to select a component and `register` to name intermediate tensors:

```python
network = [
    [
        dict(type='retrieve', tensors=['observation']),
        dict(type='conv2d', size=32),
        dict(type='flatten'),
        dict(type='register', tensor='obs-embedding'),
    ],
    [
        dict(type='retrieve', tensors=['attributes']),
        dict(type='embedding', size=32),
        dict(type='flatten'),
        dict(type='register', tensor='attr-embedding'),
    ],
    [
        dict(type='retrieve', aggregation='concat', tensors=['obs-embedding', 'attr-embedding']),
        dict(type='dense', size=64),
    ],
]
```

## Preprocessing

State preprocessing may be a string (`'linear_normalization'`) or a module/list. Common preprocessing layers include clipping, deltafier, image, sequence, and normalization. Check that the incoming state spec has bounds when using linear normalization; Tensorforce warns when bounds are missing.

## Keras layers

The `keras` layer route is for users who intentionally provide compatible Keras layers. Validate TensorFlow/Keras versions before blaming Tensorforce if a custom Keras object cannot trace or serialize.
