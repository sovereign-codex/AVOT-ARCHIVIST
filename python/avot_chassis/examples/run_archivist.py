from __future__ import annotations

from pathlib import Path
import yaml

from avot_chassis.adapters.registry_loader import RegistryLoader
from avot_chassis.adapters.signal_ledger import SignalLedger
from avot_chassis.examples.archivist import Archivist


ROOT = Path(__file__).resolve().parents[2]  # python/


def load_yaml(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def main():
    # Paths assume repo layout
    registry_path = ROOT.parent / "registry" / "avot_registry.yaml"
    ledger_path = ROOT.parent / "registry" / "signal_ledger.yaml"
    header_path = ROOT.parent / "headers" / "AVOT-ARCHIVIST.header.yaml"

    header = load_yaml(header_path)

    loader = RegistryLoader(str(registry_path))
    entry = loader.get_avot_entry("AVOT-ARCHIVIST")

    avot = Archivist(avot_id="AVOT-ARCHIVIST", header=header, registry_entry=entry)

    print("IDENTITY:", avot.identify())
    print("STATE:", avot.state())

    # Demonstrate non-binding action
    print(avot.summarize("Today we anchored the chassis and proved self-awareness works."))

    # Emit a non-binding signal
    ledger = SignalLedger(str(ledger_path))
    sig = ledger.append_signal(
        avot_id="AVOT-ARCHIVIST",
        signal_type="scope_refusal",
        description="Example signal: repeated synthesis requests exceed archival mandate.",
        severity="low",
        context={"action_type": "communicate", "lifecycle_state": entry.get("lifecycle_state", "S3")},
        metadata={"count": 1},
    )
    print("SIGNAL APPENDED:", sig)


if __name__ == "__main__":
    main()
