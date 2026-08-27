# SpikingJelly data workflows

## Core mental model

Most neuromorphic datasets in `spikingjelly.datasets` inherit from `NeuromorphicDatasetFolder` and follow the same staged pipeline:

1. **Download or verify files** under `root/download`.
2. **Extract archives** under `root/extract`.
3. **Create a normalized raw dataset** under a raw root, usually `root/events_np`; SHD/SSC use `root/events_h5`.
4. **Build the requested representation** with a dataset builder.
5. **Load samples** through `torchvision.datasets.DatasetFolder` unless a dataset explicitly bypasses it.

The constructor-level options are validated by `NeuromorphicDatasetConfig`:

- `data_type='event'` returns raw event samples.
- `data_type='frame'` requires exactly one of `frames_number`, `duration`, or `custom_integrate_function`.
- `frames_number` also requires `split_by='time'` or `split_by='number'`.
- `duration` must be a positive integer and uses the dataset's timestamp unit.

## Verified DVS128Gesture contract

The prepared inspection environment verified the public signature and basic class metadata:

```python
DVS128Gesture(
    root: str,
    train: bool = True,
    data_type: str = 'event',
    frames_number: int = None,
    split_by: str = None,
    duration: int = None,
    custom_integrate_function: Callable = None,
    custom_integrated_frames_dir_name: str = None,
    transform: Optional[Callable] = None,
    target_transform: Optional[Callable] = None,
)
```

Additional verified metadata: `DVS128Gesture.get_H_W() == (128, 128)` and `DVS128Gesture.downloadable() is False`. Manual files are listed by `resource_url_md5()` and should be placed in `root/download`: `DvsGesture.tar.gz`, `gesture_mapping.csv`, `LICENSE.txt`, and `README.txt`.

DVS128Gesture-specific layout after preprocessing:

```text
root/
  download/                         # user-provided, because downloadable() is False
  extract/DvsGesture/               # created from DvsGesture.tar.gz
  events_np/train/<label>/*.npz      # event dicts with t/x/y/p arrays
  events_np/test/<label>/*.npz
  frames_number_20_split_by_number/train/<label>/*.npz
  duration_1000000/train/<label>/*.npz
```

SpikingJelly splits DVS128Gesture with `trials_to_train.txt` and `trials_to_test.txt`, then slices each AEDAT recording by the matching `*_labels.csv` timestamp ranges. Its documented preprocessing yields 1176 train samples and 288 test samples.

## Public dataset classes and split/download distinctions

Use constructors from `spikingjelly.datasets` for new code. Legacy module-level imports still work but are not the recommended style.

| Class / family | Split argument | Auto download? | Geometry / layout notes |
| --- | --- | --- | --- |
| `DVS128Gesture` | `train=True/False` | No | `(128, 128)` DVS events; manual IBM Box files in `download`; raw `events_np/train|test/<label>`; 11 classes. |
| `CIFAR10DVS` | no split argument | Yes | `(128, 128)`; original dataset has no official train/test split; class folders are loaded directly. |
| `CIFAR10DVSTEBNSplit` | `train=True/False` | Yes | Same CIFAR10-DVS files; creates the widely used TEBN split with samples `0..99` as test and `100..999` as train per class. |
| `NMNIST` | `train=True/False` | No | `(34, 34)`; manual `Train.zip` and `Test.zip`; converted ATIS `.bin` files become `.npz` event samples. |
| `NCaltech101` | no split argument | No | `(180, 240)`; manual Caltech101 archives; class-folder raw layout with converted ATIS `.bin` samples. |
| `ASLDVS` | no split argument | No | `(180, 240)`; Dropbox link is expired in source notes, OpenI mirror is suggested; converted `.mat` samples become `t/x/y/p` `.npz`. |
| `DVSLip` | `train=True/False` | No | `(128, 128)`; manual `DVS-Lip.zip`; raw files are structured `.npy` arrays compatible with field access for `t/x/y/p`. |
| `ESImageNet` | `train=True/False` | Yes | `(256, 256)`; raw files store `pos` and `neg` event arrays, and ESImageNet builders merge/sort them into `x/y/t/p`. |
| `HARDVS` | `train_test_val='train'|'val'|'test'` | No | `(260, 346)`; manual mini-HARDVS zip plus label txt files; layout is `train|val|test/action_###/*.npz`. |
| `NAVGestureWalk`, `NAVGestureSit` | no split argument | No | `(240, 304)` despite a 240x320 camera note; class labels are gesture abbreviations such as `le`, `ri`, `up`, `do`, `ho`, `se`. |
| `Bullying10kClassification` | `train=True/False` | Yes | `(260, 346)`; converts source `.npy` events into train/test `t/x/y/p` archives; every fifth sample is assigned to test by source logic. |
| `SpikingHeidelbergDigits` | `train=True/False` | Yes | Neuromorphic audio; `get_H_W() == (None, 700)`; raw `events_h5` with `shd_train.h5` and `shd_test.h5`; event samples use `t` and `x`, not `t/x/y/p`. |
| `SpikingSpeechCommands` | `split='train'|'valid'|'test'` | Yes | Neuromorphic audio; `events_h5` with `ssc_*` files; frame builders produce `[T, 700]` sequences. |

The separate `SpeechCommands` class in `spikingjelly.datasets.speechcommands` is a torchaudio-backed `torch.utils.data.Dataset`, not a `NeuromorphicDatasetFolder`; do not apply event/frame integration rules to it.

