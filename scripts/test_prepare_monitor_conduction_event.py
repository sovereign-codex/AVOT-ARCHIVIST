"""Synthetic ERA circulation custody tests against the current Archivist normalization membrane."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from prepare_monitor_conduction_event import prepare


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "fixtures" / "inference" / "era-avot-circulation-001.completed.json"
ENGINE_SHA = "19ff2ceda7c4de75abd3946dcc712f7a38987c1c"
EXPECTED_DIGEST = "d1b20d1bd5571ff64902ff05dd163dd5648644497b401ce9e7028c42288b4c7e"


def fixture_data():
    return json.loads(FIXTURE.read_text())


def encode(data):
    return (json.dumps(data, indent=2) + "\n").encode()


def target(data, path):
    current = data
    parts = path.split(".")
    for part in parts[:-1]:
        current = current[part]
    return current, parts[-1]


class MonitorConductionEventTests(unittest.TestCase):
    def test_shared_fixture_maps_same_identity_and_exact_digest(self):
        raw = FIXTURE.read_bytes()
        event, artifact = prepare(raw, ENGINE_SHA)

        self.assertEqual(hashlib.sha256(raw).hexdigest(), EXPECTED_DIGEST)
        self.assertEqual(artifact, f"evidence/inference/{EXPECTED_DIGEST}.json")
        self.assertEqual(
            event["trace_id"],
            "inference:monitor-conduction:era-avot-circulation-001",
        )
        terminal = event["evidence"]["terminal_result"]
        self.assertEqual(terminal["fixture_id"], "ERA-AVOT-CIRCULATION-001")
        self.assertEqual(terminal["artifact_sha256"], EXPECTED_DIGEST)
        self.assertEqual(terminal["engine_commit"], ENGINE_SHA)
        self.assertEqual(
            terminal["signal_id"],
            "signal:era-avot-circulation-001",
        )
        self.assertEqual(
            terminal["request_id"],
            "monitor-conduction:era-avot-circulation-001",
        )
        self.assertEqual(
            terminal["evidence_id"],
            "inference:monitor-conduction:era-avot-circulation-001",
        )
        self.assertEqual(
            terminal["source_refs"],
            ["source:era-avot-circulation-raw-001"],
        )
        self.assertEqual(
            terminal["signal_evidence_refs"],
            ["evidence:era-avot-circulation-derived-001"],
        )

    def test_actual_ingest_projection_retains_index_without_allowlist_expansion(self):
        raw = FIXTURE.read_bytes()
        event, _ = prepare(raw, ENGINE_SHA)
        workflow = (ROOT / ".github/workflows/ingest.yml").read_text()
        projection = (
            "{trace_id:"
            + workflow.split("              '{trace_id:", 1)[1].split(
                "' \"$file\" > \"$OUTPUT\"", 1
            )[0]
        )
        command = ["jq"]
        for key in (
            "trace_id",
            "workflow",
            "repo",
            "status",
            "timestamp",
            "event_class",
            "protocol_version",
        ):
            command += ["--arg", key, event[key]]
        command += [
            "--arg",
            "source_file",
            "incoming/era-avot-circulation-001.json",
            projection,
        ]

        normalized = json.loads(
            subprocess.run(
                command,
                input=json.dumps(event),
                capture_output=True,
                text=True,
                check=True,
            ).stdout
        )
        normalization = normalized.pop("normalization")
        self.assertEqual(normalization["admission_posture"], "allowlisted")
        self.assertEqual(normalized, event)

    def test_rejects_broken_authority_lineage_and_evidence(self):
        changes = [
            ("result.monitor_signal.authority_posture", "bounded_execute"),
            ("result.monitor_signal.institutional_effect", "work_created"),
            ("result.inference.request.work_ref", "work:unauthorized"),
            ("result.inference.request.privacy_boundary", "cloud_allowed"),
            ("result.inference.request.authority_posture", "bounded_execute"),
            (
                "result.inference.request.context_refs",
                [
                    "signal:era-avot-circulation-001",
                    "evidence:era-avot-circulation-derived-001",
                ],
            ),
            (
                "result.handoff.evidence_refs",
                [
                    "evidence:era-avot-circulation-derived-001",
                    "evidence:era-completed-001",
                ],
            ),
            (
                "result.inference.return_path.archivist.evidence_id",
                "inference:wrong",
            ),
            (
                "result.inference.return_path.archivist.result.authority_effect",
                "bounded_execution_return",
            ),
            (
                "result.inference.return_path.archivist.result.evidence_refs",
                [],
            ),
            ("result.inference.return_path.trace.status", "failed"),
            (
                "result.inference.return_path.archivist.plan.fallback_plan",
                ["fallback-capability"],
            ),
            ("result.monitor_evidence_return.dormancy_entered", False),
            ("result.handoff.institutional_effect", "accepted"),
            ("result.handoff.target", None),
        ]

        for path, value in changes:
            with self.subTest(path=path):
                data = fixture_data()
                parent, key = target(data, path)
                parent[key] = value
                with self.assertRaises(ValueError):
                    prepare(encode(data), ENGINE_SHA)

    def test_noncompleted_states_remain_noncompleted_and_have_no_council_handoff(self):
        dispositions = {
            "refused": "inference_refused",
            "degraded": "inference_degraded",
            "failed": "inference_failed",
        }

        for status, disposition in dispositions.items():
            with self.subTest(status=status):
                data = fixture_data()
                result = data["result"]["inference"]["return_path"]["archivist"]["result"]
                result["status"] = status
                if status in ("refused", "failed"):
                    result.pop("output", None)
                data["result"]["inference"]["return_path"]["trace"]["status"] = status
                data["result"]["handoff"]["target"] = None
                data["result"]["handoff"]["disposition"] = disposition

                event, _ = prepare(encode(data), ENGINE_SHA)
                self.assertEqual(event["status"], status)
                terminal = event["evidence"]["terminal_result"]
                self.assertEqual(terminal["inference_status"], status)
                self.assertEqual(terminal["handoff_disposition"], disposition)
                self.assertEqual(terminal["promotion_gate"], "not_assessed")

    def test_cli_retains_exact_bytes_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source.json"
            output = root / "staged"
            raw = FIXTURE.read_bytes()
            source.write_bytes(raw)

            command = [
                "python3",
                str(ROOT / "scripts/prepare_monitor_conduction_event.py"),
                str(source),
                "--engine-sha",
                ENGINE_SHA,
                "--output-dir",
                str(output),
                "--sanitized-reviewed",
            ]
            subprocess.run(command, check=True, capture_output=True)
            event = json.loads((output / "event.json").read_text())
            artifact = output / event["evidence"]["terminal_result"]["artifact_path"]

            self.assertEqual(artifact.read_bytes(), raw)
            self.assertEqual(hashlib.sha256(artifact.read_bytes()).hexdigest(), EXPECTED_DIGEST)
            self.assertNotEqual(
                subprocess.run(command, capture_output=True).returncode,
                0,
            )
            self.assertEqual(artifact.read_bytes(), raw)


if __name__ == "__main__":
    unittest.main()
