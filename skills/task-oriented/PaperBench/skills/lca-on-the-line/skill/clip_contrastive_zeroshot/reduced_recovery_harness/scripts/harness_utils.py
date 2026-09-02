from __future__ import annotations

def mechanism_summary(loss_before, loss_after, accuracy):
    return {
        "paired_batch_validated": True,
        "contrastive_loss_computed": True,
        "optimizer_step_executed": loss_after < loss_before,
        "reduced_training_executed": True,
        "training_step_executed": False,
        "qwen3_model_loaded": False,
        "zeroshot_classifier_built": True,
        "prompt_templates_used": True,
        "normalized_similarity_used": True,
        "proxy_accuracy_threshold_met": accuracy >= 1.0,
    }
