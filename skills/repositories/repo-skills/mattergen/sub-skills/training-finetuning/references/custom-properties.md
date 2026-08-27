# Custom properties and conditional fine-tuning

A property-conditioned run has two separate contracts:

1. the datamodule must load a property value from the prepared cache; and
2. the model/adapter must have a matching property-embedding configuration.

Adding only a CLI name does not satisfy either contract.

## Existing properties

The checked-in data-module comments document these common names:

- MP-20: `dft_bulk_modulus`, `dft_band_gap`, `dft_mag_density`.
- Alex-MP-20: those names plus `ml_bulk_modulus`, `hhi_score`,
  `space_group`, and `energy_above_hull`.
- The source property allow-list also contains `chemical_system`,
  `dft_shear_modulus`, and `formation_energy_per_atom`; whether a given
  dataset split has usable values still must be checked in its cache.

Existing embedding YAML files include float-style embeddings for
`dft_band_gap`, `dft_mag_density`, `dft_bulk_modulus`, `energy_above_hull`,
`hhi_score`, and `ml_bulk_modulus`, plus categorical/vector configurations for
`chemical_system` and `space_group`. Float configurations use
`NoiseLevelEncoding` and a `StandardScalerTorch`; bulk-modulus variants enable
`log10_transform`. Do not infer that a source id is available merely because it
is present in the allow-list.

## Add a property to user data

The README's supported sequence is:

1. Add the property name to the `PROPERTY_SOURCE_IDS` list in the source's
   globals module.
2. Add a column with exactly that name to the relevant `train.csv` and
   `val.csv` (and `test.csv` if a test split is used). Values are usually
   floats, and unlabeled structures may remain sparse depending on the dataset
   transform.
3. Re-run `csv-to-dataset` for the dataset so the cache contains the new
   property JSON files. The builder only persists columns whose names are in
   its registered source-id list.
4. Add `<property>.yaml` under the `lightning_module/diffusion_module/model/property_embeddings`
   config group. For a float-valued property, the README suggests copying a
   float config such as `dft_mag_density.yaml`; categorical properties need an
   embedding module compatible with their values, such as the `space_group` or
   `chemical_system` examples.
5. Fine-tune with the same property name in the adapter config-group override
   and in `data_module.properties`.

This is a package-source change for a genuinely new source id, despite the
runtime command itself being a Hydra override. It must be reviewed and tested
in the repository checkout before training. A config-only command cannot make
`CrystalDatasetBuilder` accept an unknown property source id.

## Fine-tune an existing or custom property

For one property `p`, the essential pair is:

```text
+lightning_module/diffusion_module/model/property_embeddings@adapter.adapter.property_embeddings_adapt.p=p
data_module.properties=["p"]
```

The first line composes the YAML config into the adapter mapping. The second
line causes the datamodule/datasets to load `p`. For multiple properties, repeat
the first line once per property and list every property in the second line.
Use `adapter.pretrained_name=mattergen_base` for the published model or
`adapter.model_path=<user-owned-model-output>` for a local checkpoint.

For base conditional training rather than adapter fine-tuning, place the
property embedding in the base model's `property_embeddings` destination with
the documented form:

```text
+lightning_module/diffusion_module/model/property_embeddings@lightning_module.diffusion_module.model.property_embeddings.p=p
```

That is a different optimization path from the README's adapter command and
should be described as such in the run record.

## Labels, scaling, and sparse data

The property embedding's `scaler` is part of the model config. The callback
`SetPropertyScalers` fits non-identity scalers from the training datamodule at
setup time. Check that the training values have a meaningful range, no
unexpected units, and enough labeled structures; the model card recommends at
least several thousand labeled structures and coverage of the target range for
new-property fine-tuning. This is a quality recommendation, not a verified
threshold for the user's data.

With multiple properties and the default `dropout_fields_iid: false`, a sample
must have all requested values present before it participates in the joint
conditional embedding state. A missing value therefore changes the training
signal; it is not equivalent to a zero. If the user's intended behavior is
independent partial conditioning, review the `dropout_fields_iid` setting and
its implications before changing it.

## Validation checklist

Before launch, verify all of the following without training:

- exact property spelling is consistent across CSV, source allow-list, cache
  JSON, embedding YAML, adapter destination, and `data_module.properties`;
- every expected split has the core arrays and requested property JSON;
- float values have expected units and a valid range; categorical values match
  the embedding implementation;
- the property embedding's `name` matches its file/config key;
- a multi-property command has one adapter override per property;
- no adapter property duplicates a base model property;
- the effective batch and device/backend are safe;
- the source checkpoint and selected `load_epoch` exist.

Use [validate_hydra_overrides.py](../scripts/validate_hydra_overrides.py) for
config-file presence, then perform data-content checks through the data-
preparation route rather than adding a training launch to the preflight.
