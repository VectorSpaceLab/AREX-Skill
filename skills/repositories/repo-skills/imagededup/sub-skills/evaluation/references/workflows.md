# Evaluation and plotting workflows

## 1. Validate retrieved results against a symmetric ground-truth map

```python
from imagededup.evaluation import evaluate

metrics = evaluate(
    ground_truth_map=ground_truth,
    retrieved_map=retrieved,
    metric='all',
)
```

Use this when you already have a duplicate map and want a full score bundle.

## 2. Score one metric family at a time

- `metric='map'`
- `metric='ndcg'`
- `metric='jaccard'`
- `metric='classification'`

Choose one metric when you only need one headline value or one family of outputs.

## 3. Plot one duplicate group

```python
from imagededup.utils import plot_duplicates

plot_duplicates(
    image_dir='path/to/images',
    duplicate_map=duplicate_map,
    filename='image.jpg',
    outfile='duplicates.png',
)
```

Good plotting inputs:

- the image directory exists
- the filename exists as a key in the map
- the duplicate list for that key is not empty

## 4. Choose the right duplicate-map shape

- plain filenames: `{'a.jpg': ['b.jpg']}`
- scored tuples: `{'a.jpg': [('b.jpg', 0.97)]}`

`plot_duplicates` accepts both forms.

## 5. Validate the map before scoring it

A valid map for this repo should:

- contain the same keys on both sides of the comparison
- preserve symmetry
- avoid foreign filenames that are not already keys

## 6. Recommended smoke flow

Use the bundled smoke script when you want a quick metrics-and-plot check without repo fixtures:

```bash
python scripts/evaluate_plot_smoke.py
```

That script creates a tiny synthetic image set, evaluates a symmetric duplicate map, and writes a plot file.

## 7. When a plotting request is really an encoding request

If the user has not yet produced a duplicate map, send them to the hashing or CNN sub-skill first.

## 8. Headless environments

When running in a noninteractive environment, set or keep a noninteractive matplotlib backend such as Agg before plotting.