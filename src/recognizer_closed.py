# src/recognizer_closed.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple
import numpy as np
from PIL import Image

from src.contracts import RawCapture, CanonItem, CanonStatLine, RecError

DEBUG = False

def debug_print(*args, **kwargs):
    if DEBUG:
        print(*args, **kwargs)



SUBSTAT_FIELD_PAIRS = [
    ("sub1_stat", "sub1_value"),
    ("sub2_stat", "sub2_value"),
    ("sub3_stat", "sub3_value"),
    ("sub4_stat", "sub4_value"),
]

def canon_stat(token: str, has_percent: bool) -> str:
    if token == "health":
        return "hp_pct" if has_percent else "hp_flat"

    if token == "attack":
        return "atk_pct" if has_percent else "atk_flat"

    if token == "def":
        return "def_pct" if has_percent else "def_flat"

    if token == "speed":
        return "spd"

    if token == "crit":
        return "cr"

    if token == "cdmg":
        return "cd"

    if token == "eff":
        return "eff"

    if token == "effres":
        return "res"

    return token


# ---------- image utils ----------

def _load_rgb(path: Path) -> np.ndarray:
    return np.asarray(Image.open(path).convert("RGB"), dtype=np.uint8)

def _crop(arr: np.ndarray, rect: Tuple[int, int, int, int]) -> np.ndarray:
    x, y, w, h = rect
    return arr[y : y + h, x : x + w]

def _to_gray(arr: np.ndarray) -> np.ndarray:
    return (0.299 * arr[..., 0] + 0.587 * arr[..., 1] + 0.114 * arr[..., 2]).astype(np.uint8)

def _binarize_bright_text(crop_rgb: np.ndarray, threshold: int = 150) -> np.ndarray:
    gray = _to_gray(crop_rgb)
    return gray > threshold

def _split_glyph_spans(mask: np.ndarray, min_width: int = 2) -> List[Tuple[int, int]]:
    col_has_ink = mask.any(axis=0)

    spans: List[Tuple[int, int]] = []
    start: Optional[int] = None

    for x, has_ink in enumerate(col_has_ink):
        if has_ink and start is None:
            start = x
        elif not has_ink and start is not None:
            if x - start >= min_width:
                spans.append((start, x))
            start = None

    if start is not None:
        end = mask.shape[1]
        if end - start >= min_width:
            spans.append((start, end))

    return spans

def _zncc(a: np.ndarray, b: np.ndarray) -> float:
    a = a.astype(np.float32)
    b = b.astype(np.float32)
    a = a - a.mean()
    b = b - b.mean()
    denom = float(np.sqrt((a * a).sum()) * np.sqrt((b * b).sum()))
    if denom <= 1e-8:
        return -1.0
    return float((a * b).sum() / denom)


def _best_slide_score(patch: np.ndarray, templ: np.ndarray, stride: int = 1) -> float:
    ph, pw = patch.shape
    th, tw = templ.shape
    if th > ph or tw > pw:
        return -1.0
    best = -1.0
    for y in range(0, ph - th + 1, stride):
        for x in range(0, pw - tw + 1, stride):
            s = _zncc(patch[y : y + th, x : x + tw], templ)
            if s > best:
                best = s
    return best

def _score_to_conf(best: float, runner_up: float) -> float:
    """
    Cheap confidence proxy based on margin.
    ZNCC is [-1,1]. If best barely beats runner-up, confidence low.
    """
    margin = best - runner_up
    # clamp and map to [0,1]
    # typical margins when clear might be ~0.05-0.20 depending on noise
    conf = max(0.0, min(1.0, (margin / 0.15)))
    return float(conf)


# ---------- template bank ----------

class TemplateBank:
    def __init__(self, root: Path):
        self.root = root
        self._cache: Dict[Path, np.ndarray] = {}

    def _field_dir(self, field: str, profile: str | None = None) -> Path:
        if profile is not None:
            return self.root / field / profile
        return self.root / field

    def tokens(self, field: str, profile: str | None = None) -> List[str]:
        d = self._field_dir(field, profile)
        if not d.exists():
            return []
        return sorted(p.stem for p in d.glob("*.png"))

    def gray(self, field: str, token: str, profile: str | None = None) -> Optional[np.ndarray]:
        p = self._field_dir(field, profile) / f"{token}.png"
        if not p.exists():
            return None
        if p not in self._cache:
            self._cache[p] = np.asarray(Image.open(p).convert("L"), dtype=np.uint8)
        return self._cache[p]


