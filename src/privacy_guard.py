"""Deterministic privacy and safety screening for photo metadata bundles."""

from __future__ import annotations

import re
from typing import Any

SENSITIVE_FILENAME_TERMS = {
    "passport",
    "license",
    "idcard",
    "id-card",
    "resident",
    "ssn",
    "credit",
    "card",
    "receipt",
    "ticket",
}

SENSITIVE_TEXT_TERMS = {
    "passport",
    "driver license",
    "resident registration",
    "social security",
    "credit card",
    "card number",
    "account number",
    "boarding pass",
    "주민등록",
    "여권",
    "운전면허",
    "신용카드",
    "계좌번호",
}

PATTERNS = {
    "email": re.compile(r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b"),
    "phone": re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?(?:\d{2,4}[-.\s]?){2,3}\d{3,4}\b"),
    "credit_card_like": re.compile(r"\b(?:\d[ -]*?){13,19}\b"),
    "korean_rrn_like": re.compile(r"\b\d{6}[- ]?[1-4]\d{6}\b"),
}


def screen_bundle(payload: dict[str, Any]) -> dict[str, Any]:
    photos = payload.get("photos") or []
    public_photos: list[dict[str, Any]] = []
    excluded_photos: list[dict[str, Any]] = []

    for photo in photos:
        if not isinstance(photo, dict):
            continue
        signals = detect_sensitive_signals(photo)
        reviewed = dict(photo)
        reviewed["privacy_review"] = {
            "public_safe": not signals,
            "signals": signals,
            "policy": "exclude" if signals else "allow",
        }
        if signals:
            reviewed["exclude_from_public_outputs"] = True
            reviewed["exclusion_reason"] = ", ".join(signals)
            excluded_photos.append(reviewed)
        else:
            reviewed["exclude_from_public_outputs"] = False
            public_photos.append(reviewed)

    return {
        "privacy_status": "ok",
        "public_photos": public_photos,
        "excluded_photos": excluded_photos,
        "public_photo_count": len(public_photos),
        "excluded_photo_count": len(excluded_photos),
        "checks": [
            {"name": "metadata_flags", "status": "pass"},
            {"name": "filename_terms", "status": "pass"},
            {"name": "ocr_text_patterns", "status": "pass"},
        ],
    }


def detect_sensitive_signals(photo: dict[str, Any]) -> list[str]:
    signals: list[str] = []
    summary = photo.get("photo_summary") if isinstance(photo.get("photo_summary"), dict) else {}
    if photo.get("exclude_from_public_outputs") or summary.get("exclude_from_public_outputs"):
        signals.append("pre_flagged_exclusion")

    file_name = str(photo.get("file_name") or "").lower()
    if any(term in file_name for term in SENSITIVE_FILENAME_TERMS):
        signals.append("sensitive_filename")

    text = " ".join(_text_values(summary.get("ocr_text")))
    text += " " + str(summary.get("summary") or "")
    text = text.lower()
    if any(term in text for term in SENSITIVE_TEXT_TERMS):
        signals.append("sensitive_text_term")
    for name, pattern in PATTERNS.items():
        if pattern.search(text):
            signals.append(name)

    return list(dict.fromkeys(signals))


def _text_values(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value]
    return []

