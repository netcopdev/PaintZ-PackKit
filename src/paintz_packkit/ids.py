from __future__ import annotations

import re
import unicodedata

TYPE_CODES = {
    "basic": "B",
    "solid": "S",
    "camo": "C",
    "pattern": "P",
    "metallic": "M",
    "rusted": "R",
    "weathered": "W",
    "fluorescent": "F",
    "special": "X",
    "custom": "X",
    "transparent": "T",
}

COMMON_SUGGESTIONS = {
    "OLIVE DRAB": "ODG",
    "RANGER GREEN": "RGR",
    "NATO GREEN": "NTG",
    "COYOTE BROWN": "CBR",
    "FLAT DARK EARTH": "FDE",
    "DESERT TAN": "DTN",
    "KHAKI": "KHK",
    "FIELD GREY": "FGY",
    "FIELD GRAY": "FGY",
    "URBAN GREY": "UGY",
    "URBAN GRAY": "UGY",
    "BLACK": "BLK",
    "ARCTIC WHITE": "WHT",
    "WHITE": "WHT",
    "WOODLAND": "WDL",
    "DIGITAL WOODLAND": "DWD",
    "FLECKTARN": "FTN",
    "MULTICAM": "MTC",
    "DESERT DIGITAL": "DDT",
    "TIGER STRIPE": "TGR",
    "UNIVERSAL CAMOUFLAGE PATTERN": "UCP",
    "UNIVERSAL CAMOUFLAGE": "UCP",
    "UCP": "UCP",
}


def normalize_hex(value: str) -> str:
    value = value.strip().upper()
    if not value.startswith("#"):
        value = "#" + value
    if len(value) != 7 or any(c not in "0123456789ABCDEF" for c in value[1:]):
        raise ValueError(f"Invalid RGB color: {value!r}; expected #RRGGBB")
    return value


def normalize_prefix(value: str, *, allow_reserved_pz: bool = False) -> str:
    if not isinstance(value, str):
        raise TypeError("PaintZ pack prefix must be a string")
    prefix = value.strip().upper()
    if not re.fullmatch(r"[A-Z][A-Z0-9]{1,2}", prefix):
        raise ValueError(
            f"Invalid PaintZ pack prefix {value!r}; use 2-3 uppercase letters/digits "
            "with a letter first"
        )
    if prefix.startswith("PZ") and not allow_reserved_pz:
        raise ValueError(
            f"PaintZ pack prefix {prefix!r} is reserved for official PaintZ content; "
            "use --official only for the PaintZ Standard Pack/official content"
        )
    return prefix


def type_code(paint_type: str) -> str:
    try:
        return TYPE_CODES[paint_type.casefold()]
    except (AttributeError, KeyError):
        allowed = ", ".join(sorted(TYPE_CODES))
        raise ValueError(f"Unknown PaintZ type {paint_type!r}; expected one of: {allowed}")


def _ascii_words(value: str) -> list[str]:
    value = unicodedata.normalize("NFKD", value)
    value = value.encode("ascii", "ignore").decode("ascii")
    return re.findall(r"[A-Z0-9]+", value.upper())


def config_token(value: str) -> str:
    words = _ascii_words(value)
    token = "_".join(words)
    if not token:
        raise ValueError(f"Cannot derive a DayZ config token from {value!r}")
    if token[0].isdigit():
        token = "P_" + token
    return token


def normalize_suffix(value: str) -> str:
    if not isinstance(value, str):
        raise TypeError("PaintZ id must be a string")
    suffix = value.strip().upper()
    if not re.fullmatch(r"[A-Z0-9]{2,12}", suffix):
        raise ValueError(
            f"Invalid PaintZ id {value!r}; use 2-12 letters/digits only "
            "(3 descriptive characters are preferred)"
        )
    return suffix


def _consonant_skeleton(word: str) -> str:
    if not word:
        return ""
    chars = [word[0]]
    chars.extend(ch for ch in word[1:] if ch not in "AEIOUY")
    chars.extend(ch for ch in word[1:] if ch in "AEIOUY")
    out = ""
    for ch in chars:
        if ch not in out:
            out += ch
    return out


def suggest_suffix(name: str) -> str:
    words = _ascii_words(name)
    if not words:
        raise ValueError(f"Cannot suggest PaintZ id from name {name!r}")
    phrase = " ".join(words)
    if phrase in COMMON_SUGGESTIONS:
        return COMMON_SUGGESTIONS[phrase]
    if len(words) == 1 and 2 <= len(words[0]) <= 4 and words[0].isalnum():
        return words[0]
    if len(words) >= 3:
        acronym = "".join(w[0] for w in words if w)[:6]
        return normalize_suffix(acronym if len(acronym) >= 2 else phrase[:3])
    if len(words) == 2:
        tail = _consonant_skeleton(words[1])
        candidate = (words[0][0] + tail)[:3]
        if len(candidate) < 3:
            candidate = (candidate + _consonant_skeleton(words[0]) + words[1])[:3]
        return normalize_suffix(candidate)
    candidate = _consonant_skeleton(words[0])[:3]
    if len(candidate) < 2:
        candidate = words[0][:3]
    return normalize_suffix(candidate)


def suffix_for_paint(paint: dict) -> tuple[str, bool]:
    if paint.get("id"):
        return normalize_suffix(paint["id"]), False
    return suggest_suffix(paint.get("name", "")), True


def code_for_paint(paint: dict, prefix: str) -> tuple[str, bool]:
    suffix, suggested = suffix_for_paint(paint)
    return f"{prefix}-{type_code(paint['type'])}-{suffix}", suggested


def code_to_slug(code: str) -> str:
    return code.lower().replace("-", "_")


def class_suffix(name: str, code: str) -> str:
    del name
    return code.split("-")[-1]
