# Data-preparation troubleshooting

Start with the smallest failing HDF5 or list. Preserve raw inputs, conversion
arguments, list files, marker timestamps, and validator output. Do not repair a
malformed HDF5 or cache marker in place.

| Symptom | Likely cause | Safe recovery |
|---|---|---|
| Required `data`, `label`, or `label_seg` key is missing | Classification and segmentation files were mixed, an archive was partial, or a different writer produced the file. | Run `validate_pointcnn_h5.py --h5 FILE --kind auto`; compare the schema reference; reconvert to a new destination with the required keys. |
| Rank or leading-dimension check fails | A flattened/ transposed array, scalar label, wrong batch slice, or per-point array with a wrong B/N was written. | Inspect the reported shapes and recreate the smallest fixture. Do not silently reshape an unknown file. |
| `data_num` is zero, negative, greater than N, or not length B | Padding metadata was lost or a full buffer was saved after a partial batch. | Reconvert. If a provenance-backed manual repair is unavoidable, write a new file and validate it; never score padded points. |
| Classification labels are outside the selected class count | Split-specific remapping, a wrong mapping file, or a label offset was applied twice. | Pass the selected setting's class count to the validator, retain one mapping for all splits, and remap once into the expected range. |
| Segmentation `label` looks plausible but predictions are wrong | `label` is a sample/category placeholder; `label_seg` is the per-point target. | Use `label_seg[i, :data_num[i]]`, inspect the category/part mapping, and do not substitute the two arrays. |
| Active labels are negative or non-contiguous | Ignore values were retained, or a minimum/offset was applied inconsistently. | Decide the ignore-label policy from the dataset/model contract, then write a new consistently mapped output. Do not run `np.unique` independently on train and validation. |
| Optional indices appear in only some files | Lists combine preprocessing passes or one converter omitted reconstruction metadata. | Split lists by convention. Require indices consistently for reconstruction and validate `[B,N]` versus `[B,N,2]`. |
| Index mapping fails bounds | A source index was flattened, source rows were filtered, or room sizes are unknown. | For S3DIS/Semantic3D use `--index-size`; for ScanNet provide `--room-sizes` with one source point count per room. Validate only active prefixes and reconvert if provenance was discarded. |
| HDF5 has NaN/Inf or unexpected feature range | Degenerate normalization, double RGB/intensity scaling, or a writer received already-scaled colors. | Reject the sample, inspect raw extents, normalize exactly once, and record the converter contract. Schema validation cannot prove coordinate orientation or feature semantics. |
| Classification list reports a missing file that exists under a subdirectory | The legacy classification loader strips every entry to its basename. | Move the list beside its HDF5 files or list basenames from that directory. Do not use segmentation path semantics for classification. |
| Segmentation list resolves from the wrong directory | A child entry was interpreted relative to the top-level list, or a list was moved after generation. | Run `inspect_filelists.py --list LIST --kind segmentation --show-resolved`; fix each entry relative to the list containing it and generate a new list. |
| Flat/nested mode is surprising | `is_h5_list()` considers a list flat only if every raw line ends with `.h5`; a blank, comment, malformed suffix, or child list changes the mode. | Remove blank/comment lines and do not mix HDF5 and child-list entries. Inspect the top list and every child list. |
| Duplicate files or repeated groups are reported | A list generator was rerun, a child list was referenced twice, or intentional training repetition was encoded as duplicate HDF5 entries. | Treat individual-file duplicates as an error unless repetition is explicitly intended and documented. Keep deliberate child rotation separate from file identity checks. |
| PLY output is missing or colors are black/wrapped | Output had no explicit parent, active arrays were not truncated, property max was zero, or normalized colors were multiplied twice. | Use an approved new output directory; pass active points and parallel arrays; use a positive property maximum; inspect one PLY before scaling up. The bundled scripts never write PLY. |
| S3DIS conversion says a room is already processed | `.labels` or `.dataset` marker survived a partial write. | Inspect `.npy` and HDF5 contents and validate representative files. Move the marker aside only after preserving it, then rerun into an isolated destination. A marker is not completion evidence. |
| Semantic3D extraction/listing appears complete but labels are missing | `.unpacked` was created early, labels were moved between split directories, or the archive was incomplete. | Check archive contents, extracted point/label names, marker timestamps, and free space. Restore a clean copy and validate a tiny conversion before the full set. The full route is a documented roughly 900-GB operation. |
| Download or conversion command wants network, extraction, moves, or huge storage | The historical helper is being used as a smoke test or a default root was assumed. | Stop. Acquisition, extraction, conversion, marker creation, and PLY output need explicit approval, a new destination, integrity checks, and a bounded sample. These actions are not bundled in this skill. |
| A legacy converter cannot show `--help` | It imports optional repository-local packages before parsing arguments. | Do not run it against user data to diagnose import behavior. Use a compatible reviewed environment or adapted converter only after approval; the bundled validators are dependency-minimal and read-only. |
| Tiny HDF5 validation passes but segmentation cannot run | Input shape is independent of the legacy runtime and compiled sampling operator. | Keep the input result, route backend checks to the segmentation/operator skills, and preserve the required-backend status. TensorFlow 1.15 import/device discovery passed in the current runtime, but the GPU/custom-op session timed out; FPS is `BLOCKED_REQUIRED_BACKEND`, never passed. |

## Recovery order

1. Stop a mutating or long-running command.
2. Preserve raw files, generated outputs, lists, markers, and arguments.
3. Run `inspect_filelists.py` and `validate_pointcnn_h5.py` on a tiny sample.
4. Correct the layout/schema or reconvert into a new destination.
5. Validate every file in the final list, including index bounds where known.
6. Hand off exact list paths and unresolved limits to the model workflow.
7. Perform separate TensorFlow/CUDA/custom-op/FPS checks; never infer them from
   a passing HDF5 or PLY check.
