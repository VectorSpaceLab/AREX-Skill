# MNE-Python IO / Raw API Reference

This reference distills public API stubs, `BaseRaw` source behavior, `RawArray` source behavior, generic reader dispatch, tutorials, focused IO tests, and installed API inspection for MNE-Python `0.1.0.dev1+gb1914e98a`.

Source evidence provenance, not runtime dependencies: `mne/io/__init__.pyi`, `mne/io/_read_raw.py`, `mne/io/base.py`, `mne/io/array/_array.py`, `mne/_fiff/meas_info.py`, `mne/io/*/tests/`, `tutorials/io/`, `tutorials/raw/`, `examples/io/`, and installed public signatures.

## Core object relationships

- `mne.io.read_raw(fname, **kwargs)` is a suffix-based convenience dispatcher. It returns a `BaseRaw` subclass and forwards unknown keywords to the selected format reader.
- `mne.io.read_raw_fif()` returns the native FIF `Raw` class. Other `read_raw_*` functions return format-specific `BaseRaw` subclasses such as `RawEDF`, `RawBrainVision`, `RawCTF`, or `RawSNIRF`.
- `mne.io.RawArray(data, info)` creates an in-memory `BaseRaw` subclass from a NumPy array and an `Info` object. It is the normal constructor for synthetic continuous data.
- `mne.create_info(ch_names, sfreq, ch_types="misc")` creates a sparse but consistent `Info` object. `RawArray` checks that `len(info["ch_names"]) == data.shape[0]`.
- `BaseRaw` is public for type checks (`isinstance(raw, BaseRaw)`) but is not the user-facing constructor.
- `raw.info` is an `Info` object with keys such as `sfreq`, `ch_names`, `chs`, `nchan`, `bads`, `projs`, `meas_date`, `highpass`, and `lowpass`. Many fields should be changed only through MNE methods, not raw dict assignment.

## Verified primary signatures

```python
mne.create_info(ch_names, sfreq, ch_types='misc', verbose=None)

mne.io.RawArray(
    data: numpy.ndarray,
    info: mne._fiff.meas_info.Info,
    first_samp: int = 0,
    copy: Literal['data', 'info', 'both', 'auto'] | None = 'auto',
    verbose: bool | str | int | None = None,
)

mne.io.read_raw(
    fname: pathlib.Path | str,
    *,
    preload: bool | str = False,
    verbose: bool | str | int | None = None,
    **kwargs,
) -> mne.io.base.BaseRaw

mne.io.read_raw_fif(
    fname: pathlib.Path | str | typing.IO,
    allow_maxshield: bool | str = False,
    preload: bool | str = False,
    on_split_missing: str = 'raise',
    verbose: bool | str | int | None = None,
) -> mne.io.fiff.raw.Raw
```

## Verified `BaseRaw` methods for IO tasks

```python
raw.load_data(*, memmap: pathlib.Path | str | None = None, verbose=None) -> Self
raw.get_data(picks=None, start=0, stop=None, reject_by_annotation=None,
             return_times=False, units=None, *, tmin=None, tmax=None,
             verbose=None) -> ndarray | tuple
raw.crop(tmin=0.0, tmax=None, include_tmax=True, *, reset_first_samp=False,
         verbose=None) -> Self
raw.save(fname, picks=None, tmin=0, tmax=None, buffer_size_sec=None,
         drop_small_buffer=False, proj=False, fmt='single', overwrite=False,
         split_size='2GB', split_naming='neuromag', verbose=None) -> list[pathlib.Path]
raw.export(fname, fmt='auto', physical_range='auto', add_ch_type=False,
           *, overwrite=False, verbose=None) -> None
raw.append(raws, preload=None) -> None
raw.set_annotations(annotations, emit_warning=True, on_missing='raise', *, verbose=None) -> Self
raw.pick(picks, exclude=(), *, verbose=None)
raw.drop_channels(ch_names, on_missing='raise')
raw.rename_channels(mapping, allow_duplicates=False, *, on_missing='raise', verbose=None)
raw.set_channel_types(mapping, *, on_unit_change='warn', verbose=None)
raw.reorder_channels(ch_names)
raw.to_data_frame(picks=None, index=None, scalings=None, copy=True,
                  start=None, stop=None, long_format=False, time_format=None,
                  *, verbose=None) -> pandas.DataFrame
```

