# StyleTTS2 inference workflows

## Shared runtime shape

Both pretrained demos follow the same structure:

1. Choose `device = 'cuda' if torch.cuda.is_available() else 'cpu'`.
2. Load `TextCleaner` from `text_utils.py`. It is a character-level symbol map, so
   unsupported characters are dropped.
3. Load phonemization with `phonemizer.backend.EspeakBackend(
   language='en-us', preserve_punctuation=True, with_stress=True
   )`.
4. Tokenize phonemized text with NLTK `word_tokenize`.
5. Load ASR, F0, and PL-BERT helper models from the bundled `Utils/` assets.
6. Build the StyleTTS2 model from the family config, load the pretrained
   checkpoint, move modules to the selected device, and switch to eval mode.
7. Run a diffusion sampler with `DiffusionSampler` + `ADPM2Sampler` +
   `KarrasSchedule`.
8. Decode to a 24 kHz waveform.

Common preprocessing details from the notebooks:

```python
to_mel = torchaudio.transforms.MelSpectrogram(
    n_mels=80, n_fft=2048, win_length=1200, hop_length=300
)
mean, std = -4, 4
```

The reference-audio path trims silence with `librosa.effects.trim(..., top_db=30)`
and resamples or loads at 24 kHz before mel encoding.

The output contract for both workflows is a 24 kHz waveform array, not a
spectrogram.

## LJSpeech single-speaker inference

Use this path for the single-speaker pretrained model.

### Load order

1. Read `Models/LJSpeech/config.yml`.
2. Load the bundled helper models from the config values:
   - `load_ASR_models(ASR_path, ASR_config)`
   - `load_F0_models(F0_path)`
   - `load_plbert(PLBERT_dir)`
3. Build the model with `build_model(recursive_munch(config['model_params']),
   text_aligner, pitch_extractor, plbert)`.
4. Load `Models/LJSpeech/epoch_2nd_00100.pth` and copy matching entries into the
   model modules.
5. Instantiate the sampler:

```python
from Modules.diffusion.sampler import DiffusionSampler, ADPM2Sampler, KarrasSchedule

sampler = DiffusionSampler(
    model.diffusion.diffusion,
    sampler=ADPM2Sampler(),
    sigma_schedule=KarrasSchedule(
        sigma_min=0.0001,
        sigma_max=3.0,
        rho=9.0,
    ),
    clamp=False,
)
```

### Core synthesis function

The notebook defines:

```python
def inference(text, noise, diffusion_steps=5, embedding_scale=1):
```

Important semantics:

- `noise` is usually `torch.randn(1, 1, 256).to(device)`.
- `diffusion_steps=5` is the notebook default; larger values improve quality
  but slow inference.
- `embedding_scale=1` is the default classifier-free guidance scale.
- The function phonemizes, tokenizes, cleans symbols, predicts style from the
  diffusion sampler, and decodes directly to waveform.

### Long-form synthesis

The long-form helper is:

```python
def LFinference(text, s_prev, noise, alpha=0.7, diffusion_steps=5, embedding_scale=1):
```

Use it when synthesizing multiple sentence chunks.

- `s_prev` carries the previous sentence style forward.
- The notebook blends the previous and current style with a convex mixture:
  `s_pred = alpha * s_prev + (1 - alpha) * s_pred`.
- Larger `alpha` means more carry-over from the previous segment and smoother
  boundaries.
- The notebook splits passages on periods, appends the period back to each chunk,
  and concatenates the resulting waveforms with `np.concatenate`.

The LJSpeech notebook also removes literal double quotes before phonemization in
its helper.

## LibriTTS multi-speaker inference

Use this path for zero-shot speaker adaptation and style transfer.

### Load order

1. Read `Models/LibriTTS/config.yml`.
2. Load the same bundled helper models from the config values.
3. Build the model from `config['model_params']`.
4. Load `Models/LibriTTS/epochs_2nd_00020.pth`.
5. Prepare reference audio with `compute_style(reference_wav)`.

`compute_style` loads a 24 kHz reference wav, trims silence, builds an 80-bin mel
spectrogram, and returns a concatenated style tensor from the style encoder and
predictor encoder.

### Core synthesis function

The notebook defines:

```python
def inference(text, ref_s, alpha=0.3, beta=0.7, diffusion_steps=5, embedding_scale=1):
```

Semantics of the main controls:

- `ref_s` is the style tensor from `compute_style(reference_wav)`.
- `alpha` blends the sampled timbre with the reference timbre: `alpha=0` keeps the reference timbre, while `alpha=1` uses the sampled timbre.
- `beta` blends the sampled prosody with the reference prosody: `beta=0` keeps the reference prosody, while `beta=1` uses the sampled prosody.
- Higher `alpha` and `beta` move the result toward the sampled style and usually increase variation.
- Lower `alpha` and `beta` keep the synthesis closer to the reference audio and more deterministic.
- `embedding_scale` again acts as classifier-free guidance.

Notebook defaults and common settings:

- Default balanced synthesis: `alpha=0.3`, `beta=0.7`, `diffusion_steps=5`,
  `embedding_scale=1`.
- More expressive speech often uses `embedding_scale=2`.
- Pronounced style transfer uses settings such as `alpha=0.5`, `beta=0.9`.
- Diversity sweeps in the notebook demonstrate:
  - `alpha=0.1`, `beta=0.3` for less diverse output.
  - `alpha=0.5`, `beta=0.95` for more diverse output.
  - `alpha=1`, `beta=1` for maximum sampled-style diversity.
  - `alpha=0`, `beta=0` for no variation.

### Long-form synthesis and style smoothing

The LibriTTS notebook defines:

```python
def LFinference(text, s_prev, ref_s, alpha=0.3, beta=0.7, t=0.7,
                diffusion_steps=5, embedding_scale=1):
```

Key behavior:

- `s_prev` carries the previous segment style.
- `t` mixes the previous and newly sampled style before the `alpha`/`beta`
  blend.
- The notebook uses `t=0.7` and then applies the same `alpha` and `beta`
  style controls.
- This is the preferred path for long passages when you want smoother segment
  transitions.

The notebook also includes a style-transfer helper `STinference(text, ref_s,
ref_text, alpha=0.3, beta=0.7, diffusion_steps=5, embedding_scale=1)` that
phonemizes both the target text and a reference text before decoding.

## Expected audio shape

- Sample rate: 24,000 Hz.
- Type: mono waveform array.
- Common display path: `IPython.display.Audio(wav, rate=24000, normalize=False)`.
- Long-form output is usually concatenated across sentence chunks after each
  call returns a waveform segment.
