# src/regions_config.py
ANCHOR_RECT = (10, 10, 450, 75)

REGIONS_BAG = {
    "slot": (1440, 256, 200, 75),
    "set": (1312, 824, 529, 49),
    "rarity": (1446, 256, 176, 64),
    "ilevel": (1332, 271, 34, 25),
    "enhance": (1390, 249, 62, 47),
    "main_stat": (1314, 487, 320, 57),
    "main_value": (1740, 488, 97, 52),
    "sub1_stat": (1321, 557, 250, 35),
    "sub1_value": (1767, 559, 81, 35),
    "sub2_stat": (1323, 589, 250, 35),
    "sub2_value": (1763, 592, 80, 35),
    "sub3_stat": (1322, 625, 250, 35),
    "sub3_value": (1767, 625, 80, 35),
    "sub4_stat": (1324, 656, 250, 35),
    "sub4_value": (1750, 657, 80, 35),
    "otherworldly": (1446, 256, 176, 64),
}

REGIONS_DETAIL = {
    "slot": (206, 144, 251, 60),
    "set": (52, 665, 340, 62),
    "rarity": (207, 145, 248, 58),
    "ilevel": (62, 144, 40, 32),
    "enhance": (150, 122, 50, 45),
    "main_stat": (57, 312, 489, 67),
    "main_value": (353, 315, 184, 63),
    "sub1_stat": (59, 410, 119, 38),
    "sub1_value": (484, 414, 58, 33),
    "sub2_stat": (62, 448, 114, 40),
    "sub2_value": (486, 453, 55, 30),
    "sub3_stat": (60, 491, 256, 33),
    "sub3_value": (484, 487, 58, 38),
    "sub4_stat": (63, 526, 299, 39),
    "sub4_value": (483, 527, 64, 38),
    "otherworldly": (207, 145, 248, 58),
}


# bulk
BULK_COLS = 4
BULK_ROWS = 4

BULK_GRID_ORIGIN = (23, 190)
BULK_CARD_SIZE = (360, 190)
BULK_COL_STEP = 366
BULK_ROW_STEP = 194


def bulk_item_rect(index: int) -> tuple[int, int, int, int]:
    if not 0 <= index < BULK_COLS * BULK_ROWS:
        raise IndexError(f"bulk item index out of range: {index}")

    row = index // BULK_COLS
    col = index % BULK_COLS

    x0, y0 = BULK_GRID_ORIGIN
    w, h = BULK_CARD_SIZE

    return (
        x0 + col * BULK_COL_STEP,
        y0 + row * BULK_ROW_STEP,
        w,
        h,
    )


def bulk_item_rects() -> dict[str, tuple[int, int, int, int]]:
    return {
        f"item_{index:02d}": bulk_item_rect(index)
        for index in range(BULK_COLS * BULK_ROWS)
    }

REGIONS_BULK_ITEM_REL = {
    #"slot": (0, 0, 0, 0),
    "set": (93, 92, 45, 47),
    #"rarity": (0, 0, 0, 0),
    "enhance": (95, 7, 45, 32),
    "main_stat": (144, 16, 32, 31),
    "main_value": (179, 16, 70, 31),
    "sub1_stat": (144, 55, 30, 31),
    "sub1_value": (175, 55, 70, 31),
    "sub2_stat": (144, 86, 30, 31),
    "sub2_value": (175, 86, 70, 31),
    "sub3_stat": (144, 117, 30, 31),
    "sub3_value": (175, 117, 70, 31),
    "sub4_stat": (144, 148, 30, 31),
    "sub4_value": (175, 148, 70, 31),
    #"otherworldly": (0, 0, 0, 0),
}

def bulk_item_regions(index: int) -> dict[str, tuple[int, int, int, int]]:
    item_x, item_y, _, _ = bulk_item_rect(index)

    return {
        name: (item_x + rel_x, item_y + rel_y, w, h)
        for name, (rel_x, rel_y, w, h) in REGIONS_BULK_ITEM_REL.items()
    }