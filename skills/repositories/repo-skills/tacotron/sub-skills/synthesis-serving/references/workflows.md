# Synthesis workflows

## Batch output

```bash
SKILL_ROOT=/path/to/tacotron-skill
CHECKOUT_ROOT=/path/to/tacotron-checkout
cd "$SKILL_ROOT" && python sub-skills/synthesis-serving/scripts/build_synthesis_command.py --checkout-root "$CHECKOUT_ROOT" --mode eval --checkpoint /data/logs-tacotron/model.ckpt-185000 --hparams max_iters=300
```

Review the printed command, then intentionally execute that `cd
"$CHECKOUT_ROOT" && python eval.py ...` command only if the checkpoint and
checkout are available. Only pass the hparam override when it matches the
training run or when you have explicitly accepted checkpoint compatibility risk.
Check that the output base path is writable beside the checkpoint. This dry-run
does not load weights or produce audio.

## Browser demo

```bash
cd "$SKILL_ROOT" && python sub-skills/synthesis-serving/scripts/build_synthesis_command.py --checkout-root "$CHECKOUT_ROOT" --mode server --checkpoint /data/logs-tacotron/model.ckpt-185000 --port 9000
```

Review the printed command and execute it from the checkout only if a local
listener is approved. Open the local URL only after the process reports it
loaded the checkpoint. For remote use, bind/route through an authenticated
service rather than assuming the demo HTML provides security.

## Forced pronunciation and length

The text route supports inline ARPAbet braces. The decoder is bounded by
`max_iters`; long text or long expected audio may truncate or fail. Use the
same text cleaner and length-related hparams as training.
