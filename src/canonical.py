# src/canonical.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

import yaml


# ---------- Models (Canonical) ----------

@dataclass(frozen=True)
class StatLine:
    stat: str          # e.g., "atk_pct"
    value: float       # numeric

@dataclass(frozen=True)
class CanonItem:
    schema_version: int
    id: Optional[str]
    slot: str
    set: str
    rarity: str
    ilevel: int
    enhance: int
    main: StatLine
    subs: List[StatLine]
    locked: Optional[bool] = None
    equipped_by: Optional[str] = None


# ---------- Models (Parsed / imperfect) ----------

@dataclass(frozen=True)
class ParsedStatLine:
    stat: Optional[str]
    value: Optional[float]
    confidence: float = 1.0  # 0..1

@dataclass(frozen=True)
class ParsedItem:
    schema_version: int = 1
    id: Optional[str] = None
    slot: Optional[str] = None
    set: Optional[str] = None
    rarity: Optional[str] = None
    ilevel: Optional[int] = None
    enhance: Optional[int] = None
    main: Optional[ParsedStatLine] = None
    subs: List[ParsedStatLine] = None
    locked: Optional[bool] = None
    equipped_by: Optional[str] = None

    def __post_init__(self):
        # dataclasses don't allow easy default mutable list, so enforce here
        if self.subs is None:
            object.__setattr__(self, "subs", [])


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
    # Reads YAML file text and parses into Python dict/list primitives
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise TypeError(f"Expected mapping at top of {path}, got {type(data).__name__}")
    return data

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
    """
    Raises ValidationError on first failure.
    """
    errs = validate_canon_item_all(item, vocab, rules)
    if errs:
        raise ValidationError("; ".join(errs))

def validate_canon_item_all(item: CanonItem, vocab: Vocab, rules: Rules) -> List[str]:
    """
    Returns *all* validation errors (empty list means OK).
    """
    errors: List[str] = []

    def add(cond: bool, msg: str) -> None:
        if not cond:
            errors.append(msg)

    # Schema version sanity
    add(item.schema_version == vocab.schema_version == rules.schema_version,
        f"schema_version mismatch: item={item.schema_version}, vocab={vocab.schema_version}, rules={rules.schema_version}")

    # Basic vocab membership
    add(item.slot in vocab.slots, f"invalid slot: {item.slot}")
    add(item.set in vocab.sets, f"invalid set: {item.set}")
    add(item.rarity in vocab.rarities, f"invalid rarity: {item.rarity}")

    # Enhance bounds
    add(rules.enhance_min <= item.enhance <= rules.enhance_max,
        f"enhance out of range: {item.enhance} (allowed {rules.enhance_min}..{rules.enhance_max})")

    # Stat keys exist
    add(item.main.stat in vocab.stats, f"invalid main.stat: {item.main.stat}")
    for i, s in enumerate(item.subs):
        add(s.stat in vocab.stats, f"invalid subs[{i}].stat: {s.stat}")

    # Main stat legality
    if item.slot in rules.left_side_fixed_mains:
        expected = rules.left_side_fixed_mains[item.slot]
        add(item.main.stat == expected,
            f"illegal main stat for {item.slot}: got {item.main.stat}, expected {expected}")
    else:
        allowed = rules.right_side_allowed_mains.get(item.slot)
        add(allowed is not None, f"no right-side main rule for slot: {item.slot}")
        if allowed is not None:
            add(item.main.stat in allowed,
                f"illegal main stat for {item.slot}: {item.main.stat} not in {sorted(allowed)}")

    # Subs count
    add(len(item.subs) <= rules.subs_max,
        f"too many substats: {len(item.subs)} (max {rules.subs_max})")

    # Subs uniqueness
    if rules.subs_unique:
        sub_keys = [s.stat for s in item.subs]
        add(len(sub_keys) == len(set(sub_keys)), f"duplicate substats: {sub_keys}")

    # Forbid sub == main
    if rules.forbid_sub_equal_main:
        add(all(s.stat != item.main.stat for s in item.subs),
            f"substat contains main stat: {item.main.stat}")

    # Slot-specific forbidden subs
    forbidden = rules.slot_unallowed_subs.get(item.slot, set())
    if forbidden:
        bad = [s.stat for s in item.subs if s.stat in forbidden]
        add(not bad, f"illegal substats for slot {item.slot}: {bad}")

    return errors


# ---------- Parsing CanonItem from YAML/JSON dict ----------

def parse_canon_item(d: Dict[str, Any]) -> CanonItem:
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

