# Legacy Extension Workflows

## 1. Import and utility check

```bash
python scripts/legacy_rules_smoke.py --no-model
```

This checks `ltp_extension`, `CharacterType`, `StnSplit`, `Hook`, and entity utilities without loading legacy model files.

## 2. High-level legacy CWS/POS/NER

```python
from ltp import LTP

ltp = LTP("LTP/legacy")
ltp.add_word("汤姆去", freq=2)
result = ltp.pipeline(["他叫汤姆去拿外衣。"], tasks=["cws", "pos", "ner"])
print(result.cws, result.pos, result.ner)
```

Do not request `srl`, `dep`, `sdp`, or `sdpg` from the legacy model.

## 3. Direct CWS/POS/NER model files

```python
from ltp_extension.perceptron import CWSModel, POSModel, NERModel

cws = CWSModel.load("cws_model.bin")
pos = POSModel.load("pos_model.bin")
ner = NERModel.load("ner_model.bin")
words = cws.predict("他叫汤姆去拿外衣。")
pos_tags = pos.predict(words)
ner_tags = ner.predict(words, pos_tags)
```

Use direct classes when a task already has local binary model files and does not need high-level Hugging Face config resolution.

## 4. Custom character-type rules

```python
from ltp_extension.perceptron import CharacterType

# Split Roman-to-Kanji boundaries and keep digit-roman spans together.
cws.enable_type_cut_d(CharacterType.Roman, CharacterType.Kanji)
cws.enable_type_concat(CharacterType.Digit, CharacterType.Roman)
```

Use these rules for mixed strings such as product names, roman letters, digits, and Chinese characters. Validate on domain examples before enabling globally.

## 5. Legacy training configuration

```bash
python scripts/legacy_trainer_config_check.py --task cws --train-file train.txt --eval-file dev.txt --algorithm AP
python scripts/legacy_trainer_config_check.py --task pos --labels n,v,wp --train-file train.txt --eval-file dev.txt --algorithm PaI --param 0.5
```

After validation, construct trainers in code:

```python
from ltp_extension.perceptron import Algorithm, CWSTrainer
trainer = CWSTrainer()
trainer.epoch = 10
trainer.algorithm = Algorithm("AP")
trainer.load_train_data("train.txt")
trainer.load_eval_data("dev.txt")
model = trainer.train()
```

Training is not safe as an automatic diagnostic; ask before running it.

## 6. Entity and algorithm utilities

Use `get_entities` to convert BIO/BMES-style tags into spans. Use `eisner` only when you have score arrays and sentence lengths shaped for dependency decoding; ordinary users should prefer high-level neural DEP/SDP outputs.
