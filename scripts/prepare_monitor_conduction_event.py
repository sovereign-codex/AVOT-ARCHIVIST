#!/usr/bin/env python3
"""Prepare ERA monitor-conduction evidence locally; never ingest, dispatch, or promote it."""
import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re


FIXTURE_ID = "ERA-AVOT-CIRCULATION-001"
REQUEST_PREFIX = "monitor-conduction:"
SIGNAL_PREFIX = "signal:"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def require_string_list(value, message):
    require(isinstance(value, list) and all(isinstance(x, str) and x for x in value), message)


def prepare(raw, engine_sha):
    require(re.fullmatch(r"[0-9a-f]{40}", engine_sha), "Exact Engine commit SHA required")
    data = json.loads(raw)
    require(data.get("fixture_id") == FIXTURE_ID, "Unexpected fixture identity")

    circulation = data["result"]
    signal = circulation["monitor_signal"]
    inference = circulation["inference"]
    monitor_return = circulation["monitor_evidence_return"]
    handoff = circulation["handoff"]

    request = inference["request"]
    archive = inference["return_path"]["archivist"]
    trace = inference["return_path"]["trace"]
    plan = archive["plan"]
    result = archive["result"]

    signal_id = signal["signal_id"]
    request_id = request["request_id"]
    require(isinstance(signal_id, str) and signal_id.startswith(SIGNAL_PREFIX), "Unexpected signal identity")
    require(
        isinstance(request_id, str)
        and re.fullmatch(r"monitor-conduction:[a-z0-9][a-z0-9-]*", request_id),
        "Unexpected monitor-conduction request identity",
    )
    suffix = signal_id[len(SIGNAL_PREFIX):]
    require(request_id == REQUEST_PREFIX + suffix, "Signal/request identity mismatch")

    evidence_id = "inference:" + request_id
    require(archive["request_id"] == plan["request_id"] == result["request_id"] == request_id, "Request identity mismatch")
    require(archive["evidence_id"] == trace["trace_id"] == evidence_id, "Evidence identity mismatch")
    require(trace["repo"] == "sovereign-codex/AVOT-engine", "Unexpected source repository")

    require(signal.get("authority_posture") == "analysis_only", "Signal authority boundary mismatch")
    require(signal.get("institutional_effect") == "none", "Signal must have no institutional effect")
    require(monitor_return.get("authority_posture") == "analysis_only", "Monitor return authority boundary mismatch")
    require(monitor_return.get("institutional_effect") == "none", "Monitor return must have no institutional effect")
    require(monitor_return.get("return_status") == "returned", "Monitor return status mismatch")
    require(monitor_return.get("dormancy_entered") is True, "Monitor must return to dormancy")

    require(request.get("work_ref") is None, "Monitor conduction must not create Work")
    require(request.get("evidence_required") is True, "Evidence must be required")
    for item in (request, archive["request"], plan):
        require(item.get("privacy_boundary") == "local_only", "Privacy boundary mismatch")
        require(item.get("authority_posture") == "analysis_only", "Authority boundary mismatch")

    for key in ("intent", "work_ref", "privacy_boundary", "authority_posture"):
        require(archive["request"].get(key) == request.get(key), "Archived request mismatch")

    require(plan.get("strategy") == "direct", "First circulation fixture must remain direct")
    require(not plan.get("sidecars") and not plan.get("fallback_plan"), "Fixture must not use sidecars or fallback")

    signal_refs = signal.get("evidence_refs")
    source_refs = signal.get("source_refs")
    context_refs = request.get("context_refs")
    require_string_list(signal_refs, "Malformed signal evidence refs")
    require_string_list(source_refs, "Malformed signal source refs")
    require_string_list(context_refs, "Malformed inference context refs")
    require(signal_id in context_refs, "Inference context lost signal identity")
    for ref in signal_refs:
        require(ref in context_refs, "Inference context lost signal evidence")

    require(monitor_return.get("signal_refs") == [signal_id], "Monitor evidence return lost signal identity")
    for ref in source_refs:
        require(ref in monitor_return.get("source_refs", []), "Monitor evidence return lost source evidence")

    require(trace["timestamp"] == archive["captured_at"], "Capture timestamp mismatch")
    stamp = datetime.fromisoformat(trace["timestamp"].replace("Z", "+00:00"))
    require(stamp.tzinfo is not None, "Timestamp needs timezone")
    require(
        trace["workflow"] == "sovereign-inference/" + plan["strategy"] + "/" + plan["target_runtime"],
        "Runtime workflow mismatch",
    )

    status = result["status"]
    require(status in ("completed", "failed", "refused", "degraded"), "Unknown inference status")
    require(trace["status"] == status, "TRACE/result status mismatch")
    require(result.get("authority_effect") == "analysis_return", "Authority effect exceeds analysis")

    inference_refs = result.get("evidence_refs")
    require_string_list(inference_refs, "Malformed or missing inference evidence refs")

    expected_disposition = {
        "completed": "ready_for_review",
        "refused": "inference_refused",
        "degraded": "inference_degraded",
        "failed": "inference_failed",
    }[status]
    require(handoff.get("authority_posture") == "analysis_only", "Handoff authority boundary mismatch")
    require(handoff.get("institutional_effect") == "none", "Handoff must have no institutional effect")
    require(handoff.get("disposition") == expected_disposition, "Handoff disposition/status mismatch")
    if status == "completed":
        require(handoff.get("target") == "cit-monitor-council", "Completed inference needs review handoff")
        require(isinstance(result.get("output"), str) and result["output"].strip(), "Completed inference needs output")
        for used, target in (
            ("capability_used", "target_capability"),
            ("runtime_used", "target_runtime"),
            ("model_used", "target_model"),
        ):
            require(result.get(used) == plan.get(target), "Runtime/model/capability mismatch")
        require(result.get("node_refs") == [plan.get("target_node")], "Node mismatch")
    else:
        require(handoff.get("target") is None, "Non-completed inference must not produce council handoff")

    handoff_refs = handoff.get("evidence_refs")
    require_string_list(handoff_refs, "Malformed handoff evidence refs")
    for ref in signal_refs + inference_refs:
        require(ref in handoff_refs, "Handoff lost required evidence reference")

    digest = hashlib.sha256(raw).hexdigest()
    artifact = "evidence/inference/" + digest + ".json"
    event = {
        key: trace[key]
        for key in ("trace_id", "workflow", "repo", "status", "timestamp")
    }
    event.update({
        "event_class": "monitor_conduction_return",
        "protocol_version": "era-avot-circulation/0.1",
        "semantic": {
            "institutional_state": "candidate_evidence",
            "execution_state": status,
            "flow_state": "awaiting_cross_repository_reconciliation",
            "authority_state": "analysis_only",
            "next_valid_action": "verify_exact_artifact_and_cross_repository_identity",
            "source_role": "bounded_monitor_conduction",
            "receiving_office": "AVOT-ARCHIVIST",
            "review_role": "Promotion Reviewer",
            "review_requirement": "human_review_required",
            "handoff_semantics": {
                "next_agent_required": False,
                "rediscovery_required": False,
                "return_basis": "era_avot_circulation_exact_byte_fixture",
                "continuity_worthy": True,
            },
        },
        "evidence": {
            "source_commission": "fixture:" + FIXTURE_ID,
            "terminal_result": {
                "fixture_id": FIXTURE_ID,
                "artifact_repository": "sovereign-codex/AVOT-ARCHIVIST",
                "artifact_path": artifact,
                "artifact_sha256": digest,
                "engine_commit": engine_sha,
                "signal_id": signal_id,
                "request_id": request_id,
                "evidence_id": evidence_id,
                "source_evidence_refs": signal_refs,
                "inference_evidence_refs": inference_refs,
                "inference_status": status,
                "handoff_disposition": expected_disposition,
                "promotion_gate": "not_assessed",
                "model_execution": "not_independently_verified",
            },
            "observations": [
                "The fixture is synthetic and deterministic.",
                "The full reviewed JSON bytes are the evidence artifact; the normalized event is an index.",
                "No ingest, TRACE dispatch, Work creation, or authority promotion is performed by this mapper.",
            ],
            "test_questions": [
                "Did Engine and Archivist derive the same evidence identity?",
                "Did exact-byte custody preserve the shared SHA-256?",
                "Did non-success inference remain non-success without a council handoff?",
            ],
        },
    })
    return event, artifact


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--engine-sha", required=True)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument(
        "--sanitized-reviewed",
        required=True,
        action="store_true",
        help="Operator reviewed the source for retention; this is not an automatic sanitizer",
    )
    args = parser.parse_args()

    raw = args.source.read_bytes()
    event, artifact = prepare(raw, args.engine_sha)

    args.output_dir.mkdir(mode=0o700, parents=False, exist_ok=False)
    destination = args.output_dir / artifact
    destination.parent.mkdir(parents=True)
    destination.write_bytes(raw)
    (args.output_dir / "event.json").write_text(json.dumps(event, indent=2) + "\n")
    print("Prepared ERA circulation candidate evidence locally. No ingestion, dispatch, or promotion performed.")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, TypeError, AttributeError, OSError):
        raise SystemExit("Preparation failed: invalid circulation contract or output path; preserve the original for review.")