## Builder selection

| Builder | Selected by | Processed root | Loader contract |
| --- | --- | --- | --- |
| `EventBuilder` | `data_type='event'` | raw root (`events_np` or dataset-specific raw root) | `np.load` or a dataset-specific event loader. |
| `FrameFixedNumberBuilder` | `data_type='frame', frames_number=T, split_by='time'|'number'` | `root/frames_number_{T}_split_by_{split_by}` | `load_npz_frames`, returning `float32` `frames`. |
| `FrameFixedDurationBuilder` | `data_type='frame', duration=d` | `root/duration_{d}` | `load_npz_frames`; sample lengths can differ. |
| `FrameCustomIntegrateBuilder` | `data_type='frame', custom_integrate_function=fn` | `root/<custom_integrated_frames_dir_name or fn.__name__>` | `fn(events, H, W)` must return a frame array saved as `frames`. |

Dataset-specific overrides preserve this mental model but swap the event loader or file organization. Examples: ESImageNet converts `pos`/`neg` arrays into `x/y/t/p`; SHD/SSC use `.h5` events and frame shape `[T, W]` instead of `[T, 2, H, W]`.

## Event and frame layouts

### Event samples

For vision datasets, event samples are dict-like archives with keys:

```python
{'t': np.ndarray, 'x': np.ndarray, 'y': np.ndarray, 'p': np.ndarray}
```

Coordinates satisfy dataset-specific geometry from `get_H_W()`. Polarity `p` is treated as a two-channel selector by integration utilities: channel `0` for false/off polarity and channel `1` for true/on polarity.

### Frame samples

Frame archives save a single `frames` array. For vision datasets, the usual shape is:

```text
[T, 2, H, W]
```

`utils.load_npz_frames(path)` returns this array as `np.float32`. For SHD/SSC audio datasets, frame samples use `[T, 700]` because events are unit spikes over 700 input channels.

### Fixed frame count

Use this when a downstream network expects a fixed simulation length `T`:

```python
from spikingjelly.datasets import DVS128Gesture
train_set = DVS128Gesture(root, train=True, data_type='frame', frames_number=20, split_by='number')
```

- `split_by='number'` divides sorted events into slices with nearly equal event counts.
- `split_by='time'` divides the timestamp range into equal time windows.
- The processed directory name records the decision: `frames_number_20_split_by_number`.

### Fixed duration

Use this when each frame should represent a fixed real/event time interval:

```python
from torch.utils.data import DataLoader
from spikingjelly.datasets import DVS128Gesture
from spikingjelly.datasets.utils import pad_sequence_collate, padded_sequence_mask

train_set = DVS128Gesture(root, train=True, data_type='frame', duration=1_000_000)
loader = DataLoader(train_set, batch_size=8, collate_fn=pad_sequence_collate)
for x, y, lengths in loader:
    mask = padded_sequence_mask(lengths)  # shape [T, N]
```

Fixed-duration samples often have different `T`; do not rely on the default PyTorch collate function for those batches.

### Custom integration

Use a custom function when fixed count/duration is not the desired temporal binning:

```python
import numpy as np
from spikingjelly.datasets.utils import integrate_events_segment_to_frame

def two_half_frames(events, H, W):
    mid = len(events['t']) // 2
    return np.stack([
        integrate_events_segment_to_frame(events['x'], events['y'], events['p'], H, W, 0, mid),
        integrate_events_segment_to_frame(events['x'], events['y'], events['p'], H, W, mid, len(events['t'])),
    ])
```

Pass `custom_integrated_frames_dir_name` when you want a stable directory name instead of `two_half_frames`.

## Utility and transform map

| Helper | Use for | Contract notes |
| --- | --- | --- |
| `load_aedat_v3` | DVS128Gesture-style AEDAT v3 files | Returns `t/x/y/p` arrays. |
| `load_ATIS_bin` | ATIS binary event files used by N-MNIST / N-Caltech101 | Returns `t/x/y/p` arrays. |
| `integrate_events_segment_to_frame` | One event slice to one two-channel frame | Uses accumulation that preserves repeated positions and polarities. |
| `cal_fixed_frames_number_segment_index` | Inspect fixed-count or fixed-time slice boundaries | Returns `(j_l, j_r)` arrays. |
| `integrate_events_by_fixed_frames_number` | In-memory event dict to `[T, 2, H, W]` | Requires `split_by='time'` or `'number'`. |
| `integrate_events_by_fixed_duration` | In-memory event dict to variable-length frames | Length is computed from timestamp span and `duration`. |
| `pad_sequence_collate` | Collate variable-length frame sequences | Returns `(padded_x, labels, lengths)` with `batch_first=True`. |
| `padded_sequence_mask` | Mask padded timesteps | Returns boolean mask with shape `[T, N]`. |
| `split_to_train_test_set` | Create class-balanced `Subset`s for unsplit datasets | `random_split` is controlled by `numpy.random.seed`. |
| `create_sub_dataset` | Build a small class-preserving subset tree | Symlinks by default; pass `use_soft_link=False` to copy files. |
| `random_temporal_delete` / `RandomTemporalDelete` | Temporal augmentation | Preserve tensor/array type; `batch_first=True` means `[N, T, ...]`. |
| `save_as_pic`, `play_frame` | Visualize two-channel frame sequences | `play_frame` loops interactively unless `save_gif_to` is set. |
