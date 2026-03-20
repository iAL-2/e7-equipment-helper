**Entry:**

- `python -m src.upstream`
    

**Flow:**

- `demo()` (src/upstream.py)
    
    - capture screenshot (adb)
        
    - load image `_load_rgb`
        
    - profile detect `detect_profile`
        
    - choose region map (`REGIONS_BAG/DETAIL`)
        
    - dump crops (optional)
        
    - `ClosedSetRecognizer.create(root)`
        
    - `run_once_or_raise(...)`
        

**Core seam:**

- `ClosedSetRecognizer.recognize(cap)` does all pixel→tokens work
    
- `validate_canon_item(item, vocab, rules)` checks constraints