Related utility signatures:

```python
mne.Annotations(onset, duration, description, orig_time=None, ch_names=None, *, extras=None)
mne.read_annotations(fname, sfreq='auto', uint16_codec=None, encoding='utf8',
                     ignore_marker_types=False, data_format='auto') -> mne.Annotations
mne.pick_channels(ch_names, include, exclude=(), ordered=True, *, verbose=None)
mne.pick_types(info, meg=False, eeg=False, stim=False, eog=False, ecg=False,
               emg=False, ref_meg='auto', *, misc=False, resp=False,
               chpi=False, exci=False, ias=False, syst=False, seeg=False,
               dipole=False, gof=False, bio=False, ecog=False, fnirs=False,
               csd=False, dbs=False, temperature=False, gsr=False,
               eyetrack=False, include=(), exclude='bads', selection=None)
```

## Verified reader signatures

Use this table when choosing a format-specific reader or validating keyword names. `preload` defaults to `False` for nearly all readers.

| Reader | Signature summary |
| --- | --- |
| `read_raw` | `(fname, *, preload=False, verbose=None, **kwargs) -> BaseRaw` |
| `read_raw_fif` | `(fname, allow_maxshield=False, preload=False, on_split_missing='raise', verbose=None) -> Raw` |
| `read_raw_edf` | `(input_fname, eog=None, misc=None, stim_channel='auto', exclude=(), infer_types=False, include=None, preload=False, units=None, encoding='utf8', exclude_after_unique=False, *, verbose=None) -> RawEDF` |
| `read_raw_bdf` | Same main options as `read_raw_edf`, returning `RawBDF` |
| `read_raw_gdf` | `(input_fname, eog=None, misc=None, stim_channel='auto', exclude=(), include=None, preload=False, verbose=None) -> RawGDF` |
| `read_raw_brainvision` | `(vhdr_fname, eog=('HEOGL','HEOGR','VEOGb'), misc='auto', scale=1.0, ignore_marker_types=False, overrides=None, preload=False, verbose=None) -> RawBrainVision` |
| `read_raw_eeglab` | `(input_fname, eog=(), preload=False, uint16_codec=None, montage_units='auto', verbose=None) -> RawEEGLAB` |
| `read_raw_egi` | `(input_fname, eog=None, misc=None, include=None, exclude=None, preload=False, channel_naming='E%d', *, events_as_annotations=True, event_key=None, verbose=None) -> RawEGI` |
| `read_raw_ctf` | `(directory, system_clock='truncate', preload=False, clean_names=False, verbose=None) -> RawCTF` |
| `read_raw_bti` | `(pdf_fname, config_fname='config', head_shape_fname='hs_file', rotation_x=0.0, translation=(0.0,0.02,0.11), convert=True, rename_channels=True, sort_by_ch_name=True, ecg_ch='E31', eog_ch=('E63','E64'), preload=False, verbose=None) -> RawBTi` |
| `read_raw_kit` | `(input_fname, mrk=None, elp=None, hsp=None, stim='>', slope='-', stimthresh=1, preload=False, stim_code='binary', allow_unknown_format=False, standardize_names=False, *, bad_coils=(), verbose=None) -> RawKIT` |
| `read_raw_ant` | `(fname, eog=None, misc='BIP\\d+', bipolars=None, impedance_annotation='impedance', *, encoding='latin-1', preload=False, verbose=None) -> RawANT` |
| `read_raw_cnt` | `(input_fname, eog=(), misc=(), ecg=(), emg=(), *, data_format='auto', date_format='mm/dd/yy', recompute_n_samples=None, header='auto', preload=False, verbose=None) -> RawCNT` |
| `read_raw_curry` | `(fname, preload=False, on_bad_hpi_match='warn', verbose=None) -> RawCurry` |
| `read_raw_fieldtrip` | `(fname, info, data_name='data') -> RawArray` |
| `read_raw_nirx` | `(fname, saturated='annotate', *, preload=False, encoding='latin-1', verbose=None) -> RawNIRX` |
| `read_raw_snirf` | `(fname, optode_frame='unknown', *, sfreq=None, preload=False, verbose=None) -> RawSNIRF` |
| `read_raw_hitachi` | `(fname, preload=False, verbose=None) -> RawHitachi` |
| `read_raw_boxy` | `(fname, preload=False, verbose=None) -> RawBOXY` |
| `read_raw_eyelink` | `(fname, *, create_annotations=True, apply_offsets=False, find_overlaps=False, overlap_threshold=0.05, verbose=None) -> RawEyelink` |
| `read_raw_mef` | `(fname, *, password='', preload=False, verbose=None) -> RawMEF` |
| `read_raw_neuralynx` | `(fname, *, preload=False, exclude_fname_patterns=None, verbose=None) -> RawNeuralynx` |
| `read_raw_nsx` | `(input_fname, stim_channel=True, eog=None, misc=None, preload=False, *, verbose=None) -> RawNSX` |
| `read_raw_bci2k` | `(input_fname, preload=False, verbose=None) -> RawBCI2k` |
| `read_raw_artemis123` | `(input_fname, preload=False, verbose=None, pos_fname=None, add_head_trans=True) -> RawArtemis123` |
| `read_raw_fil` | `(binfile, precision='single', preload=False, *, verbose=None) -> RawFIL` |
| `read_raw_eximia` | `(fname, preload=False, verbose=None) -> RawEximia` |
| `read_raw_nedf` | `(filename, preload=False, verbose=None) -> RawNedf` |
| `read_raw_nicolet` | `(input_fname, ch_type, eog=(), ecg=(), emg=(), misc=(), preload=False, verbose=None) -> RawNicolet` |
| `read_raw_nihon` | `(fname, preload=False, *, encoding='utf-8', verbose=None) -> RawNihon` |
| `read_raw_persyst` | `(fname, preload=False, verbose=None) -> RawPersyst` |

