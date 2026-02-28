# tests/test_canonical.py
from pathlib import Path
import pytest

from src.canonical import (
    load_vocab, load_rules, load_yaml, parse_canon_item,
    validate_canon_item_all, ParsedItem, ParsedStatLine, canonicalize
)

def _load():
    root = Path(__file__).resolve().parents[1]
    vocab = load_vocab(root / "data" / "vocab.yaml")
    rules = load_rules(root / "data" / "rules.yaml")
    return root, vocab, rules

def test_sample_canonitem_validates():
    root, vocab, rules = _load()
    d = load_yaml(root / "data" / "canonitem.yaml")
    item = parse_canon_item(d)
    errs = validate_canon_item_all(item, vocab, rules)
    assert errs == []

def test_weapon_cannot_have_def_subs():
    _, vocab, rules = _load()
    # weapon must have main atk
    from src.canonical import CanonItem, StatLine
    item = CanonItem(
        schema_version=1,
        id=None,
        slot="weapon",
        set="speed",
        rarity="epic",
        ilevel=85,
        enhance=0,
        main=StatLine("atk", 500),
        subs=[StatLine("def", 20)],  # illegal by your rules
    )
    errs = validate_canon_item_all(item, vocab, rules)
    assert any("illegal substats for slot weapon" in e for e in errs)

def test_canonicalize_normalizes_tokens():
    _, vocab, rules = _load()
    parsed = ParsedItem(
        slot="Boots",
        set="Speed",
        rarity="Epic",
        ilevel=85,
        enhance=15,
        main=ParsedStatLine(stat="Speed", value=45, confidence=0.9),
        subs=[
            ParsedStatLine(stat="Crit", value=12, confidence=0.9),
            ParsedStatLine(stat="atk%", value=8, confidence=0.9),
        ],
    )
    item, errs = canonicalize(parsed, vocab, rules)
    assert errs == []
    assert item is not None
    assert item.slot == "boots"
    assert item.set == "speed"
    assert item.main.stat == "spd"
    assert item.subs[0].stat == "cr"
    assert item.subs[1].stat == "atk_pct"