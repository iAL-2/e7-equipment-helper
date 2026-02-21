Represent every piece as a normalized object: 

- `slot` (weapon/helm/armor/neck/ring/boots)
    
- `set`
    
- `rarity`, `level_tier` (i70/i85/i88 etc)
    
- `enhance_level` (+0…+15)
    
- `main_stat` (type, value, is_percent)
    
- `substats[]` each with:
    
    - `stat_type` (SPD, CR, CD, ATK%, ATK flat, HP%, HP flat, DEF%, DEF flat, EFF, RES)
        
    - `value`
        
    - `is_percent`
        
    - `is_modified` + `mod_delta` (optional)
        
- `reforged` flag + any reforged deltas (optional)
    

Once you have this, OCR becomes “populate fields,” and everything else is deterministic.