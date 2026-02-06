from __future__ import annotations

from typing import Any, Dict

from avot_chassis.avot_base import AvotBase


class Archivist(AvotBase):
    """First system test AVOT: Archivist (non-binding)."""

    def summarize(self, text: str) -> str:
        # Communicate is allowed if lifecycle permits; bind must be explicitly permitted.
        self.attempt("communicate", lambda: None)
        t = (text or "").strip()
        return f"[ARCHIVIST] Summary (first 120 chars): {t[:120]}"
