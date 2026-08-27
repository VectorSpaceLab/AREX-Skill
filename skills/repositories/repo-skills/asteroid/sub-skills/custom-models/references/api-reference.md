# Asteroid custom-model API surface

## Core base classes

- `asteroid.models.base_models.BaseModel`
  - serializable model base class
  - defines `sample_rate`, `in_channels`, `serialize()`, `from_pretrained()`, and separation helpers
- `asteroid.models.base_models.BaseEncoderMaskerDecoder`
  - encoder / masker / decoder base for waveform-to-waveform models
- `asteroid.models.base_models.BaseTasNet`
  - compatibility alias for encoder-masker-decoder models
- `asteroid.masknn.base.BaseUNet`
- `asteroid.masknn.base.BaseDCUMaskNet`

## Ready-to-use model families

The repo exposes these families through `asteroid.models` and `asteroid.get(...)`:

- ConvTasNet
- DPRNNTasNet
- DPTNet
- LSTMTasNet
- DeMask
- DCUNet
- DCCRNet
- SuDORMRFNet
- SuDORMRFImprovedNet
- FasNetTAC
- XUMX

## Mask-network and block helpers

- `asteroid.masknn.activations`
- `asteroid.masknn.norms`
- `asteroid.masknn.convolutional`
- `asteroid.masknn.recurrent`
- `asteroid.masknn.attention`
- `asteroid.masknn.tac`
- `asteroid.complex_nn`

The key pattern is:

1. pick or build an encoder
2. create a masker or separator block
3. decode back to waveform space
4. keep `get_config()` / `get_model_args()` round-trippable

## DSP helpers often used in custom models

- `asteroid.dsp.LambdaOverlapAdd`
- `asteroid.dsp.DualPathProcessing`
- `asteroid.dsp.mixture_consistency`
- `asteroid.dsp.vad.ebased_vad`
- `asteroid.dsp.beamforming`

## Registry helpers

- `asteroid.models.register_model(...)`
- `asteroid.masknn.activations.register_activation(...)`
- `asteroid.masknn.norms.register_norm(...)`
- `asteroid.engine.optimizers.register_optimizer(...)`
- `asteroid.engine.optimizers.get(...)`
- `asteroid.utils.prepare_parser_from_dict(...)`
- `asteroid.utils.parse_args_as_dict(...)`

## Recurrent masker constructor notes

- `asteroid.masknn.recurrent.DPRNN` uses `n_repeats` for repeated dual-path blocks; do not pass a `n_blocks` keyword.
- Use `chunk_size` and `hop_size` for the dual-path chunking geometry.
- `LSTMMasker` uses `n_layers`, while DPRNN uses `num_layers` for the internal RNN depth.

## Shape and serialization rules to remember

- Waveform tensors are usually time-last.
- Many model helpers accept 1D, 2D, or 3D inputs and normalize them internally.
- `BaseModel.serialize()` should produce a dict that `from_pretrained()` can load again.
- `get_model_args()` should exclude checkpoint state and capture only the constructor args needed to rebuild the model.
- TorchScript-friendly helpers such as `jitable_shape` and `script_if_tracing` exist for tracing-sensitive code.

## Good reference tests

- `tests/masknn/*.py`
- `tests/dsp/*.py`
- `tests/jit/*.py`
- `tests/utils/*.py`
- `tests/models/models_test.py`
