#!/usr/bin/env python3
from __future__ import annotations

import argparse
import multiprocessing as mp
from time import perf_counter


def pos(v):
    value = int(v)
    if value <= 0:
        raise argparse.ArgumentTypeError("must be positive")
    return value


def common(p):
    p.add_argument("--model", required=True)
    p.add_argument("--initial_peers", nargs="+")
    p.add_argument("--torch_dtype", default="float32", choices=("float32", "float16", "bfloat16", "auto"))
    p.add_argument("--n_processes", default="1")
    p.add_argument("--seq_len", type=pos)
    p.add_argument("--warmup_steps", type=pos, default=1)
    p.add_argument("--execute", action="store_true", help="Actually run the benchmark. Without this flag, only print the resolved plan.")


def parser():
    p = argparse.ArgumentParser(
        description="Run bundled Petals benchmark families after explicit approval. Execution may use network, caches, DHT peers, model downloads, and local devices."
    )
    sub = p.add_subparsers(dest="fam", required=True)
    inf = sub.add_parser("inference")
    common(inf)
    inf.set_defaults(seq_default=2048)
    fwd = sub.add_parser("forward")
    common(fwd)
    fwd.add_argument("--batch_size", type=pos, required=True)
    fwd.add_argument("--n_steps", type=pos, default=100)
    fwd.set_defaults(seq_default=128)
    tr = sub.add_parser("training")
    common(tr)
    tr.add_argument("--device", default="cpu")
    tr.add_argument("--task", choices=("cls", "causal_lm"), default="cls")
    tr.add_argument("--batch_size", type=pos, required=True)
    tr.add_argument("--pre_seq_len", type=pos, default=16)
    tr.add_argument("--n_steps", type=pos, default=10)
    tr.set_defaults(seq_default=128)
    return p


def normalize(args):
    if args.seq_len is None:
        args.seq_len = args.seq_default
    if args.n_processes == "n_gpus":
        if not args.execute:
            args.n_processes_resolved = "visible CUDA GPU count at execution time"
        else:
            import torch

            args.n_processes_resolved = torch.cuda.device_count()
    else:
        args.n_processes_resolved = int(args.n_processes)
        if args.n_processes_resolved <= 0:
            raise SystemExit("--n_processes must be positive or n_gpus")
    return args


def dtype_map(name):
    from petals.constants import DTYPE_MAP

    return DTYPE_MAP[name]


def model_kwargs(args):
    kwargs = {"torch_dtype": dtype_map(args.torch_dtype)}
    if args.initial_peers:
        kwargs["initial_peers"] = args.initial_peers
    return kwargs


def run_processes(args, target):
    import numpy as np

    pipe_recv, pipe_send = mp.Pipe(duplex=False)
    processes = [mp.Process(target=target, args=(i, args, pipe_send)) for i in range(int(args.n_processes_resolved))]
    for proc in processes:
        proc.start()
    for proc in processes:
        proc.join()
    if any(proc.exitcode for proc in processes):
        raise SystemExit(f"one or more benchmark workers failed: {[proc.exitcode for proc in processes]}")
    return np.mean([pipe_recv.recv() for _ in range(int(args.n_processes_resolved))], axis=0)


def bench_inference_worker(process_idx, args, result_pipe):
    import numpy as np
    import torch
    from transformers import AutoTokenizer
    from petals import AutoDistributedModelForCausalLM

    tokenizer = AutoTokenizer.from_pretrained(args.model, use_fast=False)
    model = AutoDistributedModelForCausalLM.from_pretrained(args.model, **model_kwargs(args))
    result = ""
    step_times = []
    with torch.inference_mode(), model.transformer.h.inference_session(max_length=args.seq_len) as sess:
        for step in range(args.seq_len):
            start = perf_counter()
            outputs = model.generate(max_new_tokens=1, session=sess)
            result += tokenizer.decode(outputs[0])
            if step >= args.warmup_steps:
                step_times.append(perf_counter() - start)
                print(f"process_idx={process_idx} step={step} speed={1 / np.mean(step_times):.2f}", flush=True)
    result_pipe.send(1 / np.mean(step_times))


