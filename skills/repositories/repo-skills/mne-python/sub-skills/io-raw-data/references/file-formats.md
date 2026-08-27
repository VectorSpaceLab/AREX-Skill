# File Formats, Readers, and Optional Extras

## Generic dispatch behavior

`mne.io.read_raw(fname, preload=False, **kwargs)` chooses a reader from the filename suffix. It forwards all extra keyword arguments to the reader it tries.

Dispatch details distilled from MNE-Python's generic reader:

- Unknown suffix → `ValueError: Unsupported file type (...)`.
- Marker-only BrainVision files `.vmrk` and `.amrk` are known but not raw data; the dispatcher suggests `.vhdr` or `.ahdr` instead.
- Ambiguous suffixes are tried with multiple readers. If none succeeds, MNE raises a `RuntimeError` listing reader functions to try directly.
- A dedicated reader usually gives clearer diagnostics and supports format-specific sidecar or channel-type arguments.

## Supported raw reader families

| Family | Typical suffix or input | Reader(s) | Notes |
| --- | --- | --- | --- |
| MNE/FIFF | `.fif`, `.fif.gz` | `read_raw_fif` | Native format; supports split FIF files and MaxShield warning control. Save with `raw.save(...raw.fif)`. |
| EDF/BDF/GDF | `.edf`, `.bdf`, `.gdf` | `read_raw_edf`, `read_raw_bdf`, `read_raw_gdf` | Configure `eog`, `misc`, `stim_channel`, `exclude`/`include`, `infer_types`, and `units` as needed. |
| BrainVision | `.vhdr`, `.ahdr` | `read_raw_brainvision` | Read the header file, not marker sidecars. Marker files are `.vmrk`/`.amrk`. Common options include `eog`, `misc`, `scale`, `ignore_marker_types`, and `overrides`. |
| EEGLAB | `.set` | `read_raw_eeglab` | Handles EEGLAB raw sets. Use `uint16_codec` for problematic strings and `montage_units` for coordinate units. |
| EGI/MFF | `.mff` | `read_raw_egi` | Can turn event tracks into annotations with `events_as_annotations=True`; use `channel_naming`, `include`, and `exclude` for channel names/events. |
| CTF | `.ds` directory | `read_raw_ctf` | Input is the CTF dataset directory. `clean_names` and `system_clock` are common choices. |
| 4D/BTI | PDF file plus sidecars | `read_raw_bti` | Often requires config and head-shape sidecars; has channel-renaming and sorting options. |
| KIT/Yokogawa | `.sqd`, `.con` | `read_raw_kit` | Can synthesize `STI 014` from trigger channels; marker/head-shape/electrode files may be needed. |
| ANT / CNT | `.cnt` | `read_raw_ant`, `read_raw_cnt` | `.cnt` is ambiguous. Choose directly when you know the vendor. ANT has impedance/bipolar options; CNT has header/data-format/date-format options. |
| Curry | `.dat`, `.dap`, `.rs3`, `.cdt`, `.cdt.dpa`, `.cdt.cef`, `.cef` | `read_raw_curry` | Requires the Curry file family to be complete and uses `on_bad_hpi_match`. Current reader requires the Curry reader dependency. |
| BCI2000 | `.dat` | `read_raw_bci2k` | `.dat` is ambiguous with Curry, so direct reader calls are safer. |
| FieldTrip | `.mat` | `read_raw_fieldtrip` | Returns `RawArray`; must supply an `Info` object because FieldTrip MAT data do not fully encode MNE channel metadata. |
| NIRx | `.hdr` within NIRx structure | `read_raw_nirx` | fNIRS-specific reader; `saturated` controls saturated-sample handling; encoding may matter. |
| SNIRF | `.snirf` | `read_raw_snirf` | HDF5-backed fNIRS standard; `optode_frame` and optional `sfreq` may be needed. |
| Hitachi | vendor file/list | `read_raw_hitachi` | fNIRS family; may involve multiple files. |
| BOXY | `.txt` | `read_raw_boxy` | fNIRS text format. |
| Artemis123 / FIL OPM | `.bin` | `read_raw_artemis123`, `read_raw_fil` | `.bin` is ambiguous. Direct reader calls are preferred. FIL has a `precision` option. |
| EyeLink | `.asc` | `read_raw_eyelink` | Eye-tracking data; can create annotations and handle offsets/overlaps. |
| MEF | `.mefd` | `read_raw_mef` | Supports `password` for encrypted files. |
| Neuralynx | directory/file family | `read_raw_neuralynx` | Requires the Neuralynx optional dependency stack; use `exclude_fname_patterns` to omit files. |
| NSx | `.ns3` | `read_raw_nsx` | Blackrock/NSx; configure stim, EOG, misc channels. |
| Nicolet | `.data` | `read_raw_nicolet` | Requires a mandatory `ch_type` for data channels, plus optional EOG/ECG/EMG/misc mapping. |
| Nihon Kohden | `.eeg` | `read_raw_nihon` | Encoding can matter. |
| NEDF | `.nedf` | `read_raw_nedf` | Uses `filename` parameter. |
| Eximia | `.nxe` | `read_raw_eximia` | TMS/EEG vendor format. |
| Persyst | `.lay` | `read_raw_persyst` | Header/data files must be co-located for typical Persyst datasets. |

## Optional dependency caveats

Reader and export dependencies are intentionally not all installed in minimal MNE environments. Treat missing optional imports as a capability limit, not as a core MNE import failure.

Common dependency surfaces:

- **External Raw export**: BrainVision export uses `pybv`; EDF/BDF export uses `edfio`; EEGLAB export uses `eeglabio`.
- **HDF5-backed formats**: SNIRF uses `h5py`; some MAT/EEGLAB paths may need MAT/HDF5 support beyond a simple SciPy load.
- **Neuralynx**: the reader relies on `neo` and its dependencies.
- **Curry**: current raw Curry reading requires the Curry reader dependency; DataFrame integration paths may require `pandas`.
- **EyeLink**: sample/event table handling uses pandas internally in the reader utilities.
- **Rare vendor formats**: sidecar metadata files, encodings, passwords, or external package variants can be more important than the suffix.

If an optional dependency is unavailable and the user only needs to create synthetic Raw data or read FIF/EDF-like data covered by the installed environment, continue with the supported path. If the user specifically needs that vendor format/export target, surface the missing dependency and provide the reader/exporter name and minimal package to install.

## Format selection checklist

Before reading:

- Is the path a data file, header file, marker file, or dataset directory?
- Are sidecars in the same directory and named consistently with the data/header file?
- Is the suffix ambiguous (`.cnt`, `.bin`, `.dat`)? If yes, choose a specific reader.
- Does the reader require an `Info` object (`read_raw_fieldtrip`) or mandatory channel type (`read_raw_nicolet`)?
- Are channel names/types encoded correctly or should `eog`, `misc`, `ecg`, `emg`, `stim_channel`, `infer_types`, or `units` be set?
- Is preload needed now, or can the task inspect metadata lazily and crop/pick first?
- Is the goal MNE-native preservation (`raw.save`) or exchange with another tool (`raw.export`, arrays, DataFrame)?
