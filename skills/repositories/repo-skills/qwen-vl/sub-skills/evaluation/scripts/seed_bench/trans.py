#!/usr/bin/env python3
"""Convert SEED-Bench questions into Qwen-VL JSONL inputs."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

import av
import numpy as np
import torch
from PIL import Image
from tqdm import tqdm

try:
    from decord import VideoReader, cpu
except Exception:  # optional dependency for video decoding
    VideoReader = None
    cpu = None


def is_integer_string(value: str) -> bool:
    try:
        int(value)
        return True
    except ValueError:
        return False


def filter_questions(data: list[dict[str, Any]], task: str = "all") -> list[dict[str, Any]]:
    if task == "image":
        return [q for q in data if 1 <= q["question_type_id"] <= 9]
    if task == "video":
        return [q for q in data if 10 <= q["question_type_id"] <= 12]
    if task == "all":
        return data
    if is_integer_string(task):
        return [q for q in data if q["question_type_id"] == int(task)]
    raise ValueError(f"Invalid task: {task}")


def get_index(num_frames: int, num_segments: int) -> np.ndarray:
    if num_segments > num_frames:
        return np.array([idx for idx in range(num_frames)])
    seg_size = float(num_frames - 1) / num_segments
    start = int(seg_size / 2)
    return np.array([start + int(np.round(seg_size * idx)) for idx in range(num_segments)])


def load_image_questions(questions: list[dict[str, Any]], cc3m_dir: Path, output_dir: Path) -> Path:
    output_path = output_dir / "image_input.jsonl"
    with output_path.open("w", encoding="utf-8") as fout:
        for qa_item in tqdm(filter_questions(questions, "image")):
            data_path = str(cc3m_dir / qa_item["data_id"])
            choices = [qa_item[f"choice_{letter}"] for letter in "abcd"]
            choice_txt = "\n".join(f"{chr(i + 65)}. {choice}" for i, choice in enumerate(choices))
            prompt = f"<img>{data_path}</img>\nQuestion: {qa_item['question']}\nOptions: {choice_txt}\nAnswer:"
            print(json.dumps({
                "question_id": qa_item["question_id"],
                "prompt": prompt,
                "answer": qa_item["answer"],
            }), file=fout)
    return output_path


def decode_video_with_av(data_path: Path, n_frames: int, start: float, end: float, use_segment: bool) -> np.ndarray:
    reader = av.open(str(data_path))
    frames = [torch.from_numpy(frame.to_rgb().to_ndarray()) for frame in reader.decode(video=0)]
    video_len = len(frames)
    start_frame = int(start) if use_segment else 0
    end_frame = min(int(end), video_len) if use_segment else video_len
    offset = get_index(max(end_frame - start_frame, 1), n_frames)
    frame_indices = offset + start_frame
    images = torch.stack([frames[idx] for idx in frame_indices]).numpy()
    return images


def decode_video_with_decord(data_path: Path, n_frames: int, start: float, end: float, use_segment: bool) -> np.ndarray:
    if VideoReader is None or cpu is None:
        raise RuntimeError("Decord is not installed; install decord or use --video-decoder av/--skip-video")
    vr = VideoReader(str(data_path), num_threads=1, ctx=cpu(0))
    video_len = len(vr)
    fps = vr.get_avg_fps()
    if use_segment:
        start_frame = int(min(max(start * fps, 0), video_len - 1))
        end_frame = int(min(max(end * fps, 0), video_len - 1))
        tot_frames = max(int(end_frame - start_frame), 1)
        offset = get_index(tot_frames, n_frames)
        frame_indices = offset + start_frame
    else:
        frame_indices = get_index(video_len - 1, n_frames)
    vr.seek(0)
    return vr.get_batch(frame_indices).asnumpy()


def load_video_questions(
    questions: list[dict[str, Any]],
    cc3m_dir: Path,
    dimension10_dir: Path,
    dimension11_dir: Path,
    dimension12_dir: Path,
    output_dir: Path,
    n_frames: int,
    video_decoder: str,
) -> Path:
    output_images_dir = output_dir / f"video_imgs_{n_frames}"
    output_images_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"video_input_{n_frames}.jsonl"

    with output_path.open("w", encoding="utf-8") as fout:
        for qa_item in tqdm(filter_questions(questions, "video")):
            if qa_item["question_type_id"] == 12:
                data_path = dimension12_dir / qa_item["data_id"]
            elif qa_item["question_type_id"] == 11:
                data_path = dimension11_dir / Path(qa_item["data_id"]).name
            elif qa_item["question_type_id"] == 10:
                data_path = dimension10_dir / qa_item["data_id"]
            else:
                raise AssertionError(str(qa_item))

            use_pyav = False
            if "segment" in qa_item:
                segment = qa_item["segment"]
                if isinstance(segment[0], int):
                    use_pyav = True
                start, end = segment[0], segment[1]
            else:
                start = 0.0
                end = 0.0

            if use_pyav or video_decoder == "av":
                images = decode_video_with_av(data_path, n_frames, start, end, use_pyav)
            elif video_decoder == "decord":
                images = decode_video_with_decord(data_path, n_frames, start, end, use_pyav)
            else:
                raise RuntimeError(f"Unsupported video decoder: {video_decoder}")

            prompt = ""
            for i in range(images.shape[0]):
                frame = Image.fromarray(images[i])
                img_path = output_images_dir / f"{qa_item['question_id']}_{i}.jpg"
                frame.save(img_path)
                prompt += f"<img>{img_path}</img>\n"

            choices = [qa_item[f"choice_{letter}"] for letter in "abcd"]
            choice_txt = "\n".join(f"{chr(i + 65)}. {choice}" for i, choice in enumerate(choices))
            prompt += f"Question: {qa_item['question']}\nOptions: {choice_txt}\nAnswer:"
            print(json.dumps({
                "question_id": qa_item["question_id"],
                "prompt": prompt,
                "answer": qa_item["answer"],
            }), file=fout)
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed-bench-json", default="SEED-Bench.json", help="Path to SEED-Bench question JSON")
    parser.add_argument("--cc3m-dir", required=True, help="Root directory for dimensions 1-9 images")
    parser.add_argument("--dimension10-dir", required=True, help="Root directory for dimension 10 videos")
    parser.add_argument("--dimension11-dir", required=True, help="Root directory for dimension 11 videos")
    parser.add_argument("--dimension12-dir", required=True, help="Root directory for dimension 12 videos")
    parser.add_argument("--output-dir", default=".", help="Directory where JSONL outputs and extracted frames are written")
    parser.add_argument("--n-frames", type=int, default=8, help="Number of frames to sample for video questions")
    parser.add_argument("--video-decoder", choices=["av", "decord"], default="av", help="Decoder for video questions")
    parser.add_argument("--skip-video", action="store_true", help="Only generate image_input.jsonl and skip video prompts")
    args = parser.parse_args()

    input_path = Path(args.seed_bench_json)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    qa_anno = json.loads(input_path.read_text(encoding="utf-8"))["questions"]
    cc3m_dir = Path(args.cc3m_dir)
    dimension10_dir = Path(args.dimension10_dir)
    dimension11_dir = Path(args.dimension11_dir)
    dimension12_dir = Path(args.dimension12_dir)

    image_out = load_image_questions(qa_anno, cc3m_dir, output_dir)
    print(f"Wrote {image_out}")

    if not args.skip_video:
        video_out = load_video_questions(
            qa_anno,
            cc3m_dir,
            dimension10_dir,
            dimension11_dir,
            dimension12_dir,
            output_dir,
            args.n_frames,
            args.video_decoder,
        )
        print(f"Wrote {video_out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
