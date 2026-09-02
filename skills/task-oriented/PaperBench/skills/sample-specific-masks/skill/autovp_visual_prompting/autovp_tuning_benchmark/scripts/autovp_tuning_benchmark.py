def select_best(candidates):
    return sorted(candidates, key=lambda c:(-c['score'], str(c.get('name',''))))[0]

def summarize(dataset, metric, paper_value, selected, proxy=True):
    return {"dataset":dataset,"metric":metric,"paper_value":paper_value,"selected_config":selected,"proxy":proxy}
