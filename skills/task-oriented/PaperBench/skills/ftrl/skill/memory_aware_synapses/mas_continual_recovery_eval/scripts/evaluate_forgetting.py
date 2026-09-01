def compute_forgetting(before_score, after_score): return before_score-after_score
def summarize_recovery(before, after_finetune, after_mas):
    ff=compute_forgetting(before, after_finetune); fm=compute_forgetting(before, after_mas)
    return {'task1_before':before,'task1_after_finetune':after_finetune,'task1_after_mas':after_mas,'forgetting_finetune':ff,'forgetting_mas':fm,'forgetting_reduction':ff-fm,'mas_reduces_forgetting':fm<ff}
