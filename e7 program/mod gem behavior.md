1. no difference between 85/88
2. will never roll into flat stats since it is worse
3. crit, crit damage, and speed, should be the only 3 outliers


ilvl85, 1-2, ilvl90, 3-4
crit chance
1. at +0, rolls 2-4%
2. at +1, rolls 3-6%
3. at +0, 3-5
4. at +1, 5-8

crit damage
1. at +0, rolls 4-7%
2. at +1, rolls 6-9%
3. at +0, 5-8
4. at +1, 8-11

speed
1. at +0, 2-4
2. at +1, rolls 3-5
3. at +0, 2-4
4. at +1, 4-6

all other % stats
1. at +0, 4-8%
2. at +1, 7-11%
3. at +0, 5-9
4. at +1, 10-14

canonical natural max rolls: ilvl 85
speed = 2-4
crit chance = 3-5
crit damage = 4-7
all other stats = 4-8

ilvl 90 would be +1 to both min and max rolls compared to ilvl85. speed is an exception but for simplicity use the same rule.

## Canonical natural per-roll max (given)

**ilvl85 per-roll max**

- Speed 4
    
- Crit% 5
    
- CritDmg% 7
    
- Other% 8
    

**ilvl90 per-roll max** (your simplified rule: +1 to min/max, apply to speed too)

- Speed 5
    
- Crit% 6
    
- CritDmg% 8
    
- Other% 9
    

So:

- `NatMax_total(+0) = 1× per_roll_max`
    
- `NatMax_total(+1) = 2× per_roll_max`
    

---

## ilvl85/88 mod max vs ilvl85 natural (per-roll model)

### +0 line (compare to 1×)

|Stat|ModMax|NatMax_total|Value retained|
|---|--:|--:|--:|
|Speed|4|4|100.00%|
|Crit%|4|5|80.00%|
|CritDmg%|7|7|100.00%|
|Other%|8|8|100.00%|

### +1 line (compare to 2×)

|Stat|ModMax|NatMax_total|Value retained|
|---|--:|--:|--:|
|Speed|5|8|62.50%|
|Crit%|6|10|60.00%|
|CritDmg%|9|14|64.29%|
|Other%|11|16|68.75%|

---

## ilvl90 mod max vs ilvl90 natural (per-roll model)

### +0 line (compare to 1×)

|Stat|ModMax|NatMax_total|Value retained|
|---|--:|--:|--:|
|Speed|4|5|80.00%|
|Crit%|5|6|83.33%|
|CritDmg%|8|8|100.00%|
|Other%|9|9|100.00%|

### +1 line (compare to 2×)

|Stat|ModMax|NatMax_total|Value retained|
|---|--:|--:|--:|
|Speed|6|10|60.00%|
|Crit%|8|12|66.67%|
|CritDmg%|11|16|68.75%|
|Other%|14|18|77.78%|

---

### What this comparison is actually measuring

This measures: **“If a stat line already received 0 or 1 natural rolls, how much of the _maximum possible natural invested value_ can a perfect (max-rolled) mod gem recreate?”**

Under your data:

- **0-roll lines**: mod max typically reaches **100%** of a single-roll max (except Crit% and ilvl90 Speed under your simplified rule).
    
- **1-roll lines**: mod max recreates only about **60–78%** of the theoretical “two-roll max” value (depending on stat and ilvl bucket).