# ---------- generic field recognizer (templates) ----------

@dataclass(frozen=True)
class TokenPred:
    token: str
    score: float
    conf: float

@dataclass(frozen=True)
class ValuePred:
    raw_text: str
    value: Optional[int]
    has_percent: bool
    score: float
    glyphs: List[TokenPred]

class FieldTemplateRecognizer:
    def __init__(
        self,
        bank: TemplateBank,
        field: str,
        *,
        profile: str | None = None,
        stride: int = 1,
        min_score: float = 0.20,
        min_conf: float = 0.60,
    ):
        self.bank = bank
        self.field = field
        self.profile = profile
        self.stride = stride
        self.min_score = min_score
        self.min_conf = min_conf

    def predict(self, crop_rgb: np.ndarray) -> Tuple[Optional[TokenPred], List[RecError]]:
        tokens = self.bank.tokens(self.field, self.profile)
        if not tokens:
            prof = f" profile='{self.profile}'" if self.profile else ""
            return None, [RecError(self.field, f"no templates for field '{self.field}'{prof}")]

        crop_g = _to_gray(crop_rgb)

        scored: List[Tuple[str, float]] = []
        for tok in tokens:
            templ = self.bank.gray(self.field, tok, self.profile)
            if templ is None:
                continue
            score = _best_slide_score(crop_g, templ, stride=self.stride)
            scored.append((tok, score))

        if not scored:
            prof = f" profile='{self.profile}'" if self.profile else ""
            return None, [RecError(self.field, f"no usable templates loaded for '{self.field}'{prof}")]

        scored.sort(key=lambda x: x[1], reverse=True)
        
        if self.field == "sub_stat":
            prof = f"/{self.profile}" if self.profile else ""
            debug_print(f"\n[{self.field}{prof}] top matches:")
            for tok, score in scored[:5]:
                debug_print(f"  {tok}: {score:.3f}")

        best_tok, best_score = scored[0]
        runner_up = scored[1][1] if len(scored) > 1 else -1.0
        conf = _score_to_conf(best_score, runner_up)

        if best_score < self.min_score or conf < self.min_conf:
            return None, [RecError(self.field, f"low match: best={best_tok} score={best_score:.3f} conf={conf:.3f}")]

        return TokenPred(best_tok, best_score, conf), []
