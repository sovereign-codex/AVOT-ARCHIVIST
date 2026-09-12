"""Synthetic contract tests, including the actual ingest.yml jq projection."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from prepare_inference_event import prepare

ROOT = Path(__file__).resolve().parents[1]
SHA = 'e8974ec1e031852a1e4f7475bc9ded37d8f95c99'


def fixture():
    request = dict(request_id='real-local-1', work_ref='work:real-local-model-probe-v0.1', intent='synthetic test only', input='synthetic public input', privacy_boundary='local_only', authority_posture='analysis_only', evidence_required=True)
    plan = dict(request_id='real-local-1', target_capability='real-local-chat', target_runtime='synthetic-runtime', target_model='synthetic-model', target_node='synthetic-node', strategy='direct', privacy_boundary='local_only', authority_posture='analysis_only', fallback_plan=[])
    result = dict(request_id='real-local-1', status='completed', output='SYNTHETIC: no model executed', capability_used='real-local-chat', runtime_used='synthetic-runtime', model_used='synthetic-model', node_refs=['synthetic-node'], authority_effect='analysis_return', evidence_refs=['completion:synthetic-id-not-runtime-evidence'], provenance_refs=['runtime:synthetic-runtime', 'endpoint:http://127.0.0.1:8000/v1/chat/completions'], verification={'required': False, 'status': 'not_required'})
    archive = dict(request_id='real-local-1', evidence_id='inference:real-local-1', request={k:request[k] for k in ('intent', 'work_ref', 'privacy_boundary', 'authority_posture')}, plan=plan, result=result, captured_at='2026-09-12T00:00:00Z')
    trace = dict(trace_id='inference:real-local-1', repo='sovereign-codex/AVOT-engine', workflow='sovereign-inference/direct/synthetic-runtime', status='completed', timestamp=archive['captured_at'])
    return dict(request=request, return_path=dict(archivist=archive, trace=trace))


def encode(data):
    return (json.dumps(data, indent=2) + '\n').encode()


class InferenceEventTests(unittest.TestCase):
    def test_actual_ingest_projection_retains_identity_and_artifact(self):
        raw = encode(fixture())
        event, artifact = prepare(raw, SHA)
        workflow = (ROOT / '.github/workflows/ingest.yml').read_text()
        projection = '{trace_id:' + workflow.split("              '{trace_id:", 1)[1].split("' \"$file\" > \"$OUTPUT\"", 1)[0]
        command = ['jq']
        for key in ('trace_id', 'workflow', 'repo', 'status', 'timestamp', 'event_class', 'protocol_version'):
            command += ['--arg', key, event[key]]
        command += ['--arg', 'source_file', 'incoming/probe.json', projection]
        normalized = json.loads(subprocess.run(command, input=json.dumps(event), capture_output=True, text=True, check=True).stdout)
        normalization = normalized.pop('normalization')
        self.assertEqual(normalization['admission_posture'], 'allowlisted')
        self.assertEqual(normalized, event)
        self.assertEqual(event['evidence']['terminal_result']['artifact_sha256'], hashlib.sha256(raw).hexdigest())
        self.assertIn(hashlib.sha256(raw).hexdigest(), artifact)
        self.assertEqual(event['evidence']['terminal_result']['model_execution'], 'not_independently_verified')

    def test_rejects_broken_boundaries_and_lineage(self):
        changes = [
            ('request', 'privacy_boundary', 'cloud_allowed'),
            ('request', 'authority_posture', 'bounded_execute'),
            ('request', 'evidence_required', False),
            ('trace', 'trace_id', '../../unsafe'),
            ('trace', 'status', 'failed'),
            ('trace', 'timestamp', '2026-09-13T00:00:00Z'),
            ('archive', 'request_id', 'real-local-2'),
            ('result', 'evidence_refs', []),
            ('result', 'model_used', 'other-model'),
            ('result', 'node_refs', ['other-node']),
            ('result', 'fallback_used', True),
            ('result', 'authority_effect', 'bounded_execution_return'),
            ('result', 'provenance_refs', ['endpoint:https://remote.example/v1/chat/completions']),
            ('result', 'provenance_refs', ['endpoint:http://token@127.0.0.1:8000/v1/chat/completions']),
            ('result', 'provenance_refs', ['endpoint:http://127.0.0.1:8000/v1/chat/completions?token=secret']),
        ]
        for section, key, value in changes:
            with self.subTest(section=section, key=key):
                data = fixture()
                archive = data['return_path']['archivist']
                target = dict(request=data['request'], trace=data['return_path']['trace'], archive=archive, result=archive['result'])[section]
                target[key] = value
                with self.assertRaises(ValueError):
                    prepare(encode(data), SHA)

    def test_failed_return_is_not_upgraded(self):
        data = fixture()
        result = data['return_path']['archivist']['result']
        result.update(status='failed', evidence_refs=[], provenance_refs=[], authority_effect='none')
        result.pop('output')
        data['return_path']['trace']['status'] = 'failed'
        event, _ = prepare(encode(data), SHA)
        self.assertEqual(event['status'], 'failed')
        self.assertEqual(event['evidence']['terminal_result']['promotion_gate'], 'not_assessed')

    def test_cli_retains_exact_bytes_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source, output = root / 'source.json', root / 'staged'
            raw = encode(fixture())
            source.write_bytes(raw)
            command = ['python3', str(ROOT / 'scripts/prepare_inference_event.py'), str(source), '--engine-sha', SHA, '--output-dir', str(output), '--sanitized-reviewed']
            subprocess.run(command, check=True, capture_output=True)
            event = json.loads((output / 'event.json').read_text())
            artifact = output / event['evidence']['terminal_result']['artifact_path']
            self.assertEqual(artifact.read_bytes(), raw)
            self.assertNotEqual(subprocess.run(command, capture_output=True).returncode, 0)
            self.assertEqual(artifact.read_bytes(), raw)


if __name__ == '__main__':
    unittest.main()
