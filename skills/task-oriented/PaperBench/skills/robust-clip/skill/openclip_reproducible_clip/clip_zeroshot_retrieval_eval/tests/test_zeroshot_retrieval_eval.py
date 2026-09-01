from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from zeroshot_retrieval_eval import evaluate_clip_embeddings

images = [[1, 0], [0, 1]]
classes = [[1, 0], [0, 1]]
texts = [[0.9, 0.1], [0.1, 0.9]]
result = evaluate_clip_embeddings(images, classes, [0, 1], texts, (1, 2))
assert result["top1_accuracy"] == 100.0
assert result["retrieval"]["image_to_text_recall_at_1"] == 100.0
assert result["image_to_text_rankings"] == [[0, 1], [1, 0]]
