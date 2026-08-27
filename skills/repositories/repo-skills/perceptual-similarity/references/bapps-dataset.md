# BAPPS Dataset Guide

## Purpose

Read this when you need the dataset layout, split names, or a smoke fixture for the BAPPS evaluation and training helpers.

## Official layout

The dataset root is expected to contain two top-level groups:

```text
dataset/
  2afc/
    train/
      traditional/
      cnn/
      mix/
    val/
      traditional/
      cnn/
      superres/
      deblur/
      color/
      frameinterp/
  jnd/
    val/
      traditional/
      cnn/
```

### 2AFC split contents

Each `2afc` split contains:

```text
ref/
 p0/
 p1/
 judge/
```

- `ref/` — reference images.
- `p0/` and `p1/` — distorted candidates.
- `judge/` — `.npy` labels, typically `0` or `1`, stored as small arrays.

### JND split contents

Each `jnd` split contains:

```text
p0/
 p1/
 same/
```

- `same/` — `.npy` labels indicating whether the two patches were judged identical.

## Bundled smoke fixture

The skill ships with copied example images under `assets/examples/` so you can build a tiny local BAPPS-style fixture without the original repository.

Use the bundled fixture builder:

```bash
python skills/disco/perceptual-similarity/scripts/make_tiny_bapps_fixture.py --output-root /tmp/perceptual-similarity-fixture
```

That creates a fixture shaped like:

```text
/tmp/perceptual-similarity-fixture/
  dataset/
    2afc/
      tiny/
        ref/
        p0/
        p1/
        judge/
    jnd/
      tiny/
        p0/
        p1/
        same/
```

Then point the evaluation or training helper at `/tmp/perceptual-similarity-fixture/dataset`.

## Alignment rules used by the bundled helpers

The bundled helpers do not silently guess when files are missing or misordered.

- Each split must have matching relative file names across the required subdirectories.
- Missing `ref`, `p0`, `p1`, `judge`, or `same` files are treated as layout errors.
- The helpers accept either a full dataset root or a direct split path, but they still verify the expected subdirectory structure.

## Small-split examples

Good examples of split names:

- `train/traditional`
- `train/cnn`
- `val/traditional`
- `val/superres`
- `tiny`

The bundled tiny fixture uses `tiny` so that smoke tests stay short and deterministic.
