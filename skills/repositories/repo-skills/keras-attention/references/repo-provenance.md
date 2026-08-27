# Repo provenance

Schema: `disco.repo-provenance.v1`

## Source snapshot

- Repository: Keras Attention Layer (`attention` package)
- Public remote URL: `https://github.com/philipperemy/keras-attention.git`
- Source commit: `79a2db30e3f0ff2788f1cb12b5f279b746e50022`
- Branch at extraction: `master`
- Exact tag at extraction: none detected
- Package version from source metadata: `5.0.0`
- License: Apache 2.0

## Dirty state note

The checkout was already dirty before generated skill files were written:

```text
?? skills/keras-attention.log
```

That pre-existing production log was not used as package evidence. Generated
`skills/disco/` and `skills/tests/` outputs are construction artifacts, not part
of the source package baseline.

## Evidence paths used

| Relative path | Evidence role |
| --- | --- |
| `README.md` | Public install guidance, constructor arguments, input/output shape contract, basic example, example descriptions, tested TensorFlow range, references. |
| `setup.py` | Distribution name, version, dependencies, package metadata. |
| `tox.ini` | TensorFlow version matrix, protobuf environment setting, and focused native example command. |
| `.github/workflows/ci.yml` | CI Python versions and test/lint invocation context. |
| `attention/__init__.py` | Public import surface. |
| `attention/attention.py` | `Attention` implementation, score branches, debug flag, serialization config, layer names, and error messages. |
| `examples/example-attention.py` | Basic layer use, Luong/Bahdanau native candidate, save/load round trip. |
| `examples/add_two_numbers.py` | Debug-mode delimiter-sum visualization pattern and optional dependency needs. |
| `examples/find_max.py` | Debug-mode max-of-sequence visualization pattern. |
| `examples/imdb.py` | Long IMDB comparison workflow and runtime cautions. |
| `examples/examples-requirements.txt` | Optional visualization dependencies (`keract`, `matplotlib`, `pydot`). |
| `LICENSE` | Apache 2.0 license text. |

## Inspection facts confirmed

A private inspection environment installed the package and confirmed these
public facts without requiring a GPU:

- Distribution metadata: `attention==5.0.0`.
- Runtime stack used for inspection: TensorFlow 2.15.1, Keras 2.15.0, NumPy
  1.26.4.
- Optional visualization packages imported: `keract`, `matplotlib`, `pydot`;
  Graphviz `dot` was available in the inspection environment.
- `from attention import Attention` succeeds.
- Public constructor signature: `Attention(units: int = 128, score: str =
  "luong", **kwargs)`.
- Valid scores are `"luong"` and `"bahdanau"`; invalid scores raise the
  repository's documented `ValueError`.
- Tiny CPU TensorFlow/Keras models using both score functions produced expected
  output shapes and saved/loaded with `custom_objects={"Attention": Attention}`.
- `KERAS_ATTENTION_DEBUG=1` must be set before import and makes `Attention` no
  longer subclass Keras `Layer`, matching the repository's debug-introspection
  comments.

## Staleness checks for future refresh

Refresh this skill if any of these change in a future checkout or release:

- `Attention` constructor parameters, valid score values, output shape, or
  serialization behavior.
- The package distribution/import names or dependencies in setup metadata.
- TensorFlow/Keras compatibility claims or tested version ranges.
- The debug-mode contract, `attention_weight` layer name, or example dependency
  list.
- The example workflows' safety/resource profile, especially if long demos are
  replaced by maintained smoke tests.
