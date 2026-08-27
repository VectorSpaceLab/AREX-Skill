# Dataset assets and download planning

Network dataset acquisition is reference-only in this sub-skill. Required verification uses local or synthetic fixtures and does not download archives. Before any network action, get explicit user approval for the dataset name, destination, license terms, bandwidth/storage budget, and archive cleanup policy.

## CycleGAN dataset names

The CycleGAN dataset helper accepts these names. Except for the Cityscapes license exception, the archive URL pattern is:

```text
http://efrosgans.eecs.berkeley.edu/cyclegan/datasets/<dataset_name>.zip
```

| Name | Notes distilled from repository docs/scripts |
| --- | --- |
| `apple2orange` | ImageNet apple/orange domains; unaligned layout after unpacking. |
| `summer2winter_yosemite` | Yosemite seasonal domains; unaligned layout. |
| `horse2zebra` | ImageNet horse/zebra domains; common pretrained-model companion dataset. |
| `monet2photo` | WikiArt Monet paintings and Flickr landscape photos. |
| `cezanne2photo` | WikiArt Cezanne paintings and Flickr landscape photos. |
| `ukiyoe2photo` | WikiArt Ukiyo-e images and Flickr landscape photos. |
| `vangogh2photo` | WikiArt Van Gogh paintings and Flickr landscape photos. |
| `maps` | Google Maps-derived paired/unpaired map-photo asset used in examples. |
| `facades` | CMP Facades-derived asset also appears in pix2pix examples. |
| `iphone2dslr_flower` | Flickr iPhone/DSLR flower domains. |
| `ae_photos` | Accepted by the helper; treat as a public/reference asset if user requests it. |
| `mini` | Tiny smoke asset accepted by the helper; useful only if user approves a network smoke download. |
| `mini_pix2pix` | Tiny pix2pix smoke asset accepted by the helper. |
| `mini_colorization` | Tiny colorization smoke asset accepted by the helper. |
| `cityscapes` | Not downloaded by the helper because of licensing; see the Cityscapes section below. |

## pix2pix dataset names

The pix2pix dataset helper accepts these names. Except for the Cityscapes license exception, the archive URL pattern is:

```text
http://efrosgans.eecs.berkeley.edu/pix2pix/datasets/<dataset_name>.tar.gz
```

| Name | Notes distilled from repository docs/scripts |
| --- | --- |
| `facades` | 400 CMP Facades examples; examples often use `--direction BtoA` for label-to-photo. |
| `maps` | Map/photo paired asset. |
| `edges2shoes` | About 50k shoe examples; edges were computed by HED plus post-processing. |
| `edges2handbags` | About 137k handbag examples; edges were computed by HED plus post-processing. |
| `night2day` | Around 20k natural scene examples; for day-to-night, use `--direction BtoA`. |
| `cityscapes` | Not downloaded by the helper because of licensing; see the Cityscapes section below. |

## Cityscapes license exception

Cityscapes is intentionally not hosted by the dataset helpers. A user must obtain it through the official Cityscapes licensing process and provide already downloaded/extracted trees containing:

```text
gtFine_trainvaltest.zip      -> extracted gtFine/... tree
leftImg8bit_trainvaltest.zip -> extracted leftImg8bit/... tree
```

After those assets are local, use the bundled converter [`../scripts/prepare_cityscapes_dataset.py`](../scripts/prepare_cityscapes_dataset.py) to create paired `train/test` and unpaired `trainA/trainB/testA/testB` outputs. The converter performs no network access and fails if matching color label maps and photos are missing.

## Network and storage warnings

- The original helpers use `wget` plus `unzip` or `tar`; systems without those tools will fail before any model work begins.
- Archives can be large: `edges2handbags`, `edges2shoes`, `night2day`, and Cityscapes are not suitable for implicit verification downloads.
- Partial archives can leave misleading target folders. Re-run only after checking the destination and removing incomplete archives or incomplete output folders deliberately.
- Dataset names are strict. A typo fails before download; do not guess a URL for an unsupported name.
- Some datasets come from third parties and may require citation or additional license review. Preserve the user's intended citation/licensing workflow in any handoff.
- The repository also contains an interactive Python data downloader based on HTTP requests and HTML parsing. It is reference-only here because it performs network I/O and the fixed shell-helper name lists above are enough for planning.

## Safe acquisition decision checklist

Before approving a download workflow, record:

1. dataset family (`cyclegan` zip pattern, `pix2pix` tar pattern, or licensed Cityscapes manual download),
2. exact dataset name,
3. target storage location and free-space expectation,
4. whether archive files should be kept or removed,
5. whether the user accepts third-party citation/license obligations,
6. whether a smaller local/synthetic fixture would satisfy the current verification task instead.
