# Data formats and loader catalog

## Base contracts

`BaseLoader` is a PyTorch `Dataset`. Its normal lifecycle is:
`get_raw_data` → `split_raw_data` → `preprocess_dataset_subprocess` →
`preprocess` → `save_multi_process` → `build_file_list` →
`load_preprocessed_data`. A loader generally provides `get_raw_data`,
`split_raw_data`, a preprocessing worker, `read_video`, and `read_wave`; some
loaders override file-list loading or preprocessing for metadata/multitask data.

Raw frames are converted to `(T,H,W,C)` RGB-like arrays before common processing.
Common video readers are AVI/PNG/BMP/ZIP/MAT/HDF5/CSV readers as listed below.
`BaseLoader.preprocess` performs face crop/resize, concatenates one or more
`DATA_TYPE` channel groups along the last axis, applies `LABEL_TYPE`, and either
chunks into complete `(D,H,W,C)` clips or emits one full clip. The standard on-disk
input is therefore rank 4 NDHWC and the standard label is rank 1 with the same
`D`. `Raw` preserves values until save; `DiffNormalized` computes temporal
relative differences, divides by global standard deviation, appends a zero frame,
and replaces NaNs; `Standardized` z-scores the whole array and replaces NaNs.
The same three names apply to labels (temporal difference for
`DiffNormalized`). Constant signals can collapse to zeros because the source
normalizers replace NaNs.

`resample_ppg` uses linear interpolation to make a waveform the frame length.
Pseudo labels use POS, detrending, a 0.70–3 Hz second-order bandpass, and Hilbert
amplitude-envelope normalization. They are periodic proxy labels, not faithful
waveform morphology; use only when the experiment intentionally accepts that
trade-off.

## Supported loaders and raw layouts

The README's seven-dataset summary is stale relative to the loader directory. The
following public loaders are present and should remain discoverable:

| Loader | Expected `DATA_PATH` layout and important behavior |
|---|---|
| `UBFCrPPGLoader` | `subjectN/vid.avi` plus `ground_truth.txt`; `subjectN` is the source id. With `DATA_AUG` containing `Motion`, reads NPY frames from the subject directory instead of AVI. |
| `PURELoader` | `ii-jj/ii-jj/*.png` plus `ii-jj.json`; JSON `/FullPackage` waveform is resampled to frame count. Fractional splits group by the two-digit subject id to avoid overlap. Motion mode reads NPY files in the nested video directory. |
| `SCAMPSLoader` | `*.mat` files (commonly separate Train/Val/Test directories) with `Xsub` frames and `d_ppg`; frames are scaled by 255 and converted to uint8 before common processing. It suffixes cache/file-list paths with the dataset name. |
| `MMPDLoader` | `subjectN/pN_K.mat`; each MAT contains `video`, `GT_ppg`, and metadata (`light`, `motion`, `exercise`, `skin_color`, `gender`, `glasser`, `hair_cover`, `makeup`). It resamples labels and encodes metadata into cache names, then filters file lists by `INFO`. Unsupported metadata strings raise `ValueError`. |
| `BP4DPlusLoader` | `2D+3D/Fxxx.zip`, `Physiology/{F|Mxxx}/Tn/`, and associated BP4D+ trees. It selects physiology trials, skips known missing `F042T11`, reads JPGs from the subject ZIP, downsamples before face processing, and uses `BP_mmHg.txt` unless pseudo labels are requested. It splits by subject. |
| `BP4DPlusBigSmallLoader` | Same BP4D+ source, but only AU-bearing trials `T1,T6,T7,T8` and skips `F041T7`. It reads physiology/AU arrays, emits 49-column labels, and writes `<id>_inputN.pickle` holding big and small streams plus `<id>_labelN.npy`. This path is not a standard NPY cache. |
| `UBFCPHYSLoader` | `sN/vid_sN_Tn.avi` and sibling `bvp_sN_Tn.csv`; labels are resampled. `USE_EXCLUSION_LIST` and `SELECT_TASKS` filter already-cached inputs by task id; both are loader-specific filtering features. |
| `iBVPLoader` | `pNN_x/pNN_x_rgb/*.bmp`, `pNN_x_t/*.raw`, and `pNN_x_bvp.csv`. `IBVP.DATA_MODE` can be `RGB`, `T`, or `RGBT`; RGBT truncates streams to the shorter length and crops thermal height to RGB height. Signal-quality column `SQ2` is resampled and frames with `SQ2 <= 0.3` are removed before preprocessing. Motion mode reads NPY frames. |
| `PhysDriveLoader` | `subject/session/Align/*.png` and `Label/BVP.mat` (plus ECG/RESP/SPO2). Motion mode reads session-level NPY files. Subject-aware splitting is used; missing Align/BVP or empty data raises/logs errors. Clips with signal quality below `0.5` are skipped using NeuroKit peak/quality assessment. |
| `LADHLoader` | Under a path containing `p_*`, each participant has `vNN/video_RGB_H264.avi` and timestamped `BVP.csv`; RGB frame timestamps are synchronized to BVP by interpolation. Only `RGB_H264` videos are saved; IR is discovered but not emitted by this loader. |
| `SUMSLoader` | `0602xx/vNN/video_*_H264.avi`, `BVP.csv`, and `frames_timestamp.csv`. BVP is interpolated to frame timestamps and only videos whose path contains `face` are saved. Splits group by numeric subject id. |
| `COHFACELoader` | `subject/trial/data.avi` and `data.hdf5`, with trials `0`–`3`; HDF5 dataset key is `pulse`. It overrides preprocessing and saves sequentially rather than using the common multiprocessing path. |

Some loaders print paths or discovered directories, and several source checks are
minimal. Validate the exact dataset tree before invoking them. In particular,
`PhysDrive` and `LADH` are newer additions whose README coverage is brief, and
`COHFACE` is not in the README's current support list.

## Splits, file lists, and naming

A generated CSV has a column named `input_files`; the source writes a pandas index
column too, which consumers ignore. Labels are inferred by replacing `input` with
`label` in each input path. Custom lists may point at any existing cache, but every
listed input must have a sibling label with the exact corresponding source id and
chunk number. Do not use an arbitrary CSV column or omit the extension.

BP4D BigSmall fold files are CSVs with one `subjects` column. `Split1`, `Split2`,
and `Split3` each have train/test subject lists; the BigSmall loader keeps trials
whose four-character subject prefix occurs in the selected fold. Confirm that a
fold path and `FOLD_NAME` are set together. The fold CSVs are intended for the
BigSmall loader and should not be substituted for generic `BEGIN`/`END` splitting.

## Face detector resources

The HC detector entry point is `BaseLoader.face_detection`, which constructs an
OpenCV `CascadeClassifier`; it uses `[x,y,width,height]` boxes and falls back to a
full-frame box when no face is found. The checked-in cascade is a resource named
`haarcascade_frontalface_default.xml`. The Y5F entry point is
`face_detector.YOLO5Face.detect_face`, which returns `[x1,y1,x2,y2]` and is
converted to a square `[x,y,width,height]` box by `BaseLoader`. A portable consumer
must resolve both detector resources from its installed package or explicit
absolute paths, not from the current working directory or the original source
checkout. Do not silently download a missing Y5F checkpoint.
