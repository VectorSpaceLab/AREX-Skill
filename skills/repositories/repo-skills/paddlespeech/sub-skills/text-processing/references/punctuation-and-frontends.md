# Punctuation and Text Frontend Reference

## Punctuation CLI

```bash
paddlespeech text --task punc --input 今天的天气真不错啊你下午有空吗我想约你一起去吃饭
paddlespeech text --task punc --model ernie_linear_p3_wudao_fast --input 今天的天气真不错啊你下午有空吗我想约你一起去吃饭
```

Options:

- `--task`: currently `punc`.
- `--model`: `ernie_linear_p7_wudao`, `ernie_linear_p3_wudao`, or `ernie_linear_p3_wudao_fast`.
- `--lang`: parser accepts `zh` and `en`, but released punctuation resources in this checkout are Chinese-focused.
- `--config`, `--ckpt_path`, `--punc_vocab`: use custom punctuation resources.
- `--device`: Paddle runtime device.
- `-d`: dump job results for job input.

Python executor:

```python
import paddle
from paddlespeech.cli.text import TextExecutor

text = TextExecutor()
out = text(text="今天的天气真不错啊你下午有空吗", task="punc", model="ernie_linear_p3_wudao_fast", lang="zh", device=paddle.get_device())
```

## Cleaning Behavior

The punctuation executor lowercases input and removes characters outside letters, digits, and Chinese ideographs before tokenization. If the cleaned string is empty, it raises an invalid-input assertion. Use the helper script to preview this behavior.

## ERNIE Model Notes

The punctuation model code uses `ErnieLinear` and PaddleNLP tokenizers. Older/newer PaddleNLP or AIStudio SDK combinations can break imports. If the module imports but model initialization downloads resources, confirm network/cache side effects.

## Frontend and Recipe Tools

PaddleSpeech examples include text processing utilities used by ASR/TTS recipes:

- **G2P**: phoneme prediction/evaluation recipes; usually depends on a dataset and scoring tool.
- **Text normalization**: raw/normed test case recipes and CER evaluation.
- **MFA**: forced aligner workflows for duration/rhythm tags; external MFA and dataset requirements.
- **SentencePiece**: English tokenizer model training and unit-file generation.

These are valuable planning references but not safe default commands: they can require external downloads, host tool installs, and staged shell recipes.
