# Components, decoders, and losses

SpeechBrain exposes many reusable modules under `speechbrain.nnet`, `speechbrain.lobes`, `speechbrain.processing`, and `speechbrain.decoders`. Use this reference for component-level design before building or modifying a recipe.

## Component families

- `speechbrain.nnet`: generic layers, activations, attention, CNN/RNN blocks, losses, normalization, pooling, schedulers, embeddings, adapters, diffusion, quantizers, containers.
- `speechbrain.lobes`: higher-level speech blocks such as features, downsampling, beamforming, and model-specific modules.
- `speechbrain.processing`: signal processing, features, multi-mic processing, decomposition, PLDA/LDA, vocal features.
- `speechbrain.decoders`: CTC, seq2seq, transducer, language-model scoring, beam-search utilities.
- `speechbrain.utils`: training/logging/distributed/metric/checkpoint utilities.

## Wiring pattern in recipes

HyperPyYAML constructs modules:

```yaml
modules:
    compute_features: !new:speechbrain.lobes.features.Fbank
        sample_rate: 16000
        n_mels: 40
    model: !new:speechbrain.nnet.linear.Linear
        input_size: 40
        n_neurons: 10
```

The `Brain` subclass consumes them:

```python
feats = self.modules.compute_features(wavs)
outputs = self.modules.model(feats)
loss = self.hparams.compute_cost(outputs, targets, lengths)
```

## Decoder selection

- Use CTC decoders for CTC acoustic models and blank-token outputs.
- Use seq2seq/attention decoders for encoder-decoder models.
- Use transducer decoders for RNNT/transducer recipes.
- Add language-model scoring/rescoring only when tokenizer/vocabulary/LM artifacts are aligned.

Before decoding, validate:

- Logit shape and batch/time ordering.
- Relative lengths correspond to the logit time dimension.
- Tokenizer or label encoder index mapping matches training.
- Blank/BOS/EOS indices match hparams.

## Loss selection

Loss functions often live in `speechbrain.nnet.losses` or are constructed through recipe hparams. Common tasks:

- ASR CTC: CTC loss plus CTC decoding metrics.
- Classification/speaker ID: cross entropy or negative log likelihood.
- VAD: binary cross entropy with frame-level targets.
- Enhancement/separation: signal-domain or metric-learning losses.
- G2P/seq2seq: sequence NLL with target lengths.

## Component-level checks

- Write a synthetic tensor shape test before running a full recipe.
- Confirm modules move to `self.device` through `Brain` / `Pretrained` machinery.
- Keep random transforms seeded when comparing outputs.
- If using complex/quaternion/adapters/streaming features, add focused tests from the relevant unit/integration patterns before changing a full recipe.