def bench_forward_worker(process_idx, args, result_pipe):
    import numpy as np
    import torch
    from petals import AutoDistributedModel

    model = AutoDistributedModel.from_pretrained(args.model, **model_kwargs(args))
    torch.manual_seed(42)
    step_times = []
    with torch.inference_mode():
        for step in range(args.warmup_steps + args.n_steps):
            input_ids = torch.randint(0, model.config.vocab_size, size=(args.batch_size, args.seq_len))
            start = perf_counter()
            _ = model(input_ids)
            if step >= args.warmup_steps:
                step_times.append(perf_counter() - start)
                speed = input_ids.numel() / np.mean(step_times)
                print(f"process_idx={process_idx} step={step} speed={speed:.2f}", flush=True)
    result_pipe.send(input_ids.numel() / np.mean(step_times))


def bench_training_worker(process_idx, args, result_pipe):
    import numpy as np
    import torch
    from petals import AutoDistributedModelForCausalLM, AutoDistributedModelForSequenceClassification

    cls = AutoDistributedModelForSequenceClassification if args.task == "cls" else AutoDistributedModelForCausalLM
    kwargs = dict(model_kwargs(args), tuning_mode="deep_ptune", pre_seq_len=args.pre_seq_len)
    if args.task == "cls":
        kwargs["num_labels"] = 2
    model = cls.from_pretrained(args.model, **kwargs).to(args.device)
    opt = torch.optim.Adam([p for p in model.parameters() if p.requires_grad])
    torch.manual_seed(42)
    fwd_times, bwd_times = [], []
    for step in range(args.warmup_steps + args.n_steps):
        input_ids = torch.randint(0, model.config.vocab_size, size=(args.batch_size, args.seq_len), device=args.device)
        labels = torch.randint(0, 2, size=[args.batch_size], device=args.device) if args.task == "cls" else input_ids
        start = perf_counter()
        outputs = model(input_ids, labels=labels)
        if step >= args.warmup_steps:
            fwd_times.append(perf_counter() - start)
        start = perf_counter()
        outputs.loss.backward()
        if step >= args.warmup_steps:
            bwd_times.append(perf_counter() - start)
        opt.step(); opt.zero_grad(set_to_none=True)
        if step >= args.warmup_steps:
            print(
                f"process_idx={process_idx} step={step} fwd_speed={input_ids.numel() / np.mean(fwd_times):.2f} bwd_speed={input_ids.numel() / np.mean(bwd_times):.2f}",
                flush=True,
            )
    result_pipe.send((input_ids.numel() / np.mean(fwd_times), input_ids.numel() / np.mean(bwd_times)))


def dry_run(args):
    print(f"Bundled Petals benchmark runner plan: {args.fam}")
    print(f"model={args.model}")
    print(f"initial_peers={'provided' if args.initial_peers else 'Petals public default at execution time'}")
    print(f"torch_dtype={args.torch_dtype} n_processes={args.n_processes_resolved} seq_len={args.seq_len} warmup_steps={args.warmup_steps}")
    if args.fam in ("forward", "training"):
        print(f"batch_size={args.batch_size} n_steps={args.n_steps}")
    if args.fam == "training":
        print(f"task={args.task} device={args.device} pre_seq_len={args.pre_seq_len}")
    print("No benchmark was executed. Re-run with --execute only after approving network, model cache, runtime, and cleanup constraints.")


def main():
    args = normalize(parser().parse_args())
    if not args.execute:
        dry_run(args)
        return 0
    if args.fam == "inference":
        speed = run_processes(args, bench_inference_worker)
        print(f"Final result: speed={float(speed):.2f}")
    elif args.fam == "forward":
        speed = run_processes(args, bench_forward_worker)
        print(f"Final result: speed={float(speed):.2f}")
    else:
        fwd_speed, bwd_speed = run_processes(args, bench_training_worker)
        print(f"Final result: fwd_speed={float(fwd_speed):.2f} bwd_speed={float(bwd_speed):.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
