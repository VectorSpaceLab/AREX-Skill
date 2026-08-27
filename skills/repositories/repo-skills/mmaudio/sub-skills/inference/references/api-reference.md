# API Reference

Evidence labels used for this reference: demo.py, gradio_demo.py,
mmaudio/eval_utils.py, mmaudio/model/networks.py, mmaudio/model/sequence_config.py.

## Registry and model configuration

### `ModelConfig`
```python
@dataclasses.dataclass
class ModelConfig:
    model_name: str
    model_path: Path
    vae_path: Path
    bigvgan_16k_path: Optional[Path]
    mode: str
    synchformer_ckpt: Path = Path('./ext_weights/synchformer_state_dict.pth')
```

#### Behavior
- `seq_cfg` returns `CONFIG_16K` when `mode == '16k'`, otherwise `CONFIG_44K`.
- `download_if_needed()` ensures the checkpoint, VAE, optional BigVGAN file, and Synchformer checkpoint exist and match the expected MD5 files.
- `all_model_cfg` maps the public names to configs:
  - `small_16k`
  - `small_44k`
  - `medium_44k`
  - `large_44k`
  - `large_44k_v2`

### `get_my_mmaudio`
```python
def get_my_mmaudio(name: str, **kwargs) -> MMAudio
```
- Returns the model constructor for the named variant.
- Raises `ValueError` for an unknown name.

## Core generation API

### `generate`
```python
def generate(
    clip_video: Optional[torch.Tensor],
    sync_video: Optional[torch.Tensor],
    text: Optional[list[str]],
    *,
    negative_text: Optional[list[str]] = None,
    feature_utils: FeaturesUtils,
    net: MMAudio,
    fm: FlowMatching,
    rng: torch.Generator,
    cfg_strength: float,
    clip_batch_size_multiplier: int = 40,
    sync_batch_size_multiplier: int = 40,
    image_input: bool = False,
) -> torch.Tensor
```

#### Expected inputs
- `clip_video` and `sync_video` should already include a batch dimension when used from the demos.
- `text` is a list of prompts, one per batch element.
- If `negative_text` is supplied, its length must equal the batch size.
- `image_input=True` tells the function to treat the clip path as a single image-style conditioning source. Sync video is ignored in that mode.

#### What it does
1. Encodes clip-video features with CLIP unless `clip_video` is `None`.
2. Encodes sync-video features with Synchformer unless `sync_video` is `None` or `image_input=True`.
3. Encodes text and negative text.
4. Samples latent audio with the flow model.
5. Decodes and vocodes the audio back to waveform space.

#### Practical notes
- The default batch-size multipliers are intentionally high for throughput.
- Lower them if custom programmatic inference hits memory pressure.
- If `clip_video` is `None`, the model uses its empty clip sequence.
- If `sync_video` is `None`, the model uses its empty sync sequence.

## Media loading and reconstruction

### `load_video`
```python
def load_video(video_path: Path, duration_sec: float, load_all_frames: bool = True) -> VideoInfo
```

#### Behavior
- Reads frames at the CLIP and Synchformer frame rates.
- Resizes CLIP frames to `384 x 384`.
- Resizes the Synchformer side to `224` on the shorter edge and center-crops to `224 x 224`.
- Truncates the requested duration if the source video is shorter.
- Returns a `VideoInfo` object containing:
  - `duration_sec`
  - `fps`
  - `clip_frames`
  - `sync_frames`
  - `all_frames` when `load_all_frames=True`

#### Shape facts
- CLIP stream: `8 FPS`.
- Synchformer stream: `25 FPS`.
- If the source video is below `25 FPS`, frames are duplicated to satisfy the Synchformer stream.
- The returned tensors are then batched by the caller with `unsqueeze(0)`.

### `load_image`
```python
def load_image(image_path: Path) -> VideoInfo
```

