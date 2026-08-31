#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "capability-test/incoming/scc-live-observe-001.json"
EXPECTED = ROOT / "capability-test/expected/scc-live-observe-001.normalized.json"
WORKFLOW = ROOT / ".github/workflows/capability-test-ingress.yml"

REQUIRED_IDENTITIES = ("capability_id", "adapter_id", "device_or_surface_id", "actor_id")
REQUIRED_INTERLOCKS = {
    "no_hardware_endpoint",
    "no_external_device_api",
    "no_control_center_dispatch",
}
REQUIRED_PROHIBITIONS = {
    "physical_actuation",
    "authority_escalation",
    "procedure_promotion",
}


def load(path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def normalize(source):
    out = {
        "trace_id": source["trace_id"],
        "workflow": source["workflow"],
        "repo": source["repo"],
        "status": source.get("status", "unknown"),
        "timestamp": source["timestamp"],
    }
    for key in ("event_class", "protocol_version", "synthetic_test", "test_posture"):
        if key in source:
            out[key] = source[key]
    if isinstance(source.get("semantic"), dict):
        out["semantic"] = source["semantic"]
    if isinstance(source.get("evidence"), dict):
        out["evidence"] = source["evidence"]
    out["normalization"] = {
        "membrane_version": "archivist.capability-test.v0.1",
        "admission_posture": "synthetic_test_only",
        "source_file": "capability-test/incoming/scc-live-observe-001.json",
    }
    if isinstance(source.get("capability_context"), dict):
        out["capability_context"] = source["capability_context"]
    return out


def validate(source, expected, workflow_text):
    errors = []
    ctx = source.get("capability_context") or {}
    identity = ctx.get("identity") or {}
    declaration = ctx.get("declaration") or {}
    authority = ctx.get("authority") or {}
    constraints = ctx.get("constraints") or {}

    if source.get("synthetic_test") is not True:
        errors.append("source fixture must be marked synthetic_test=true")
    if declaration.get("actuation_available") is not False:
        errors.append("actuation_available must be false")
    if authority.get("posture") != "observe":
        errors.append("authority posture must be observe")
    if authority.get("ceiling") != "observe":
        errors.append("authority ceiling must be observe")
    for field in REQUIRED_IDENTITIES:
        if not identity.get(field):
            errors.append(f"missing identity field: {field}")
    if not authority.get("basis_ref"):
        errors.append("basis_ref is required")
    if not authority.get("gate_ref"):
        errors.append("gate_ref is required")

    declared = set(declaration.get("declared_actions") or [])
    allowed = set(authority.get("allowed_actions") or [])
    prohibited = set(authority.get("prohibited_actions") or [])
    if not allowed.issubset(declared):
        errors.append("allowed_actions must be a subset of declared_actions")
    if allowed & prohibited:
        errors.append("allowed_actions and prohibited_actions overlap")
    if not REQUIRED_PROHIBITIONS.issubset(prohibited):
        errors.append("required prohibitions are missing")

    interlocks = set(constraints.get("hard_interlocks") or [])
    if not REQUIRED_INTERLOCKS.issubset(interlocks):
        errors.append("required hard interlocks are missing")

    actual = normalize(source)
    if actual != expected:
        errors.append("expected normalized fixture differs from deterministic normalization")
    if actual.get("capability_context") != source.get("capability_context"):
        errors.append("capability_context was not preserved exactly")

    forbidden_workflow_tokens = ("Codex-control-center", "route-event")
    for token in forbidden_workflow_tokens:
        if token in workflow_text:
            errors.append(f"forbidden workflow target/token present: {token}")
    if workflow_text.count("/dispatches") != 1:
        errors.append("dedicated workflow must contain exactly one /dispatches target")
    if "sovereign-codex/AVOT-TRACE/dispatches" not in workflow_text:
        errors.append("TRACE dispatch target missing")

    return errors


def main():
    source = load(SOURCE)
    expected = load(EXPECTED)
    workflow_text = WORKFLOW.read_text(encoding="utf-8")
    errors = validate(source, expected, workflow_text)
    if errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)
    print("PASS")
    print("fixture_id=SCC-LIVE-OBSERVE-001")
    print("synthetic_test=true")
    print("actuation_available=false")
    print("authority_ceiling=observe")
    print("dispatch_target=AVOT-TRACE-only")
    print("repository_writes=not_permitted")


if __name__ == "__main__":
    main()