def parse_parsed_item(d: Dict[str, Any]) -> ParsedItem:
    main = None
    if d.get("main") is not None:
        main = ParsedStatLine(
            stat=d["main"].get("stat"),
            value=(None if d["main"].get("value") is None else float(d["main"]["value"])),
            confidence=float(d["main"].get("confidence", 1.0)),
        )

    subs: List[ParsedStatLine] = []
    for x in d.get("subs", []) or []:
        subs.append(ParsedStatLine(
            stat=x.get("stat"),
            value=(None if x.get("value") is None else float(x["value"])),
            confidence=float(x.get("confidence", 1.0)),
        ))

    return ParsedItem(
        schema_version=int(d.get("schema_version", 1)),
        id=(None if d.get("id") is None else str(d.get("id"))),
        slot=d.get("slot"),
        set=d.get("set"),
        rarity=d.get("rarity"),
        ilevel=(None if d.get("ilevel") is None else int(d["ilevel"])),
        enhance=(None if d.get("enhance") is None else int(d["enhance"])),
        main=main,
        subs=subs,
        locked=d.get("locked"),
        equipped_by=d.get("equipped_by"),
    )

# ---------- Normalization + Canonicalization ----------

# --- replace your old STAT_ALIASES + norm_token with this ---

STAT_ALIASES: Dict[str, str] = {
    "atk%": "atk_pct",
    "hp%": "hp_pct",
    "def%": "def_pct",
    "crit": "cr",
    "crit_rate": "cr",
    "critdmg": "cd",
    "crit_dmg": "cd",
    "effectiveness": "eff",
    "effect_resist": "res",
    "effect resist": "res",
    "speed": "spd",   # <-- keep this ONLY for stat labels, not sets
}

SET_ALIASES: Dict[str, str] = {
    "speed_set": "speed",
    "speedset": "speed",
    # (optional) add more display-name variants later
}

def _basic_norm(x: Optional[str]) -> Optional[str]:
    if x is None:
        return None
    return x.strip().lower().replace(" ", "_")

def norm_stat(x: Optional[str]) -> Optional[str]:
    s = _basic_norm(x)
    if s is None:
        return None
    return STAT_ALIASES.get(s, s)

def norm_set(x: Optional[str]) -> Optional[str]:
    s = _basic_norm(x)
    if s is None:
        return None
    return SET_ALIASES.get(s, s)

def norm_enum(x: Optional[str]) -> Optional[str]:
    # for slot/rarity where you mostly just want lowercase/underscore
    return _basic_norm(x)

def canonicalize(parsed: ParsedItem, vocab: Vocab, rules: Rules) -> Tuple[Optional[CanonItem], List[str]]:
    """
    Best-effort: if required fields are missing or invalid, returns (None, errors).
    No OCR/classifier logic here yet—just normalization + strict validation.
    """
    errors: List[str] = []

    # Required scalar fields (domain-aware normalization)
    slot = norm_enum(parsed.slot)
    set_name = norm_set(parsed.set)
    rarity = norm_enum(parsed.rarity)

    if slot is None: errors.append("missing slot")
    if set_name is None: errors.append("missing set")
    if rarity is None: errors.append("missing rarity")
    if parsed.ilevel is None: errors.append("missing ilevel")
    if parsed.enhance is None: errors.append("missing enhance")
    if parsed.main is None: errors.append("missing main")

    if errors:
        return None, errors

    # Main + subs (stat-aware normalization)
    main_stat = norm_stat(parsed.main.stat)
    main_val = parsed.main.value
    if main_stat is None: errors.append("missing main.stat")
    if main_val is None: errors.append("missing main.value")

    subs: List[StatLine] = []
    for i, s in enumerate(parsed.subs or []):
        st = norm_stat(s.stat)
        if st is None or s.value is None:
            errors.append(f"missing subs[{i}] fields")
            continue
        subs.append(StatLine(stat=st, value=float(s.value)))

    if errors:
        return None, errors

    item = CanonItem(
        schema_version=parsed.schema_version,
        id=parsed.id,
        slot=slot,
        set=set_name,
        rarity=rarity,
        ilevel=int(parsed.ilevel),
        enhance=int(parsed.enhance),
        main=StatLine(stat=main_stat, value=float(main_val)),
        subs=subs,
        locked=parsed.locked,
        equipped_by=parsed.equipped_by,
    )

    v_errs = validate_canon_item_all(item, vocab, rules)
    if v_errs:
        return None, v_errs
    return item, []


# ---------- Quick local test runner ----------
if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    vocab = load_vocab(root / "data" / "vocab.yaml")
    rules = load_rules(root / "data" / "rules.yaml")

    # Validate canonical sample
    sample = load_yaml(root / "data" / "canonitem.yaml")
    item = parse_canon_item(sample)
    validate_canon_item(item, vocab, rules)
    print("OK: CanonItem validated")