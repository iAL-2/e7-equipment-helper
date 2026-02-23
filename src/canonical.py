# src/canonical.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Dict, Any

import yaml


# ---------- Models ----------

@dataclass(frozen=True)
class StatLine:
    stat: str          # e.g., "atk_pct"
    value: float       # store numeric; caller decides int/float

@dataclass(frozen=True)
class CanonItem:
    schema_version: int
    id: Optional[str]
    slot: str
    set: str
    rarity: str
    ilevel: int        # use ilevel instead of "level"
    enhance: int
    main: StatLine
    subs: List[StatLine]
    locked: Optional[bool] = None
    equipped_by: Optional[str] = None


# ---------- Load YAML ----------

@dataclass(frozen=True)
class Vocab:
    schema_version: int
    slots: set[str]
    rarities: set[str]
    stats: set[str]
    sets: set[str]

@dataclass(frozen=True)
class Rules:
    schema_version: int
    left_side_fixed_mains: Dict[str, str]
    right_side_allowed_mains: Dict[str, set[str]]
    enhance_min: int
    enhance_max: int
    subs_max: int
    subs_unique: bool
    forbid_sub_equal_main: bool
    slot_unallowed_subs: Dict[str, set[str]]

def load_yaml(path: Path) -> Dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))
# path.read_text(encoding="utf-8")) is functionally the same as 
# with open(path, "r", encoding=utf-8") as f:
# yaml.safe_load() is required for a dict/list structure

def load_vocab(vocab_path: Path) -> Vocab:
    d = load_yaml(vocab_path)
    return Vocab(
        schema_version=int(d["schema_version"]),
        slots=set(d["slots"]),
        rarities=set(d["rarities"]),
        stats=set(d["stats"]),
        sets=set(d["sets"]),
    )

def load_rules(rules_path: Path) -> Rules:
    d = load_yaml(rules_path)

    cons = d.get("constraints", {})
    slot_unallowed = d.get("slot_unallowed_subs", {})  # mapping: slot -> [stats]

    return Rules(
        schema_version=int(d["schema_version"]),
        left_side_fixed_mains=dict(d["left_side_fixed_mains"]),
        right_side_allowed_mains={k: set(v) for k, v in d["right_side_allowed_mains"].items()},
        enhance_min=int(cons["enhance_min"]),
        enhance_max=int(cons["enhance_max"]),
        subs_max=int(cons["subs_max"]),
        subs_unique=bool(cons["subs_unique"]),
        forbid_sub_equal_main=bool(cons["forbid_sub_equal_main"]),
        slot_unallowed_subs={k: set(v) for k, v in slot_unallowed.items()},
    )


# ---------- Validation ----------

class ValidationError(ValueError):
    pass

def _require(cond: bool, msg: str) -> None:
    if not cond:
        raise ValidationError(msg)

def validate_canon_item(item: CanonItem, vocab: Vocab, rules: Rules) -> None:
    # Schema version sanity
    _require(item.schema_version == vocab.schema_version == rules.schema_version,
             f"schema_version mismatch: item={item.schema_version}, vocab={vocab.schema_version}, rules={rules.schema_version}")

    # Basic vocab membership
    _require(item.slot in vocab.slots, f"invalid slot: {item.slot}")
    _require(item.set in vocab.sets, f"invalid set: {item.set}")
    _require(item.rarity in vocab.rarities, f"invalid rarity: {item.rarity}")

    # Enhance bounds
    _require(rules.enhance_min <= item.enhance <= rules.enhance_max,
             f"enhance out of range: {item.enhance} (allowed {rules.enhance_min}..{rules.enhance_max})")

    # Stat keys exist
    _require(item.main.stat in vocab.stats, f"invalid main.stat: {item.main.stat}")
    for i, s in enumerate(item.subs):
        _require(s.stat in vocab.stats, f"invalid subs[{i}].stat: {s.stat}")

    # Main stat legality
    if item.slot in rules.left_side_fixed_mains:
        expected = rules.left_side_fixed_mains[item.slot]
        _require(item.main.stat == expected,
                 f"illegal main stat for {item.slot}: got {item.main.stat}, expected {expected}")
    else:
        allowed = rules.right_side_allowed_mains.get(item.slot)
        _require(allowed is not None, f"no right-side main rule for slot: {item.slot}")
        _require(item.main.stat in allowed,
                 f"illegal main stat for {item.slot}: {item.main.stat} not in {sorted(allowed)}")

    # Subs count
    _require(len(item.subs) <= rules.subs_max,
             f"too many substats: {len(item.subs)} (max {rules.subs_max})")

    # Subs uniqueness
    if rules.subs_unique:
        sub_keys = [s.stat for s in item.subs]
        _require(len(sub_keys) == len(set(sub_keys)),
                 f"duplicate substats: {sub_keys}")

    # Forbid sub == main
    if rules.forbid_sub_equal_main:
        _require(all(s.stat != item.main.stat for s in item.subs),
                 f"substat contains main stat: {item.main.stat}")

    # Slot-specific forbidden subs (weapon/armor rules, etc.)
    forbidden = rules.slot_unallowed_subs.get(item.slot, set())
    if forbidden:
        bad = [s.stat for s in item.subs if s.stat in forbidden]
        _require(not bad, f"illegal substats for slot {item.slot}: {bad}")

def parse_canon_item(d: Dict[str, Any]) -> CanonItem:
    # expects dict shaped like your canonitem.yaml/json
    main = StatLine(stat=str(d["main"]["stat"]), value=float(d["main"]["value"]))
    subs = [StatLine(stat=str(x["stat"]), value=float(x["value"])) for x in d.get("subs", [])]
    return CanonItem(
        schema_version=int(d["schema_version"]),
        id=(None if d.get("id") is None else str(d.get("id"))),
        slot=str(d["slot"]),
        set=str(d["set"]),
        rarity=str(d["rarity"]),
        ilevel=int(d["ilevel"]),
        enhance=int(d["enhance"]),
        main=main,
        subs=subs,
        locked=d.get("locked"),
        equipped_by=d.get("equipped_by"),
    )


# ---------- Quick local test runner ----------
if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    vocab = load_vocab(root / "data" / "vocab.yaml")
    rules = load_rules(root / "data" / "rules.yaml")

    sample = load_yaml(root / "data" / "canonitem.yaml")  # or wherever you store it
    item = parse_canon_item(sample)
    validate_canon_item(item, vocab, rules)
    print("OK: CanonItem validated")