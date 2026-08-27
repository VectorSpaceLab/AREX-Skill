# Connectivity and plasticity patterns

## Conditional and probabilistic recurrent graphs

For a recurrent population, make self-connection policy explicit:

```python
S = Synapses(G, G, "w : 1", on_pre="v_post += w")
S.connect(condition="i != j", p=0.2)
```

`condition` selects candidate pairs; `p` then samples each accepted pair.
Expressions may use pre/post state, but a pair-dependent expression can examine
all candidate pairs. For sparse, structured patterns use a generator or edge
arrays instead. To test a probabilistic graph, seed randomness, assert no
forbidden edges, and check count within an intentionally broad statistical
bound rather than demanding an exact count unless the fixture uses `p=0` or
`p=1`.

For parallel synapses:

```python
S = Synapses(G, G, "w : 1", on_pre="v_post += w",
             multisynaptic_index="k")
S.connect(condition="i != j", n=2)
S.delay = "(k + 1) * ms"
```

Third-axis indexing (`S.w[:, :, 1]`) is only available when the index variable
was requested. A synaptic subgroup created before later `connect` calls is
invalidated; create it after graph construction.

## STDP event ordering

A pre pathway normally runs before a post pathway at the same simulation time.
Named pathways can separate transmission and plasticity:

```python
on_pre={
  "transmit": "g_post += w",
  "plasticity": "w = clip(w + Apost, 0, wmax); Apre += dApre",
}
```

Set `.order` explicitly if same-delay pathway order is part of the model; do
not rely on dictionary or incidental alphabetical ordering. Delays belong to
the individual pathway (`S.transmit.delay`, `S.plasticity.delay`). Use a
separate post pathway for post-triggered updates.

Event-driven eligibility traces should be independent one-dimensional linear
ODEs. Brian analytically advances them from `lastupdate` whenever either
associated pathway fires. Do not make an event-driven equation depend on a
clock-driven or summed differential equation. A failing construction is a
useful diagnostic: classify it as a dependency error and decide whether the
quantity truly needs continuous integration.

## Summed variables

A summed variable is declared in the synapse model with a target suffix:

```python
S = Synapses(pre, post, "g : siemens\n gtot_post = g : siemens (summed)")
```

`post` must declare a parameter `gtot : siemens`. Brian updates `gtot` with the
sum of `g` over incoming synapses. Units must match exactly, and a target
parameter may not be the destination of two summed updaters. Use `gtot1` and
`gtot2` on the target, then define `gtot = gtot1 + gtot2`, for multiple sources.

## Explicit event-time update

For continuously interacting models, keep the continuously varying state in
one of the connected groups when it is shared by all outgoing synapses, or
keep a per-synapse differential variable in `Synapses` when time constants or
state differ per edge. A common continuous coupling pattern is a summed
expression such as `g_post = w * s_pre : 1 (summed)`, where `s_pre` is a
source-group state and `g_post` is a predeclared target parameter. This is
updated on the synaptic clock each step and does not require spikes or an
`on_pre` pathway. Mark genuinely continuous synaptic differential equations
`(clock-driven)`; use `(event-driven)` only for compatible event-time traces.
This route does not claim that a spike-triggered integrate-and-fire synapse
reproduces a continuously coupled conductance model.

For non-linear short-term dynamics that are only needed at events, declare a
`lastupdate : second` parameter and update with elapsed time in `on_pre`:

```python
on_pre="""
  x = 1 + (x - 1) * exp(-(t - lastupdate) / tau)
  lastupdate = t
  v_post += w * x
"""
```

This is more error-prone than automatic event-driven equations: initialize the
state, update every pathway that consumes it, and test repeated events with
known separations. Never confuse `t` with a Python wall-clock value.

## Evidence boundary

These rules are distilled from the Brian2 2.9.0 synapse documentation,
`Synapses` pathway/indexing and dependency implementation, the synapse tests,
and the STDP example. General equation syntax and unit errors route to
`units-and-equations`; monitor data route to `recording`; standalone scheduling
and operation restrictions route to `code-generation`.
