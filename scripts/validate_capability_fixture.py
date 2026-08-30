#!/usr/bin/env python3
"""Validate the offline Sovereign Capability preservation fixture.

This script performs local, read-only JSON checks. It does not import network
clients, invoke workflows, dispatch repository events, or write files.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

FIXTURE_ID = "MHS-EDGE-OBSERVE-001"
ALLOWED_ACTIONS = {
    "discover_declared_capability",
    "read_simulated_environmental_state",
    "return_static_evidence",
}
REQUIRED_PROHIBITED_ACTIONS = {
    "write_device_state",
    "energize_output",
    "move_hardware",
    "change_interlock",
    "dispatch_repository_event",
    "promote_procedure",
}
VALID_DISPOSITIONS = {
    "preserved",
    "fixture_metadata",
    "owned_elsewhere",
    "intentional_projection",
    "known_gap",
}


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"expected JSON object in {path}")
    return data


def flatten_leaves(value: Any, prefix: str = "") -> dict[str, Any]:
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, child in value.items():
            path = f"{prefix}.{key}" if prefix else key
            result.update(flatten_leaves(child, path))
        return result
    return {prefix: value}


def get_path(value: dict[str, Any], path: str) -> Any:
    current: Any = value
    for segment in path.split("."):
        if not isinstance(current, dict) or segment not in current:
            raise KeyError(path)
        current = current[segment]
    return current


def require(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    fixture_dir = repo_root / "fixtures" / "capability"
    source_path = fixture_dir / "mhs-edge-observe-001.source.json"
    expected_path = fixture_dir / "mhs-edge-observe-001.expected-normalized.json"
    loss_map_path = fixture_dir / "mhs-edge-observe-001.loss-map.json"

    failures: list[str] = []

    try:
        source = load_json(source_path)
        expected = load_json(expected_path)
        loss_map = load_json(loss_map_path)
    except ValueError as exc:
        print(f"FAIL: {exc}")
        return 1

    require(source.get("fixture_id") == FIXTURE_ID, "source fixture_id mismatch", failures)
    require(loss_map.get("fixture_id") == FIXTURE_ID, "loss-map fixture_id mismatch", failures)
    require(source.get("fixture_posture") == "synthetic_read_only", "fixture must remain synthetic_read_only", failures)

    capability = source.get("capability", {})
    authority = source.get("authority", {})
    constraints = source.get("constraints", {})
    payload = source.get("payload", {})

    require(capability.get("actuation_available") is False, "actuation_available must be false", failures)
    require(authority.get("ceiling") in {"observe", "none"}, "authority ceiling must be observe or none", failures)
    require(authority.get("posture") in {"observe", "unknown", "none"}, "authority posture exceeds fixture scope", failures)
    require(payload.get("synthetic") is True, "payload must be explicitly synthetic", failures)
    require(constraints.get("safe_state") == "read_only", "safe_state must be read_only", failures)

    declared_actions = set(capability.get("declared_actions", []))
    authority_actions = set(authority.get("allowed_actions", []))
    unavailable_actions = set(capability.get("unavailable_actions", []))
    prohibited_actions = set(authority.get("prohibited_actions", []))

    require(declared_actions == ALLOWED_ACTIONS, "declared actions differ from the bounded allow-list", failures)
    require(authority_actions == ALLOWED_ACTIONS, "authority allow-list differs from declared observation actions", failures)
    require(REQUIRED_PROHIBITED_ACTIONS <= unavailable_actions, "capability unavailable-actions list is incomplete", failures)
    require(REQUIRED_PROHIBITED_ACTIONS <= prohibited_actions, "authority prohibited-actions list is incomplete", failures)
    require(not (ALLOWED_ACTIONS & REQUIRED_PROHIBITED_ACTIONS), "allowed and prohibited action sets overlap", failures)

    source_leaves = flatten_leaves(source)
    expected_leaves = flatten_leaves(expected)

    fields = loss_map.get("fields", [])
    require(isinstance(fields, list), "loss-map fields must be a list", failures)
    field_entries: dict[str, dict[str, Any]] = {}
    if isinstance(fields, list):
        for entry in fields:
            if not isinstance(entry, dict):
                failures.append("loss-map field entry must be an object")
                continue
            source_key = entry.get("source_path")
            disposition = entry.get("disposition")
            if not isinstance(source_key, str):
                failures.append("loss-map field entry missing source_path")
                continue
            if source_key in field_entries:
                failures.append(f"duplicate loss-map entry: {source_key}")
            field_entries[source_key] = entry
            require(disposition in VALID_DISPOSITIONS, f"invalid disposition for {source_key}: {disposition}", failures)

    missing_classifications = sorted(set(source_leaves) - set(field_entries))
    extra_classifications = sorted(set(field_entries) - set(source_leaves))
    require(not missing_classifications, f"unclassified source fields: {missing_classifications}", failures)
    require(not extra_classifications, f"loss-map entries not present in source: {extra_classifications}", failures)

    mapped_destinations: set[str] = set()
    for source_key, entry in field_entries.items():
        disposition = entry.get("disposition")
        destination = entry.get("destination_path")
        if disposition == "preserved":
            require(isinstance(destination, str) and bool(destination), f"preserved field lacks destination: {source_key}", failures)
            if isinstance(destination, str) and destination:
                mapped_destinations.add(destination)
                try:
                    actual = get_path(expected, destination)
                except KeyError:
                    failures.append(f"preserved destination missing from expected output: {destination}")
                else:
                    require(actual == source_leaves[source_key], f"preserved value mismatch: {source_key} -> {destination}", failures)
        else:
            require(destination is None, f"non-preserved field must not claim a destination: {source_key}", failures)

    derived = loss_map.get("derived_fields", [])
    require(isinstance(derived, list), "derived_fields must be a list", failures)
    declared_derived: set[str] = set()
    if isinstance(derived, list):
        for entry in derived:
            if not isinstance(entry, dict):
                failures.append("derived field entry must be an object")
                continue
            expected_key = entry.get("expected_path")
            if not isinstance(expected_key, str):
                failures.append("derived field entry missing expected_path")
                continue
            declared_derived.add(expected_key)
            require(expected_leaves.get(expected_key) == entry.get("value"), f"derived value mismatch: {expected_key}", failures)

    unexplained_expected = sorted(set(expected_leaves) - mapped_destinations - declared_derived)
    require(not unexplained_expected, f"expected fields lack preserved or derived basis: {unexplained_expected}", failures)

    critical_paths = loss_map.get("critical_known_gap_paths", [])
    require(isinstance(critical_paths, list), "critical_known_gap_paths must be a list", failures)
    if isinstance(critical_paths, list):
        for path in critical_paths:
            entry = field_entries.get(path)
            require(entry is not None, f"critical known gap missing loss-map entry: {path}", failures)
            if entry is not None:
                require(entry.get("disposition") == "known_gap", f"critical path is not marked known_gap: {path}", failures)
                require(entry.get("severity") in {"high", "critical"}, f"critical path severity too low: {path}", failures)

    identity_paths = {
        "identity.capability_id",
        "identity.adapter_id",
        "identity.device_id",
        "identity.actor_id",
    }
    authority_boundary_paths = {
        "authority.basis_ref",
        "authority.gate_ref",
        "authority.allowed_actions",
        "authority.prohibited_actions",
    }
    require(identity_paths <= set(critical_paths), "identity losses are not all declared critical gaps", failures)
    require(authority_boundary_paths <= set(critical_paths), "authority-boundary losses are not all declared critical gaps", failures)

    policy = loss_map.get("policy", {})
    require(policy.get("physical_actuation_is_prohibited") is True, "loss-map policy must prohibit physical actuation", failures)
    require(policy.get("index_or_projection_is_not_authority") is True, "loss-map policy must deny projection authority", failures)

    if failures:
        print("FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1

    known_gap_count = sum(1 for entry in field_entries.values() if entry.get("disposition") == "known_gap")
    preserved_count = sum(1 for entry in field_entries.values() if entry.get("disposition") == "preserved")
    print("PASS_WITH_KNOWN_GAPS")
    print(f"fixture_id={FIXTURE_ID}")
    print(f"source_leaf_fields={len(source_leaves)}")
    print(f"preserved_fields={preserved_count}")
    print(f"known_gap_fields={known_gap_count}")
    print("actuation_available=false")
    print("authority_ceiling=observe")
    print("network_access=not_used")
    return 0


if __name__ == "__main__":
    sys.exit(main())
