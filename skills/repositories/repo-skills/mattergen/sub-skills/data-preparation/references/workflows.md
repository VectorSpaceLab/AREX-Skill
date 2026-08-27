# Released-data and preprocessing workflows

This reference routes MP-20 and Alex-MP-20 preparation without silently
starting a large download or conversion. First run the safe
[CSV validator](../scripts/validate_dataset_csv.py); then invoke the actual
package converter only after storage, split, and provenance checks pass.

## MP-20

The released MP-20 instructions describe the following opt-in sequence:

```bash
# Acquire <MP20_ARCHIVE>.zip explicitly, then verify it is a real archive.
unzip <MP20_ARCHIVE>.zip -d <DATA_ROOT>
python <mattergen-skill-root>/sub-skills/data-preparation/scripts/validate_dataset_csv.py \
  --csv-folder <DATA_ROOT>/mp_20
csv-to-dataset \
  --csv-folder <DATA_ROOT>/mp_20 \
  --dataset-name mp_20 \
  --cache-folder <CACHE_ROOT>
```

The package documentation describes the resulting cache as
`datasets/cache/mp_20`. The package MP-20 data config expects `train`, `val`,
and `test` below the cache dataset root. Confirm the extracted CSV names before
conversion; the converter processes all `.csv` files, not just those three
names.

## Alex-MP-20

Alex-MP-20 is the larger released training dataset. Its documented sequence is:

```bash
# Acquire <ALEX_MP20_ARCHIVE>.zip explicitly, then verify it is a real archive.
unzip <ALEX_MP20_ARCHIVE>.zip -d <DATA_ROOT>
python <mattergen-skill-root>/sub-skills/data-preparation/scripts/validate_dataset_csv.py \
  --csv-folder <DATA_ROOT>/alex_mp_20
csv-to-dataset \
  --csv-folder <DATA_ROOT>/alex_mp_20 \
  --dataset-name alex_mp_20 \
  --cache-folder <CACHE_ROOT>
```

The Alex-MP-20 data config expects `train` and `val` below the cache dataset
root. The README estimates about one hour for this preprocessing. Treat that as
a planning signal, not a guarantee: CIF parsing and disk speed vary.

LFS download and unzip are deliberately opt-in. An archive that is only an LFS
pointer is not usable input. Check `git lfs --version` and inspect the archive
with `file` or `unzip -t` before allocating a conversion run. Do not download
reference energy archives, CIF presentation data, or measurement files for
training preprocessing; they are separate releases.

## Storage-first routing

For a small disk, do not launch Alex-MP-20 blindly. The archive, extracted CSVs,
and generated NumPy/JSON cache may coexist, and the repository does not publish
one fixed byte budget. Use a destination with measured free space:

```bash
df -h <DATA_ROOT> <CACHE_ROOT>
du -sh <ALEX_MP20_ARCHIVE>.zip <DATA_ROOT>/alex_mp_20 <CACHE_ROOT>/alex_mp_20 2>/dev/null || true
```

If space is tight, keep the archive and cache on a larger filesystem, use that
location as `--cache-folder`, and remove the archive only after extraction and
provenance checks succeed. Validate a small copy or a bounded sample with
`--limit-rows` first, but do not treat a limited run as full validation. A
successful limited probe does not make a full conversion safe.

The converter accepts generic paths, so a storage-aware run can look like:

```bash
csv-to-dataset --csv-folder <DATA_ROOT>/alex_mp_20 \
  --dataset-name alex_mp_20 \
  --cache-folder <CACHE_ROOT>
```

Before training, point Hydra at the resulting dataset root if it is not the
package's default location:

```bash
mattergen-train data_module=alex_mp_20 \
  data_module.root_dir=<CACHE_ROOT>/alex_mp_20 \
  ~trainer.logger trainer.accumulate_grad_batches=4
```

Use the same root override for fine-tuning. Confirm that every configured split
exists before starting a trainer; a cache path override does not create missing
splits.

## Training and fine-tuning handoff

After cache validation, the documented base-training entry points are:

```bash
mattergen-train data_module=mp_20 ~trainer.logger
mattergen-train data_module=alex_mp_20 ~trainer.logger trainer.accumulate_grad_batches=4
```

Fine-tuning adds the selected property to both the data module and property
embedding configuration. Follow [custom-properties](custom-properties.md) when
the property is not already configured. This sub-skill does not decide whether a
label is scientifically valid, reproduce DFT energies, or evaluate generated
structures.
