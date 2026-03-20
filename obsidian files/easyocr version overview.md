````markdown
# e7-equipment-helper

Pipeline-first toolchain for extracting Epic Seven gear data from screenshots/emulator capture, normalizing it into a canonical schema, and (eventually) scoring/using it downstream.

This README documents the **current** structure of the repo and what each piece is responsible for, as it exists right now.

---

## Quick start

### Run the current upstream demo pipeline

From repo root:

```bash
python -m src.upstream
````

What it does (current behavior):

1. Loads vocab/rules YAML from `data/`
    
2. Connects via ADB to `127.0.0.1:5555`, LDplayer's adb port
    
3. Captures a screenshot to `data/captures/gear_panel.png`
    
4. Crops configured regions (debug dump optional)
    
5. Runs OCR recognizer (EasyOCR) to produce a `ParsedItem`
    
6. Canonicalizes + validates into a strict canonical form (or fails)
    

---

## Repository map (table of contents)

### `src/` — core library code

#### Entry / Orchestration

- `src/upstream.py`
    
    - Current “main pipeline” entrypoint when you run `python -m src.upstream`
        
    - Owns: capture → region crop (debug) → recognizer → canonicalize → error handling
        

#### Capture / Device interface

- `src/adb_client.py`
    
    - ADB connection + screenshot capture (expects emulator/device reachable at configured address)
        
    - Output is an image saved to disk used by the upstream pipeline
        

#### Region definitions (UI crop coordinates)

- `src/regions_config.py`
    
    - Defines `REGIONS`: a mapping of logical fields → crop rectangles
        
    - Rectangles are intentionally “superset” crops (wider than the exact label area) to tolerate UI jitter/concatenation
        

#### Recognition (current implementation: EasyOCR)

- `src/recognizer_easyocr.py`
    
    - `EasyOCRE7Recognizer`
        
    - Crops regions from the screenshot and runs EasyOCR
        
    - Builds a `ParsedItem` from recognized strings/numbers
        
    - Enforces a hard screenshot resolution gate (currently calibrated for 1920×1080)
        

> This module is the current “pixel → structured fields” layer and is the primary target for replacement (classifier/template approach).

#### Canonicalization / Validation

- `src/canonical.py`
    
    - Converts `ParsedItem` (noisy/partial) into canonical normalized tokens
        
    - Applies strict requirements: item must have all mandatory fields to be considered valid
        
    - Applies rules constraints (e.g., allowed main stats per slot)
        
    - Returns either canonical item + errors, or failure + errors
        

#### Schema / Types (current state)

- `src/schema.py`
    
    - Present but currently empty (placeholder)
        
    - Some schema-like structure is currently implied by the `ParsedItem` structures used in recognizer/canonicalization
        

---

### `data/` — closed-world vocab + rules + artifacts

- `data/vocab.yaml`
    
    - “Closed library” definitions (slots/sets/stats/rarities aliases, canonical tokens, etc.)
        
    - Used by canonicalization to normalize noisy inputs
        
- `data/rules.yaml`
    
    - Constraint rules used during canonicalization/validation
        
    - Example: slot → allowed main stats, left-side fixed mains, etc.
        
- `data/captures/`
    
    - Output directory for screenshots and debugging crops
        
    - `gear_panel.png` is the default screenshot path used by the upstream demo
        
    - Debug crop dumps can be placed under a `last_run_crops/` style folder
        

---

## Current pipeline stages (conceptual)

### Stage A — Capture

**Responsibility:** Get a screenshot image.

- Implemented via ADB screenshot call
    
- Output: image file on disk
    

### Stage B — Region cropping

**Responsibility:** Extract relevant UI regions for recognition.

- Implemented via `REGIONS` rectangle map
    
- Output: per-field crops (optional debug dump)
    

### Stage C — Recognition (current: OCR)

**Responsibility:** Convert crops into raw field readings.

- Implemented by `EasyOCRE7Recognizer`
    
- Output: `ParsedItem` (slot/set/rarity/ilevel/enhance/main/subs, with confidence where available)
    

### Stage D — Canonicalization + validation

**Responsibility:** Convert parsed readings into canonical tokens; enforce constraints.

- Implemented by `canonicalize(...)`
    
- Output: canonical item OR failure with errors
    

---

## Design notes (current version)

### Strict downstream invariant

Canonicalization currently treats core fields as mandatory. If any required field is missing/invalid, it fails rather than emitting a partial canonical item.

### Regions are intentionally wide

Many rectangles are deliberately larger than the “tight” text bounding box due to:

- UI text movement/jitter
    
- concatenated strings appearing inside the same general area
    
- desire to capture a superset and disambiguate later
    

### OCR is a temporary recognition strategy

The recognition stage is expected to be replaced with:

- classifier(s), template matching, or other closed-world detectors
    
- a resolver that chooses globally-consistent tokens using constraints
    

---

## Known “next structural change” (planned)

Replace **Recognition (Stage C)**:

- Current: `EasyOCRE7Recognizer` does crop → EasyOCR → parse → `ParsedItem`
    
- Planned: swap with a closed-world recognizer (classifier/template/detector), likely producing either:
    
    - a `ParsedItem` directly (drop-in), or
        
    - “observations/hypotheses” that are resolved later into a `ParsedItem` / canonical item
        

---

## How to navigate when modifying upstream

If you’re changing “what reads pixels”:

- work in `src/recognizer_*`
    
- keep the upstream entrypoint (`src/upstream.py`) stable as much as possible
    

If you’re changing “what valid items look like”:

- work in `data/vocab.yaml`, `data/rules.yaml`, and `src/canonical.py`
    

If you’re changing “what gets cropped”:

- work in `src/regions_config.py`
    
- use the crop dump hook in upstream to verify regions visually
    

---

## Status

This README reflects the repo as it currently exists:

- Working demo pipeline: capture → OCR → canonicalize
    
- Primary bottleneck: recognition reliability (OCR) and the need for a closed-world approach
    

```

If you want this to be a *true* table-of-contents (with links that won’t break), you can paste it into `README.md` and replace filenames with relative links like `./src/upstream.py`, `./data/vocab.yaml`, etc.
```