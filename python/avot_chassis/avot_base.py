from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, Optional


@dataclass(frozen=True)
class AvotRefusal:
    """Structured refusal. Refusal is a valid outcome, not an error state."""

    reason: str
    reference: str
    next_step: str = "wait"


class AvotBase:
    """
    Minimal AVOT chassis (Python).

    Provides:
    - identity awareness
    - lifecycle awareness
    - action classification
    - permission checking
    - dignified refusal
    - signal emission

    Does NOT provide:
    - domain logic
    - enforcement of other AVOTs
    - automation/orchestration
    """

    def __init__(self, avot_id: str, header: Dict[str, Any], registry_entry: Dict[str, Any]):
        self.avot_id = avot_id
        self.header = header
        self.registry_entry = registry_entry

    # --- Identity & State ---

    def identify(self) -> Dict[str, Any]:
        return {
            "avot_id": self.avot_id,
            "purpose": self.header.get("purpose"),
            "steward": self.header.get("steward"),
            "header_ref": self.header.get("id"),
        }

    def state(self) -> Dict[str, Any]:
        return {
            "lifecycle_state": self.registry_entry.get("lifecycle_state"),
            "maturity": self.registry_entry.get("maturity"),
            "binding": bool(self.registry_entry.get("binding", False)),
        }

    # --- Action Classification ---

    def classify_action(self, intent: str) -> str:
        i = (intent or "").strip().lower()
        if i in {"think", "analyze", "reason"}:
            return "think"
        if i in {"say", "respond", "communicate"}:
            return "communicate"
        if i in {"run", "execute", "perform"}:
            return "execute"
        if i in {"bind", "write", "commit"}:
            return "bind"
        if i in {"propose", "suggest", "request"}:
            return "propose"
        return "communicate"

    # --- Permission Evaluation ---

    def can_attempt(self, action_type: str) -> bool:
        lifecycle = self.registry_entry.get("lifecycle_state")
        binding_allowed = bool(self.registry_entry.get("binding", False))

        if lifecycle in {"S6", "S7", "S8", "S9"}:
            return False

        if action_type == "bind" and not binding_allowed:
            return False

        return True

    # --- Refusal ---

    def refuse(self, reason: str, reference: str, next_step: str = "wait") -> AvotRefusal:
        return AvotRefusal(reason=reason, reference=reference, next_step=next_step)

    # --- Signals ---

    def emit_signal(self, signal_type: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return {
            "avot_id": self.avot_id,
            "signal_type": signal_type,
            "payload": payload or {},
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

    # --- Guarded attempt helper ---

    def attempt(self, intent: str, action_callable: Callable[[], Any]) -> Any:
        action_type = self.classify_action(intent)
        if not self.can_attempt(action_type):
            refusal = self.refuse(
                reason=f"Action '{action_type}' not permitted in current state",
                reference=f"lifecycle={self.registry_entry.get('lifecycle_state')}",
                next_step="propose",
            )
            raise PermissionError(refusal)
        return action_callable()
