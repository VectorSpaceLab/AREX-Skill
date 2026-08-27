# API Reference

Use this reference for constructor defaults and stateful layer conventions.
The installed package inspection confirmed these public signatures.

## Activations

- `ReLU()`
- `Sigmoid()`
- `Tanh()`
- `GELU(approximate=True)`

Other common activations in the module include `LeakyReLU`, `ELU`, `SELU`,
`Affine`, `Identity`, `Exponential`, `HardSigmoid`, and `SoftPlus`.

## Layers and modules

- `FullyConnected(n_out, act_fn=None, init='glorot_uniform', optimizer=None)`
- `Conv1D(out_ch, kernel_width, pad=0, stride=1, dilation=0, act_fn=None, init='glorot_uniform', optimizer=None)`
- `Conv2D(out_ch, kernel_shape, pad=0, stride=1, dilation=0, act_fn=None, optimizer=None, init='glorot_uniform')`
- `LSTMCell(n_out, act_fn='Tanh', gate_fn='Sigmoid', init='glorot_uniform', optimizer=None)`
- `Embedding(n_out, vocab_size, pool=None, init='glorot_uniform', optimizer=None)`
- `DotProductAttention(scale=True, dropout_p=0, init='glorot_uniform', optimizer=None)`

Useful module classes include `BidirectionalLSTM`, `WavenetResidualModule`,
`SkipConnectionIdentityModule`, `SkipConnectionConvModule`, and
`MultiHeadedAttentionModule`.

## Losses

- `SquaredError()`
- `CrossEntropy()`
- `VAELoss()`
- `WGAN_GPLoss(lambda_=10)`
- `NCELoss(n_classes, noise_sampler, num_negative_samples, optimizer=None, init='glorot_uniform', subtract_log_label_prob=True)`

## Optimizers

- `SGD(lr=0.01, momentum=0.0, clip_norm=None, lr_scheduler=None, **kwargs)`
- `AdaGrad(lr=0.01, eps=1e-07, clip_norm=None, lr_scheduler=None, **kwargs)`
- `RMSProp(lr=0.001, decay=0.9, eps=1e-07, clip_norm=None, lr_scheduler=None, **kwargs)`
- `Adam(lr=0.001, decay1=0.9, decay2=0.999, eps=1e-07, clip_norm=None, lr_scheduler=None, **kwargs)`

## Schedulers

- `ConstantScheduler(lr=0.01, **kwargs)`
- `ExponentialScheduler(initial_lr=0.01, stage_length=500, staircase=False, decay=0.1, **kwargs)`
- `NoamScheduler(model_dim=512, scale_factor=1, warmup_steps=4000, **kwargs)`
- `KingScheduler(initial_lr=0.01, patience=1000, decay=0.99, **kwargs)`

## Working conventions

- Layers and modules usually keep state in attributes such as `parameters`,
  `gradients`, `derived_variables`, and sometimes cached inputs.
- `fit` is not the usual neural-network entry point; use the layer's forward /
  backward / update style methods described in the source docs.
- If a task refers to a specific layer family, check the constructor names
  rather than assuming a framework-style API.
