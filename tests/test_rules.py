from pathlib import Path
from src.canonical import load_vocab, load_rules, CanonItem, StatLine, validate_canon_item_all

def _load():
    root = Path(__file__).resolve().parents[1]
    vocab = load_vocab(root / "data" / "vocab.yaml")
    rules = load_rules(root / "data" / "rules.yaml")
    return vocab, rules

def test_left_side_mains_fixed():
    vocab, rules = _load()
    item = CanonItem(
        schema_version=1, id=None, slot="weapon", set="speed", rarity="epic",
        ilevel=85, enhance=0, main=StatLine("hp", 100), subs=[]
    )
    errs = validate_canon_item_all(item, vocab, rules)
    assert any("illegal main stat for weapon" in e for e in errs)

def test_subs_unique_enforced():
    vocab, rules = _load()
    item = CanonItem(
        schema_version=1, id=None, slot="boots", set="speed", rarity="epic",
        ilevel=85, enhance=0, main=StatLine("spd", 40),
        subs=[StatLine("cr", 5), StatLine("cr", 7)]
    )
    errs = validate_canon_item_all(item, vocab, rules)
    assert any("duplicate substats" in e for e in errs)

def test_main_cannot_be_sub():
    vocab, rules = _load()
    item = CanonItem(
        schema_version=1, id=None, slot="boots", set="speed", rarity="epic",
        ilevel=85, enhance=0, main=StatLine("spd", 40),
        subs=[StatLine("spd", 5)]
    )
    errs = validate_canon_item_all(item, vocab, rules)
    assert any("substat contains main stat" in e for e in errs)