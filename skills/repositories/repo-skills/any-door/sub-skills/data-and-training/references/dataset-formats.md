# Dataset Formats

AnyDoor’s training and debugging workflows expect several different dataset
families. The important part is not just the root path, but the mask and
annotation convention each family uses.

## Common sample shape

`BaseDataset.process_pairs` builds a training item with:

- `ref`: reference image tensor or array,
- `jpg`: target image tensor or array,
- `hint`: collage/control tensor with an extra mask channel,
- `extra_sizes`: original and padded size metadata,
- `tar_box_yyxx_crop`: crop box metadata,
- and sometimes `time_steps` for the training scheduler.

## Dataset families from the source

| Family | Source class | Key path inputs | Mask / label convention |
| --- | --- | --- | --- |
| YouTube-VOS | `YoutubeVOSDataset` | image dir, annotation dir, meta JSON | per-frame object id from the video record |
| YouTube-VIS | `YoutubeVISDataset` | image dir, annotation dir, meta JSON | per-object frame id from the video record |
| VIPSeg | `VIPSegDataset` | image dir, panoptic mask dir | panoptic RGB converted to ids; choose a common non-zero id |
| UVO | `UVODataset` / `UVOValDataset` | image dir, video JSON, reorg JSON | sparse video annotations decoded from RLE masks |
| MOSE | `MoseDataset` | image dir, annotation dir | common object id from paired frames |
| MVImageNet | `MVImageNetDataset` | text index file, image dir | alpha channel in PNG masks |
| SAM | `SAMDataset` | JSON subset dirs | RLE masks from JSON annotations |
| LVIS | `LvisDataset` | image dir, LVIS JSON | LVIS annotation mask with area filtering |
| DreamBooth | `DreamBoothDataset` | foreground dir, background dir | alpha mask for the foreground object |
| DressCode | `DresscodeDataset` | label-map image dir | parse label `4` |
| FashionTryon | `FashionTryonDataset` | target cloth root | parse label `7` after erosion |
| VITON-HD | `VitonHDDataset` | cloth image dir | parse label `5` |
| Saliency | `SaliencyDataset` | several saliency roots | paired image/mask files |

## Important label notes

- VITON-HD target masks use label `5`.
- DressCode target masks use label `4`.
- FashionTryon target masks use label `7`.
- LVIS uses areas to filter object candidates before mask extraction.
- SAM selects large enough regions from JSON annotations.

## What to validate before training

- Path roots are real and not placeholders.
- Annotation files exist and match the expected class.
- Parse masks contain the correct foreground label for the chosen dataset.
- Video datasets have a common object id across the chosen frames.
- PNG masks and alpha masks threshold cleanly to binary values.

## UVO preprocessing

The UVO reorganization step rewrites the annotation JSON into a map from
video-id to frame list. That is a preprocessing step, not a training-time hack.
Use the bundled rewriter if the JSON is still in the original format.

## Why this matters

If the dataset family is wrong, the loader may still open files but silently
construct the wrong object mask. Most downstream failures look like “bad model
behavior” but actually begin here.