# ---------- DigitSequenceRecognizer ---------
class DigitSequenceRecognizer:
    def __init__(
            self,
            bank: TemplateBank,
            *,
            profile: str,
            field: str = "digit",
            min_score: float = 0.70,
            stride: int= 1,
            allow_blank: bool = False,
    ):
        self.bank = bank
        self.profile = profile
        self.field = field
        self.min_score = min_score
        self.stride = stride
        self.allow_blank = allow_blank

    def _best_glyph(self, glyph_rgb: np.ndarray) -> Tuple[Optional[TokenPred], List[RecError]]:
        tokens = self.bank.tokens(self.field, self.profile)
        if not tokens:
            return None, [RecError(self.field, f"no templates for field '{self.field}' profile='{self.profile}'")]

        glyph_g = _to_gray(glyph_rgb)

        scored: List[Tuple[str, float]] = []

        for tok in tokens:
            templ = self.bank.gray(self.field, tok, self.profile)
            if templ is None:
                continue

            score = _best_slide_score(glyph_g, templ, stride=self.stride)
            scored.append((tok, score))

        if not scored:
            return None, [RecError(self.field, f"no usable digit templates for profile '{self.profile}'")]

        scored.sort(key=lambda x: x[1], reverse=True)

        best_tok, best_score = scored[0]
        runner_up = scored[1][1] if len(scored) > 1 else -1.0
        conf = _score_to_conf(best_score, runner_up)

        if best_score < self.min_score:
            return None, [RecError(self.field, f"low digit match: best={best_tok} score={best_score:.3f}")]

        return TokenPred(best_tok, best_score, conf), []

    def predict(self, crop_rgb: np.ndarray) -> Tuple[Optional[ValuePred], List[RecError]]:
        errs: List[RecError] = []

        mask = _binarize_bright_text(crop_rgb, threshold=150)
        spans = _split_glyph_spans(mask)

        ## temp debug print
        debug_print(f"[{self.field}/{self.profile}] crop shape:", crop_rgb.shape)
        debug_print(f"[{self.field}/{self.profile}] spans:", spans)

        if not spans:
            if self.allow_blank:
                return None, []
            return None, [RecError(self.field, "no glyph spans found")]

        if len(spans) > 5:
            return None, [RecError(self.field, f"too many glyph spans found: {len(spans)}")]

        glyph_preds: List[TokenPred] = []

        for x0, x1 in spans:
            # Add small horizontal padding around each glyph.
            px0 = max(0, x0 - 1)
            px1 = min(crop_rgb.shape[1], x1 + 1)

            glyph_rgb = crop_rgb[:, px0:px1]

            pred, e = self._best_glyph(glyph_rgb)
            errs.extend(e)
            
            ## temp debug print
            debug_print(f"[{self.field}/{self.profile}] glyph {x0}-{x1} =>", pred)

            if pred is None:
                return None, errs

            glyph_preds.append(pred)

        raw_text = "".join(pred.token for pred in glyph_preds)

        has_percent = "%" in raw_text
        numeric_text = raw_text.replace("%", "").replace("+", "")

        if numeric_text == "":
            return None, errs + [RecError(self.field, f"no numeric digits in '{raw_text}'")]

        if not numeric_text.isdigit():
            return None, errs + [RecError(self.field, f"bad numeric text '{raw_text}'")]

        value = int(numeric_text)
        avg_score = float(sum(pred.score for pred in glyph_preds) / len(glyph_preds))

        return ValuePred(
            raw_text=raw_text,
            value=value,
            has_percent=has_percent,
            score=avg_score,
            glyphs=glyph_preds,
        ), errs

