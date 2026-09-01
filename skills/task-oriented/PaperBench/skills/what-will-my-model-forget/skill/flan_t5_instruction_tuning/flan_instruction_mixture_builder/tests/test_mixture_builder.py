import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from mixture_builder import build_mixture

def test_filters_heldout_and_keeps_cot():
    tasks=[{"source":"muffin","task_id":"mmlu_math","benchmark":"MMLU","examples":[]},{"source":"niv2","task_id":"sentiment","benchmark":"sst","examples":[]},{"source":"cot","task_id":"gsm_style","benchmark":"reasoning","cot":True,"examples":[]}]
    result=build_mixture(tasks,["mmlu"])
    assert [task["task_id"] for task in result["mixture"]] == ["sentiment", "gsm_style"]
    assert result["audit"]["cot_task_count"] == 1
    assert result["audit"]["excluded"][0]["reason"] == "heldout_overlap"
if __name__ == "__main__": test_filters_heldout_and_keeps_cot()