#### Behavior
- Uses the same CLIP and Synchformer transforms as `load_video`.
- Treats the image as a single frame source.
- Returns an image-backed `VideoInfo`-style object for the experimental UI path.

### `make_video`
```python
def make_video(video_info: VideoInfo, output_path: Path, audio: torch.Tensor, sampling_rate: int)
```

#### Behavior
- Re-encodes the input frames with the generated audio.
- Requires frame data that can be reconstructed from `video_info`.
- Used by both the CLI demo and the Gradio UI when an MP4 should be written.

## Sequence and duration contract

### `SequenceConfig`
```python
@dataclasses.dataclass
class SequenceConfig:
    duration: float
    sampling_rate: int
    spectrogram_frame_rate: int
    latent_downsample_rate: int = 2
    clip_frame_rate: int = 8
    sync_frame_rate: int = 25
    sync_num_frames_per_segment: int = 16
    sync_step_size: int = 8
    sync_downsample_rate: int = 2
```

#### Derived properties
- `latent_seq_len`
- `clip_seq_len`
- `sync_seq_len`
- `num_audio_frames`

### `MMAudio.update_seq_lengths`
```python
def update_seq_lengths(self, latent_seq_len: int, clip_seq_len: int, sync_seq_len: int) -> None
```

#### Why it matters
- The model reinitializes rotary embeddings when the sequence lengths change.
- Call it after changing `seq_cfg.duration` and before calling `generate`.
- Failing to update the lengths can produce assertion failures or duration mismatches.

## Reference duration facts

At the default `duration = 8.0` seconds:
- `CONFIG_16K`: `latent_seq_len = 250`, `clip_seq_len = 64`, `sync_seq_len = 192`, `num_audio_frames = 128000`
- `CONFIG_44K`: `latent_seq_len = 345`, `clip_seq_len = 64`, `sync_seq_len = 192`, `num_audio_frames = 353280`

Important consequences:
- The visual sequence lengths are fixed by duration, not by the model size.
- Only the audio sampling rate changes between the 16 kHz and 44.1 kHz paths.

## Programmatic inference recipe
```python
import torch
from mmaudio.eval_utils import all_model_cfg, generate, load_video
from mmaudio.model.flow_matching import FlowMatching
from mmaudio.model.networks import get_my_mmaudio
from mmaudio.model.utils.features_utils import FeaturesUtils

model = all_model_cfg['large_44k_v2']
model.download_if_needed()
seq_cfg = model.seq_cfg

net = get_my_mmaudio(model.model_name).to(device, dtype).eval()
net.load_weights(torch.load(model.model_path, map_location=device, weights_only=True))

video_info = load_video(video_path, duration)
clip_frames = video_info.clip_frames.unsqueeze(0)
sync_frames = video_info.sync_frames.unsqueeze(0)
seq_cfg.duration = video_info.duration_sec
net.update_seq_lengths(seq_cfg.latent_seq_len, seq_cfg.clip_seq_len, seq_cfg.sync_seq_len)

fm = FlowMatching(min_sigma=0, inference_mode='euler', num_steps=25)
feature_utils = FeaturesUtils(
    tod_vae_ckpt=model.vae_path,
    synchformer_ckpt=model.synchformer_ckpt,
    enable_conditions=True,
    mode=model.mode,
    bigvgan_vocoder_ckpt=model.bigvgan_16k_path,
    need_vae_encoder=False,
).to(device, dtype).eval()

audios = generate(
    clip_frames,
    sync_frames,
    [prompt],
    negative_text=[negative_prompt],
    feature_utils=feature_utils,
    net=net,
    fm=fm,
    rng=torch.Generator(device=device).manual_seed(seed),
    cfg_strength=4.5,
)
```

## Common programmatic edge cases
- `negative_text=None` is allowed and uses the model's empty-string conditioning path.
- `image_input=True` skips sync encoding and expands the clip features across the clip sequence.
- `load_all_frames=False` saves memory but makes reconstruction via `make_video` unavailable.
