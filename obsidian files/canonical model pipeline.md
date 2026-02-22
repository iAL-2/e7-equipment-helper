
## 1) Core idea

A flowchart is just:

- a set of **binary predicates** (checks)
    
- a **routing mechanism** (what happens if true/false)
    
- a set of **actions** (STOP / CONTINUE / KEEP / TRASH / PIVOT)
    

So implement a generic rule engine that evaluates predicates against an `ItemState`.

## 2) Canonical `ItemState` (what rules read)

Minimal fields needed to replicate the typical gear flowchart:

- `tier` (i85, i88, etc.)
    
- `rarity` (heroic/epic)
    
- `slot`
    
- `set`
    
- `enhance` (+0/+3/+6/+9/+12/+15)
    
- `main_stat` (type, value, percent/flat)
    
- `subs`: list of `{stat, value, percent/flat}`
    
- derived features computed once per state:
    
    - `quality_total` (roll-equivalent sum or your “equip score”)
        
    - `has_sub(stat)`, `sub_value(stat)`
        
    - `hit_counts` (optional later; for now you can ignore if you’re matching the flowchart exactly)
        
    - `coherence_tags` (optional later)
        

This separation matters: the decision engine shouldn’t care how you got the state (OCR/manual/etc.).

## 3) Predicate functions (binary checks)

Implement a library of reusable checks. Examples:

- `is_rarity("Epic")`
    
- `is_set_in(["Speed", "Torrent"])`
    
- `is_slot("Boots")`
    
- `main_stat_is("Speed")`
    
- `has_sub("Speed")`
    
- `sub_at_least("Speed", 3)` (or roll-equivalent threshold)
    
- `quality_at_least(XX)` (your “equip score” gate)
    
- `enhance_at_least(9)`
    
- `subs_match_any_cluster(["DPS", "Bruiser"])` _(optional later)_
    

Each returns `true/false`. That’s the “binary constraints” you want.

## 4) Node graph (the flowchart as data)

Represent the flowchart as a directed graph of nodes:

- `CheckNode(predicate, if_true=next_id, if_false=next_id)`
    
- `ActionNode(action_type, payload)` (e.g., STOP, CONTINUE, KEEP_AS="speed_stick")
    

Evaluation = start at `root`, walk until action.

This exactly reproduces a flowchart and stays sane because it _is_ binary gating.

## 5) Profiles = different graphs (or same graph + different threshold tables)

You can implement profiles two ways:

**A) Separate graphs** (simplest to match “this is the community flowchart”)

- `profile: early_game`, `mid_game`, `late_game`
    
- heroic stricter version is literally a different graph or just different threshold constants.
    

**B) Same graph, different parameters**

- Predicates like `quality_at_least($Q_MIN[rarity][enhance])`
    
- Profile selects the threshold table.
    

This is usually the best compromise: the graph stays readable; behavior changes via tables.

## 6) “Expand from there” without exploding complexity

After the baseline flowchart works, expand in small, non-disruptive layers:

### Layer 1: Add “override” predicates (still binary)

Without going full multi-track, you can add a couple of high-signal overrides as extra branches:

- `is_premium_line_on_track()` (e.g., speed line meets breakpoint minimum)
    
- `is_concentration_exception()` (triple/quad/penta detection when you implement hit tracking)
    

These are still binary checks; they just add “escape hatches” before STOP nodes.

### Layer 2: Add limited pivoting as an action

Add an action node: `PIVOT_TO(["Bruiser", "Debuffer"])` that changes the active profile/cluster context and continues evaluation from another node.

Still a flowchart—just with a controlled “goto another subgraph.”

## 7) What’s trivial vs not

**Trivial engineering**

- Node graph execution
    
- Predicate library scaffolding
    
- Threshold tables
    
- Loading flowchart definitions from JSON/YAML
    

**Non-trivial (but still straightforward)**

- Deriving `quality_total` correctly (roll tables per tier/rarity)
    
- Hit-count inference across breakpoints (if you want concentration rules)
    
- Handling edge cases (3-start subs, modded lines, reforges)
    

But none of that forces a redesign of the flowchart engine.

## 8) Minimal implementation plan (tight)

1. Implement `ItemState` + derived `quality_total` (even if rough at first).
    
2. Implement flowchart engine (nodes + predicates + actions).
    
3. Encode the exact existing decision tree into a JSON graph.
    
4. Run it on manually entered test items and confirm it matches the expected roll/stop outputs.
    
5. Only then add concentration overrides / pivot actions.
    

This gives you the “binary constrained sanity” of the original flowchart, while keeping the structure expandable without rewriting logic.