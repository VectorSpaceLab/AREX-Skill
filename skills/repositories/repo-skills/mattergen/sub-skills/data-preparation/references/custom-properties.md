# Custom property columns

Use this route when a training or fine-tuning dataset has a label that is not
already selected by the data-module YAML. A CSV column alone is not enough:
the converter copies only property names registered by MatterGen, and a
conditional model also needs a compatible property embedding.

## Supported-property route

For an existing property, select the exact registry name in every relevant CSV
split and in the data module. The released configs document these common
choices:

- MP-20: `dft_bulk_modulus`, `dft_band_gap`, and `dft_mag_density`.
- Alex-MP-20: those plus `ml_bulk_modulus`, `hhi_score`, `space_group`, and
  `energy_above_hull`.

The full package registry is listed in [data-formats](data-formats.md). Names
are case-sensitive and are not aliases for similarly named source columns such
as `band_gap`, `spacegroup.number`, or `e_above_hull`.

Use a schema-and-structure preflight before conversion:

```bash
python <SKILL_DIR>/scripts/validate_dataset_csv.py \
  --csv-folder <CSV_FOLDER> \
  --property dft_band_gap \
  --property dft_mag_density
```

The validator requires each selected property column in every CSV file. It
reports partial missingness as a warning because the package's
`filter_sparse_properties` dataset transform drops structures missing any
selected property. An entirely empty selected column is a blocking error.
Keep train/val/test property columns aligned even when only a subset of rows is
labeled; otherwise the cache schema is inconsistent.

## Adding a new property

The documented custom-property procedure is:

1. Add the exact property name to MatterGen's `PROPERTY_SOURCE_IDS` registry.
2. Add a column with that exact name to each dataset CSV used for training and
   validation; values may cover only a subset of structures.
3. Re-run `csv-to-dataset` for the dataset so the property JSON is generated.
4. Add the corresponding property-embedding configuration. A float label can
   follow an existing scalar embedding pattern; categorical or structured
   values need an appropriate custom `PropertyEmbedding` implementation.
5. Add the property to the data-module `properties` list and configure the
   adapter/model to use its embedding before fine-tuning.

Do not claim that a validator-passing arbitrary column will be learned. If the
name is not in the installed registry, the validator rejects it because the
converter will ignore it. If the registry was changed after an old cache was
built, rebuild into a fresh cache or verify that `<property>.json` was actually
written and has one value per `structure_id.npy` entry.

## Value and provenance checks

The data types supported by the package's target-property type include scalar
integers/floats, strings, and sequences of strings, but the selected embedding
must agree with the actual values. `space_group` is interpreted as a
pymatgen space-group symbol and converted to its number when loaded. Do not
silently rename or numerically encode it in the CSV. `chemical_system` is
normally set by the dataset transform from atomic numbers rather than treated
as an ordinary user label.

Record, outside the runtime skill, the label source, units, calculation method,
version, missing-value convention, structure-ID join rule, and license. The
cache stores property values and a property-source document ID, not a guarantee
that the values are scientifically comparable. A sparse label should be
filtered or split intentionally; do not fill missing values with zero without
scientific evidence.

The model card recommends several thousand labeled structures and coverage over
the intended target range for property-guided generation. A tiny or highly
skewed custom label set may still preprocess successfully but is a model-quality
risk that belongs in the experiment record.