# ---------- ClosedSetRecognizer ----------
PROFILES = ["bag", "detail", "bulk"]
class ClosedSetRecognizer:

    def _make_rec_by_profile(
        self,
        field: str,
        *,
        stride: int = 2,
        min_score: float = 0.18,
        min_conf: float = 0.55,
    ):
        return {
            profile: FieldTemplateRecognizer(
                self.bank,
                field,
                profile=profile,
                stride=stride,
                min_score=min_score,
                min_conf=min_conf,
            )
            for profile in PROFILES
        }
    
    def __init__(self, *, template_root: Path):
        self.bank = TemplateBank(template_root)

        self.slot_rec_by_profile = self._make_rec_by_profile(
            "slot",
            stride=1,
            min_score=0.20,
            min_conf=0.40,
        )

        self.rarity_rec_by_profile = self._make_rec_by_profile(
            "rarity",
            stride=1,
            min_score=0.20,
            min_conf=0.40,
        )

        self.enhance_rec_by_profile = self._make_rec_by_profile(
            "enhance",
            stride=1,
            min_score=0.20,
            min_conf=0.40,
        )

        self.enhance_weapon_rec_by_profile = self._make_rec_by_profile(
            "enhance",
            stride=1,
            min_score=0.15,
            min_conf=0.15,
        )

        self.set_rec_by_profile = self._make_rec_by_profile(
            "set",
            stride=2,
            min_score=0.18,
            min_conf=0.40,
        )

        self.main_stat_rec_by_profile = self._make_rec_by_profile(
            "main_stat",
            stride=2,
            min_score=0.18,
            min_conf=0.40,
        )

        self.sub_stat_rec_by_profile = self._make_rec_by_profile(
            "sub_stat",
            stride=2,
            min_score=0.18,
            min_conf=0.00,
        )

        self.otherworldly_rec_by_profile = self._make_rec_by_profile(
            "otherworldly",
            stride=2,
            min_score=0.75,
            min_conf=0.0,
        )

        self.digit_main_rec_by_profile = {}
        self.digit_sub_rec_by_profile = {}

        for profile in PROFILES:
            self.digit_main_rec_by_profile[profile] = DigitSequenceRecognizer(
                self.bank,
                profile=profile,
                field="digits_main",
                min_score=0.70,
                stride=1,
            )

            self.digit_sub_rec_by_profile[profile] = DigitSequenceRecognizer(
                self.bank,
                profile=profile,
                field="digits_sub",
                min_score=0.70,
                stride=1,
                allow_blank=True,
            )
                    
    @classmethod
    def create(cls, *, root: Path) -> "ClosedSetRecognizer":
        return cls(template_root=root / "data" / "recognition" / "templates")

    def recognize(self, cap: RawCapture) -> Tuple[Optional[CanonItem], Sequence[RecError]]:
        errs: List[RecError] = []

        img = _load_rgb(Path(cap.screenshot_path))

        profile = getattr(cap, "profile", None)
        if profile is None and hasattr(cap, "meta") and isinstance(cap.meta, dict):
            profile = cap.meta.get("profile")

        if profile is None:
            return None, errs + [RecError("profile", "missing profile")]

        slot_rec = self.slot_rec_by_profile.get(profile)
        if slot_rec is None:
            return None, errs + [RecError("slot", f"no slot recognizer for profile '{profile}'")]

        rarity_rec = self.rarity_rec_by_profile.get(profile)
        if rarity_rec is None:
            return None, errs + [RecError("rarity", f"no rarity recognizer for profile '{profile}'")]

        enhance_rec = self.enhance_rec_by_profile.get(profile)
        if enhance_rec is None:
            return None, errs + [RecError("enhance", f"no enhance recognizer for profile '{profile}'")]

        enhance_weapon_rec = self.enhance_weapon_rec_by_profile.get(profile)
        if enhance_weapon_rec is None:
            return None, errs + [RecError("enhance", f"no weapon enhance recognizer for profile '{profile}'")]

        set_rec = self.set_rec_by_profile.get(profile)
        if set_rec is None:
            return None, errs + [RecError("set", f"no set recognizer for profile '{profile}'")]

        main_stat_rec = self.main_stat_rec_by_profile.get(profile)
        if main_stat_rec is None:
            return None, errs + [RecError("main_stat", f"no main_stat recognizer for profile '{profile}'")]

        sub_stat_rec = self.sub_stat_rec_by_profile.get(profile)
        if sub_stat_rec is None:
            return None, errs + [RecError("sub_stat", f"no sub_stat recognizer for profile '{profile}'")]

        otherworldly_rec = self.otherworldly_rec_by_profile.get(profile)
        if otherworldly_rec is None:
            return None, errs + [RecError("otherworldly", f"no otherworldly recognizer for profile '{profile}'")]

        slot_crop = _crop(img, cap.regions["slot"])
        rarity_crop = _crop(img, cap.regions["rarity"])
        set_crop = _crop(img, cap.regions["set"])
        enh_crop = _crop(img, cap.regions["enhance"])
        otherworldly_crop = _crop(img, cap.regions["otherworldly"])

        # slot first so we can special-case weapons
        slot_pred, e = slot_rec.predict(slot_crop)
        errs.extend(e)
        if slot_pred is None:
            return None, errs

        # normal enhance attempt
        enh_pred, e = enhance_rec.predict(enh_crop)

        if enh_pred is None and slot_pred.token == "weapon":
            enh_pred, e = enhance_weapon_rec.predict(enh_crop)

        errs.extend(e)
        if enh_pred is None:
            return None, errs

        try:
            enhance = int(enh_pred.token.replace("+", ""))
        except ValueError:
            return None, errs + [RecError("enhance", f"bad token '{enh_pred.token}'")]

        rarity_pred, e = rarity_rec.predict(rarity_crop)
        errs.extend(e)
        if rarity_pred is None:
            return None, errs

        set_pred, e = set_rec.predict(set_crop)
        errs.extend(e)
        if set_pred is None:
            return None, errs

        otherworldly_pred, _ = otherworldly_rec.predict(otherworldly_crop)
        is_otherworldly = (
            otherworldly_pred is not None
            and otherworldly_pred.score >= 0.75
        )

        main_stat_crop = _crop(img, cap.regions["main_stat"])
        main_stat_pred, e = main_stat_rec.predict(main_stat_crop)
        errs.extend(e)
        if main_stat_pred is None:
            return None, errs


        digit_main_rec = self.digit_main_rec_by_profile.get(profile)
        if digit_main_rec is None:
            return None, errs + [RecError("digits_main", f"no main digit recognizer for profile '{profile}'")]

        digit_sub_rec = self.digit_sub_rec_by_profile.get(profile)
        if digit_sub_rec is None:
            return None, errs + [RecError("digits_sub", f"no sub digit recognizer for profile '{profile}'")]

        sub_stat_preds = []
        sub_value_preds = []
        SUBSTAT_OPTIONAL_ICON_MIN_SCORE = 0.40

        for stat_key, value_key in SUBSTAT_FIELD_PAIRS:
            row_errs: list[RecError] = []

            stat_crop = _crop(img, cap.regions[stat_key])
            stat_pred, e = sub_stat_rec.predict(stat_crop)

            if e:
                row_errs.extend(
                    RecError(stat_key, err.reason)
                    for err in e
                )

            debug_print(stat_key, "=>", stat_pred)

            if stat_pred is not None and stat_pred.score < SUBSTAT_OPTIONAL_ICON_MIN_SCORE:
                debug_print(
                    stat_key,
                    f"low substat icon score {stat_pred.score:.3f}; treating as blank",
                )
                stat_pred = None

            value_crop = _crop(img, cap.regions[value_key])
            value_pred, e = digit_sub_rec.predict(value_crop)

            if e:
                row_errs.extend(
                    RecError(value_key, err.reason)
                    for err in e
                )

            debug_print(value_key, "=>", value_pred)

            # Legal blank row: no stat icon and no value.
            if stat_pred is None and value_pred is None:
                continue

            # Illegal partial row: one side exists, the other does not.
            if stat_pred is None or value_pred is None:
                errs.extend(row_errs)
                errs.append(
                    RecError(
                        f"{stat_key}/{value_key}",
                        f"partial substat row: stat={stat_pred}, value={value_pred}",
                    )
                )
                return None, errs

            # Complete row.
            errs.extend(row_errs)
            sub_stat_preds.append(stat_pred)
            sub_value_preds.append(value_pred)


        
        main_value_crop = _crop(img, cap.regions["main_value"])
        main_value_pred, e = digit_main_rec.predict(main_value_crop)

        if e:
            errs.extend(
                RecError("main_value", err.reason)
                for err in e
            )

        debug_print("main_value:", main_value_pred)

        if main_value_pred is None:
            return None, errs

        debug_print("profile:", profile)
        debug_print("slot:", slot_pred)
        debug_print("rarity:", rarity_pred)
        debug_print("set:", set_pred)
        debug_print("enhance:", enhance, "| raw:", enh_pred)
        debug_print("otherworldly:", is_otherworldly)
        debug_print("main_stat:", main_stat_pred)
        debug_print("sub_stats:", sub_stat_preds)
        debug_print("main_value:", main_value_pred)
        debug_print("sub_values:", sub_value_preds)

        item = CanonItem(
            schema_version=1,
            slot=slot_pred.token,
            set=set_pred.token,
            rarity=rarity_pred.token,
            ilevel=85,
            enhance=enhance,
            otherworldly=is_otherworldly,
            main=CanonStatLine(
                stat=canon_stat(main_stat_pred.token, main_value_pred.has_percent),
                value=main_value_pred.value,
                confidence=min(main_stat_pred.conf, main_value_pred.score),
            ),
            subs=[
                CanonStatLine(
                    stat=canon_stat(stat_pred.token, value_pred.has_percent),
                    value=value_pred.value,
                    confidence=min(stat_pred.conf, value_pred.score),
                )
                for stat_pred, value_pred in zip(sub_stat_preds, sub_value_preds)
            ],
        )

        return item, errs