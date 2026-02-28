from src.canonical import norm_stat, norm_set, norm_enum

def test_norm_stat_speed_becomes_spd():
    assert norm_stat("Speed") == "spd"

def test_norm_set_speed_stays_speed():
    assert norm_set("Speed") == "speed"

def test_norm_enum_boots():
    assert norm_enum("Boots") == "boots"