## `RawArray` contract

- `data` must be a 2-D array shaped `(n_channels, n_times)`.
- `info["ch_names"]` length must equal `data.shape[0]`.
- Data are converted to `float64`, or `complex128` when any sample is complex. With `copy="auto"`, MNE copies `info` and only copies data if the dtype conversion requires it.
- Units are MNE SI units: EEG/EOG/ECG/EMG/ECoG/sEEG/DBS/bio/resp/fNIRS amplitude/OD in volts, magnetometers in tesla, gradiometers in tesla/meter, hemoglobin in molar, fNIRS phase in radians, dipoles in ampere-meter, conductance in siemens, temperature in Celsius, and misc/stim/eyegaze/pupil in arbitrary units.
- `first_samp` controls recording sample numbering; downstream event sample numbers are compared to `raw.first_samp`/`raw.last_samp`.

## Info and FIF metadata

```python
mne.io.read_info(fname, verbose=None)
mne.io.write_info(fname, info, *, data_type=None, reset_range=True,
                  overwrite=False, verbose=None)
info.save(fname, *, overwrite=False, verbose=None)
```

- `read_info`/`write_info` work with `.fif` and `.fif.gz` files. Info-only files conventionally end in `-info.fif`.
- Use `mne.create_info()` for synthetic objects and reader-returned `raw.info` for real files. Avoid constructing `Info` dictionaries by hand unless an MNE API explicitly requires expert-level fields.
- Some metadata are duplicated (`ch_names`, `nchan`, `chs`) and consistency is checked. Use methods such as `rename_channels`, `set_channel_types`, `set_montage`, `add_proj`, and `info['bads']` updates rather than arbitrary nested edits.
