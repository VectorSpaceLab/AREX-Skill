# Classification model overview

These facts are from the PytorchWildlife 1.3.0 classification wrappers and
its classifier model-zoo metadata. Names and counts are part of the runtime
contract; do not silently substitute labels from another release.

## PlainResNet family

| Public class | Architecture / input | Constructor choices | Output vocabulary |
|---|---|---|---|
| `AI4GAmazonRainforest` | PlainResNet-50; 224x224 inference transform | `pretrained=True`, `version="v1"` or `"v2"`; default is `"v2"` | 36 classes, ids 0-35 |
| `AI4GOpossum` | PlainResNet-50 backbone; 224x224 transform | `pretrained=True` or local `weights`; no version parameter | `0: Non-opossum`, `1: Opossum`; source uses one sigmoid logit |
| `AI4GSnapshotSerengeti` | PlainResNet-18; 224x224 transform | `pretrained=True` or local `weights` | 10 classes, ids 0-9 |
| `CustomWeights` | PlainResNet-50; 224x224 transform | local `weights` plus `class_names`; no pretrained URL | caller-supplied vocabulary |

### Amazon v1/v2 labels

Both Amazon versions use the same 36-label map in this package:

```text
0 Dasyprocta       1 Bos              2 Pecari            3 Mazama
4 Cuniculus        5 Leptotila        6 Human             7 Aramides
8 Tinamus          9 Eira            10 Crax             11 Procyon
12 Capra          13 Dasypus         14 Sciurus          15 Crypturellus
16 Tamandua       17 Proechimys      18 Leopardus        19 Equus
20 Columbina      21 Nyctidromus     22 Ortalis          23 Emballonura
24 Odontophorus   25 Geotrygon       26 Metachirus       27 Catharus
28 Cerdocyon      29 Momotus         30 Tapirus          31 Canis
32 Furnarius      33 Didelphis       34 Sylvilagus        35 Unknown
```

The spelling `Sylvilagus` is the literal class name exposed by the inspected
1.3.0 wrapper; preserve it when exporting labels.

### Serengeti labels

`AI4GSnapshotSerengeti` uses this exact id map:

```text
0 wildebeest       1 guineafowl       2 zebra
3 buffalo          4 gazellethomsons  5 gazellegrants
6 warthog          7 impala           8 hyenaspotted
9 other
```

## TIMM family

Both TIMM wrappers use the `vit_large_patch14_dinov2.lvd142m` backbone and a
182-pixel inference transform. They construct the TIMM model with
`num_classes=len(CLASS_NAMES)` and load a checkpoint under a model-specific
key. `DeepfauneClassifier` is documented as version **v1.3**; `DFNE`
(Deepfaune-New-England) is documented as version **v1.0**.

### `DeepfauneClassifier`

Use `class_name_lang` from exactly `fr`, `en`, `it`, or `de`; default is `en`.
The 34 ids are stable across languages, while only the display strings change.

| id | English (`en`) | French (`fr`) |
|---:|---|---|
| 0 | bison | bison |
| 1 | badger | blaireau |
| 2 | ibex | bouquetin |
| 3 | beaver | castor |
| 4 | red deer | cerf |
| 5 | chamois | chamois |
| 6 | cat | chat |
| 7 | goat | chevre |
| 8 | roe deer | chevreuil |
| 9 | dog | chien |
| 10 | fallow deer | daim |
| 11 | squirrel | ecureuil |
| 12 | moose | elan |
| 13 | equid | equide |
| 14 | genet | genette |
| 15 | wolverine | glouton |
| 16 | hedgehog | herisson |
| 17 | lagomorph | lagomorphe |
| 18 | wolf | loup |
| 19 | otter | loutre |
| 20 | lynx | lynx |
| 21 | marmot | marmotte |
| 22 | micromammal | micromammifere |
| 23 | mouflon | mouflon |
| 24 | sheep | mouton |
| 25 | mustelid | mustelide |
| 26 | bird | oiseau |
| 27 | bear | ours |
| 28 | nutria | ragondin |
| 29 | raccoon | raton laveur |
| 30 | fox | renard |
| 31 | reindeer | renne |
| 32 | wild boar | sanglier |
| 33 | cow | vache |

The Italian and German lists are exposed by the same constructor. Preserve
Unicode labels from the class map rather than transliterating them. The exact
Italian list is `bisonte, tasso, stambecco, castoro, cervo, camoscio, gatto,
capra, capriolo, cane, daino, scoiattolo, alce, equide, genetta, ghiottone,
riccio, lagomorfo, lupo, lontra, lince, marmotta, micromammifero, muflone,
pecora, mustelide, uccello, orso, nutria, procione, volpe, renna, cinghiale,
mucca`. The German list is `Bison, Dachs, Steinbock, Biber, Rothirsch, Gämse,
Katze, Ziege, Rehwild, Hund, Damwild, Eichhörnchen, Elch, Equide, Ginsterkatze,
Vielfraß, Igel, Lagomorpha, Wolf, Otter, Luchs, Murmeltier, Kleinsäuger, Mufflon,
Schaf, Marder, Vogel, Bär, Nutria, Waschbär, Fuchs, Rentier, Wildschwein, Kuh`.

### `DFNE`

DFNE has 24 fixed English labels:

```text
0 American Marten       1 Bird sp.             2 Black Bear
3 Bobcat                4 Coyote               5 Domestic Cat
6 Domestic Cow          7 Domestic Dog         8 Fisher
9 Gray Fox             10 Gray Squirrel       11 Human
12 Moose               13 Mouse sp.            14 Opossum
15 Raccoon             16 Red Fox              17 Red Squirrel
18 Skunk               19 Snowshoe Hare        20 White-tailed Deer
21 Wild Boar            22 Wild Turkey          23 no-species
```

`DeepfauneClassifier` and `DFNE` use different checkpoint keys: the former
expects `state_dict` and removes `base_model.` from every key; DFNE expects
`model_state_dict` and does not remove a prefix by default.
