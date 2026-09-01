from __future__ import annotations

def flatten(x):
    if isinstance(x, (list, tuple)):
        out=[]
        for v in x: out.extend(flatten(v))
        return out
    return [x]

def build_programmed_input(task_values, mask, program_values):
    mask_f=[int(v) for v in flatten(mask)]
    if not any(mask_f) or all(mask_f):
        raise ValueError('mask must contain both task and program positions')
    task=list(flatten(task_values)); prog=list(flatten(program_values))
    if len(task)!=sum(mask_f):
        raise ValueError('task_values length must equal number of mask ones')
    prog_needed=len(mask_f)-sum(mask_f)
    if len(prog)==1: prog=prog*prog_needed
    if len(prog)!=prog_needed:
        raise ValueError('program_values length must equal number of mask zeros or be scalar')
    ti=pi=0; y=[]; task_positions=[]; program_positions=[]
    for i,m in enumerate(mask_f):
        if m:
            y.append(task[ti]); task_positions.append(i); ti+=1
        else:
            y.append(prog[pi]); program_positions.append(i); pi+=1
    return {'programmed_input': y, 'metadata': {'task_positions': task_positions, 'program_positions': program_positions, 'task_preserved': [y[i] for i in task_positions]==task}}
