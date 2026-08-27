# Preprocessing workflow

## One target font

Create one output directory for rendered pairs and one experiment data directory
for packaged objects:

```sh
mkdir -p samples experiment/data
python font2img.py \
  --src_font=fonts/source.ttf \
  --dst_font=fonts/target.otf \
  --charset=CN \
  --sample_count=1000 \
  --sample_dir=samples \
  --label=0 \
  --filter=1 \
  --shuffle=1

python package.py \
  --dir=samples \
  --save_dir=experiment/data \
  --split_ratio=0.1
```

Validate:

```sh
ls samples/*.jpg | head
ls experiment/data/train.obj experiment/data/val.obj
```

Then inspect the object stream with the bundled Python 3 helper:

```sh
python scripts/inspect_zi2zi_obj.py experiment/data/train.obj experiment/data/val.obj --image-check
```

## Multiple target fonts

Render all target styles into the same sample directory with different labels:

```sh
mkdir -p samples experiment/data
python font2img.py --src_font=fonts/source.ttf --dst_font=fonts/style_a.otf --charset=CN --sample_count=1000 --sample_dir=samples --label=0 --filter=1 --shuffle=1
python font2img.py --src_font=fonts/source.ttf --dst_font=fonts/style_b.otf --charset=CN --sample_count=1000 --sample_dir=samples --label=1 --filter=1 --shuffle=1
python font2img.py --src_font=fonts/source.ttf --dst_font=fonts/style_c.otf --charset=CN --sample_count=1000 --sample_dir=samples --label=2 --filter=1 --shuffle=1
python package.py --dir=samples --save_dir=experiment/data --split_ratio=0.1
```

For training, set `--embedding_num` to at least the number of distinct labels.
If you later fine-tune a subset, keep label IDs stable.

## Custom charset

Create a one-line UTF-8 file containing only the characters to render:

```sh
printf '天地玄黄宇宙洪荒' > charset.txt
python font2img.py \
  --src_font=fonts/source.ttf \
  --dst_font=fonts/target.otf \
  --charset=charset.txt \
  --sample_count=8 \
  --sample_dir=samples \
  --label=0 \
  --filter=0
```

For tiny smoke tests, disable filtering (`--filter=0`) so the filter pre-sample
step does not dominate runtime or skip all characters.

## Using the planner helper

The bundled planner prints commands and catches common label/path mistakes
without running the original renderer:

```sh
python sub-skills/data-preparation/scripts/zi2zi_font_pair_planner.py \
  --src-font fonts/source.ttf \
  --target-font 0=fonts/style_a.otf \
  --target-font 1=fonts/style_b.otf \
  --charset CN \
  --sample-root samples \
  --package-save-dir experiment/data \
  --check-paths
```

It is safe to use in Python 3 because it only validates inputs and prints
command templates.

## Reproducibility notes

The original `font2img.py` and `package.py` use random shuffling/splitting
without a seed flag. For strict reproducibility, record the rendered sample set
or patch a local maintenance copy to set random seeds. Do not promise that two
runs with the same command will produce identical train/validation splits.
