# Classification Workflow

## 1. Confirm labels and prompts

- Make sure the class ids are known up front.
- Use the repo’s default `A/B` mapping only if it matches the task.
- Add a task prompt when the dataset needs one; otherwise the repo can inject the default user message.

## 2. Choose a head and loss

- Start with cross-entropy for balanced data.
- Move to focal or class-balanced losses when one class dominates.
- Add an MLP head only if the plain classifier head is not expressive enough.

## 3. Decide on finetuning scope

- Full finetuning is the simplest path.
- LoRA is useful when the user wants to keep most of the model frozen.
- Vision and merger flags follow the same freeze logic as the training code.

## 4. Launch safely

Use the bundled command builder before running the trainer. It runs `src/train/train_cls.py` from the skill root with `PYTHONPATH=src`, so it does not require the original checkout.

```bash
python scripts/classification_command.py --help
python scripts/classification_command.py --model-id Qwen/Qwen2.5-VL-3B-Instruct --data-path data/cls_train.json --image-folder data/images --output-dir outputs/cls
# add --run only when the printed command should be executed
```

## 5. Review results

- Check weighted F1 as the repo’s early-stopping metric.
- Confirm that the eval split uses the same prompt and label semantics as the train split.
